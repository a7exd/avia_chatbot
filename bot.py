# -*- coding: utf-8 -*-
import logging
import random

import requests
from pony.orm import db_session

import handlers
from models import UserState, OrderTicket

try:
    import settings
    import conn_settings
except ImportError:
    exit('Do cp settings.py.default settings.py '
         'Do cp conn_settings.py.default conn_settings.py '
         'then set TOKEN and GROUP_ID of yours in conn_settings.py')
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

log = logging.getLogger('bot')


def configure_logging():
    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter('%(levelname)s %(message)s')
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler('bot.log', encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
                                         datefmt='%d-%m-%Y %H:%M')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)
    log.setLevel(logging.DEBUG)


class Bot:
    """
    Echo bot для vk.com.

    Use python 3.10.1
    """
    def __init__(self, group_id, token):
        """
        :param group_id: group id из группы vk
        :param token: секретный токен для подключения к группе
        """
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        """Запуск бота."""
        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception:
                log.exception('Ошибка обработки события')

    @db_session
    def on_event(self, event):
        """
        Отправляет сообщение назад, если это текст.

        :param event: VkBotMessageEvent object
        :return: None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info(f'Пока я не умею работать с типом сообщений: {event.type}')
            return

        user_id = event.message.peer_id
        text = event.message.text

        state = UserState.get(user_id=str(user_id))

        if (state is None) or (text in ('/ticket', '/help')):
            self.search_intent(text, user_id, state)
        else:
            self.continue_scenario(text, state, user_id)

    def send_text(self, text_to_send, user_id):
        self.api.messages.send(message=text_to_send,
                               random_id=random.randint(0, 2 ** 20),
                               peer_id=user_id, )

    def send_image(self, image, user_id):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(
            url=upload_url,
            files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)

        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment = f'photo{owner_id}_{media_id}'
        self.api.messages.send(attachment=attachment,
                               random_id=random.randint(0, 2 ** 20),
                               peer_id=user_id, )

    def send_step(self, step, user_id, text, context):
        if 'text' in step:
            self.send_text(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            ticket = handler(text, context)
            self.send_image(ticket, user_id)

    def search_intent(self, text, user_id, state):
        for intent in settings.INTENTS:
            log.debug(f'User gets {intent}')
            if any(token in text.lower() for token in intent['tokens']):
                # run intent
                if intent['answer']:
                    self.send_text(intent['answer'], user_id)
                else:
                    self.start_scenario(intent['scenario'], user_id, state, text)
                break
        else:
            self.send_text(settings.DEFAULT_ANSWER, user_id)

    def start_scenario(self, scenario_name, user_id, state, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_step(step, user_id, text, context={})
        if (state is not None) and (state.user_id == str(user_id)):
            state.delete()
        UserState(user_id=str(user_id), scenario_name=scenario_name,
                  step_name=first_step, context={})

    def continue_scenario(self, text, state, user_id):
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            # next step
            next_step = steps[step['next_step']]

            if step['next_step'] == 'step4':
                self.get_flights(state.context)
            if step['next_step'] == 'step7':
                state.context['verbose_flight'] = \
                    self.verbose_flight(state.context['flight'])

            self.send_step(next_step, user_id, text, state.context)
            if next_step['next_step']:
                # switch to next_step
                state.step_name = step['next_step']
            else:
                # finish scenario
                log.info('Принят заказ на рейс:\n{verbose_flight}'
                         'ФИО: {name}\nкол-во мест: {count_seats}\n'
                         'комментарий: {comment}'.
                         format(**state.context))
                OrderTicket(name=state.context['name'],
                            date=state.context['flight']['date'],
                            from_=state.context['flight']['from'],
                            to=state.context['flight']['to'],
                            flight_num=state.context['flight']['number'],
                            count_seats=state.context['count_seats'],
                            seats=state.context['seats'],
                            comment=state.context['comment'])
                state.delete()
        else:
            self.send_text(step['failure_text'].format(**state.context), user_id)
            if state.step_name == 'step2' or state.step_name == 'step7':
                state.delete()

    def get_flights(self, context, verbose=True):
        verbose_flights = ''
        context['from_to_flights'] =\
            settings.dispatcher(context)
        if verbose:
            for flight in context['from_to_flights']:
                verbose_flights += self.verbose_flight(flight)
            context['verbose_flights'] = verbose_flights

    def verbose_flight(self, flight):
        return f"Дата: {flight['date'][:16]}\n" \
                f"Откуда: {flight['from']}\n" \
                f"Куда: {flight['to']}\n" \
                f"Номер рейса: {flight['number']}\n"


if __name__ == '__main__':
    configure_logging()
    bot = Bot(conn_settings.GROUP_ID, conn_settings.TOKEN)
    bot.run()

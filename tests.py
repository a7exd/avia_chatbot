# -*- coding: utf-8 -*-
from copy import deepcopy
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch, Mock

from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent
from bot import Bot
import settings
from generate_ticket import make_ticket


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()

    return wrapper


class Test1(TestCase):
    RAW_EVENT = {
        'type': 'message_new',
        'object': {'message':
                       {'date': 1643049709, 'from_id': 699917363, 'id': 73,
                        'out': 0, 'attachments': [],
                        'conversation_message_id': 70, 'fwd_messages': [],
                        'important': False, 'is_hidden': False,
                        'peer_id': 699917363, 'random_id': 0,
                        'text': 'Привет бот'},
                   'client_info':
                       {'button_actions': ['text', 'vkpay', 'open_app',
                                           'location', 'open_link', 'callback',
                                           'intent_subscribe',
                                           'intent_unsubscribe'],
                        'keyboard': True, 'inline_keyboard': True,
                        'carousel': True, 'lang_id': 0
                        }
                   },
        'group_id': 210253602,
        'event_id': '29b37f24fa377c98130f2d26075d4e186c94bf4b'}

    def test_run(self):
        count = 5
        obj = {'a': 1}
        events = [obj] * count  # [obj, obj, ...]
        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)
        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll',
                       return_value=long_poller_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.send_image = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count

    INPUTS = [
        'Привет',
        'Помощь',
        'бИлет',
        'Иванов Петр Петрович',
        'Караганда',
        'Стамбул',
        'Москва',
        '01-05-2019',
        '01-05-2025',
        '44_32',
        '12134',
        '3',
        'kghvhg',
        'kmm',
        '+7(9999)555-77X-X77X',
        '+7(999)555-77-77']
    FLIGHT = 'Дата: 2025-05-01 17:06\nОткуда: Стамбул\n' \
             'Куда: Москва\nНомер рейса: 12134\n'
    FLIGHTS = \
        'Дата: 2025-05-01 17:06\nОткуда: Стамбул\nКуда: Москва\n' \
        'Номер рейса: 12134\n' \
        'Дата: 2025-05-02 17:06\nОткуда: Стамбул\nКуда: Москва\n' \
        'Номер рейса: 12234\n' \
        'Дата: 2025-05-03 17:06\nОткуда: Стамбул\nКуда: Москва\n' \
        'Номер рейса: 12334\n' \
        'Дата: 2025-05-04 17:06\nОткуда: Стамбул\nКуда: Москва\n' \
        'Номер рейса: 12434\n' \
        'Дата: 2025-05-05 17:06\nОткуда: Стамбул\nКуда: Москва\n' \
        'Номер рейса: 12534\n'
    EXPECTED_OUTPUTS = [
        settings.DEFAULT_ANSWER,
        settings.INTENTS[0]['answer'],
        settings.SCENARIOS['order_ticket']['steps']['step0']['text'],
        settings.SCENARIOS['order_ticket']['steps']['step1']['text'],
        settings.SCENARIOS['order_ticket']['steps']['step1'][
            'failure_text'].format(CITIES=settings.CITIES),
        settings.SCENARIOS['order_ticket']['steps']['step2']['text'],
        settings.SCENARIOS['order_ticket']['steps']['step3']['text'],
        settings.SCENARIOS['order_ticket']['steps']['step3'][
            'failure_text'],
        settings.SCENARIOS['order_ticket']['steps']['step4'][
            'text'].format(verbose_flights=FLIGHTS),
        settings.SCENARIOS['order_ticket']['steps']['step4'][
            'failure_text'].format(verbose_flights=FLIGHTS),
        settings.SCENARIOS['order_ticket']['steps']['step5']['text'],
        settings.SCENARIOS['order_ticket']['steps']['step6']['text'],
        settings.SCENARIOS['order_ticket']['steps']['step7']['text'
        ].format(name=INPUTS[3], verbose_flight=FLIGHT,
                 count_seats='3', comment='kghvhg'),
        settings.SCENARIOS['order_ticket']['steps']['step8']['text'],
        settings.SCENARIOS['order_ticket']['steps']['step8'][
            'failure_text'],
        settings.SCENARIOS['order_ticket']['steps']['step9']['text']
    ]

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll',
                   return_value=long_poller_mock):
            bot = Bot('', '')
            bot.api = api_mock
            bot.api.messages.send = send_mock
            bot.send_image = Mock()
            bot.run()

        assert send_mock.call_count == len(self.INPUTS)

        real_OUTPUTS = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_OUTPUTS.append(kwargs['message'])

        assert real_OUTPUTS == self.EXPECTED_OUTPUTS

    def test_image_generation(self):
        ticket_file = make_ticket(self.INPUTS[3], 'Стамбул', 'Москва',
                                  datetime.strptime('2025-05-01 17:06',
                                                    '%Y-%m-%d %H:%M'),
                                  '12134', ['01A', '01B', '01C'])
        with open('./files/ticket_example.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()

        assert ticket_file.read() == expected_bytes

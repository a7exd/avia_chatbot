# -*- coding: utf-8 -*-
import datetime
import os

DEFAULT_ANSWER = 'Не знаю что Вам на это и ответить. Могу помочь заказать ' \
                 'авиабилет.'

CITIES = ['Москва', 'Париж', 'Лондон', 'Санкт-Петербург', 'Мадрид', 'Мюнхен',
          'Стамбул', 'Вашингтон', 'Хьюстон', 'Казань', 'Марсель', 'Пекин',
          'Токио', 'Бразилиа', 'Лос-Анджелес', 'Алматы', 'Гонконг', 'Ханой',
          'Анталья', 'Киев', 'Минск', 'Гуанчжоу', 'Барселона', 'Тбилиси', 'Рим',
          'Прага', 'Берлин']

NO_FLIGHTS = [['Киев', 'Москва'], ['Берлин', 'Минск']]

TEMPLATE_PATH = os.path.join('./files', 'ticket_template.png')
FONT_PATH = os.path.join('./files', 'Roboto-Regular.ttf')
TIME_BTWN_DEPART_BOARDING = datetime.timedelta(minutes=30)
FONT_SIZE = 20
BLACK = (0, 0, 0, 255)
OFFSET = {'fio': (40, 120), 'from_': (40, 190), 'to': (40, 255),
          'depart_date': (260, 255), 'depart_time': (410, 255),
          'flight_number': (50, 320), 'seats': (150, 320), 'row': (300, 320),
          'boarding_time': (410, 320)}

SEAT_LETTERS = ['A', 'B', 'C', 'D', 'E']

DB_CONFIG = dict(
    provider='postgres',
    user='postgres',
    host='localhost',
    database='aviachatbot')

INTENTS = [
    {
        'name': 'info',
        'tokens': ('help', '/help', 'info', 'помощь', 'помоги', 'что ты умеешь',
                   'инфо', 'как'),
        'scenario': None,
        'answer': 'Приветствую Вас! Меня зовут Ticky, я создан помочь Вам '
                  'купить авиабилет. Доступные команды: '
                  'оформление билета - /ticket, '
                  'помощь (вывод этого сообщения) - /help.'
    },
    {
        'name': 'Заказ авиабилетов',
        'tokens': ('ticket', '/ticket', 'купить', 'заказать', 'билет'),
        'scenario': 'order_ticket',
        'answer': None
    }]

SCENARIOS = {
    'order_ticket': {
        'first_step': 'step0',
        'steps': {
            'step0': {
                'text': 'Введите вашу фамилию, имя и отчество(если есть): ',
                'failure_text': f'Не правильно указаны данные! Фамилия, имя и '
                                f'отчество должны быть указаны кирилицей через '
                                f'пробел. Если отчества нет, '
                                f'указывать ничего не надо.',
                'handler': 'handle_name',
                'next_step': 'step1'
            },
            'step1': {
                'text': 'Введите город отправления',
                'failure_text': f'К сожалению, в расписании рейсов указанного '
                                f'города нет. Список городов, для которых '
                                f'совершаются рейсы:\n'
                                f'{CITIES}\n '
                                f'Введите город '
                                f'из списка. ',
                'handler': 'handle_from_',
                'next_step': 'step2'
            },
            'step2': {
                'text': 'Введите город назначения',
                'failure_text': 'К сожалению, в расписании рейсов указанного '
                                'города нет. Город прилета не должен совпадать '
                                'с городом вылета. Повторите попытку сначала.',
                'handler': 'handle_to',
                'next_step': 'step3'
            },
            'step3': {
                'text': 'Введите дату вылета в формате 01-05-2019.',
                'failure_text': 'Дата вылета должна быть указана в формате '
                                '01-05-2019. На прошедшее число купить билет '
                                'нельзя. Попробуйте еще раз.',
                'handler': 'handle_date',
                'next_step': 'step4'
            },
            'step4': {
                'text': "Введите номер понравившегося рейса:\n\n"
                        "{verbose_flights}",
                'failure_text': "Неправильный номер рейса. Попробуйте еще раз.\n"
                                "Список рейсов:\n\n "
                                "{verbose_flights}",
                'handler': 'handle_flights',
                'next_step': 'step5'
            },
            'step5': {
                'text': 'Уточните необходимое количество мест (от 1 до 5).',
                'failure_text': 'Не выбрано количество мест или оно не попадает'
                                'в диапазон (от одного до пяти). '
                                'Попробуйте еще раз.',
                'handler': 'handle_seat',
                'next_step': 'step6'
            },
            'step6': {
                'text': 'Если у Вас есть пожелания к заказу, укажите их '
                        'в произвольной форме (до 250 символов).',
                'failure_text': 'Длина комментария больше 250 символов.'
                                'Попробуйте еще раз.',
                'handler': 'handle_comment',
                'next_step': 'step7'
            },
            'step7': {
                'text': "Введенные данные указаны верно?\n"
                        "ФИО: {name}\n"
                        "{verbose_flight}"
                        "Кол-во мест: {count_seats}\n"
                        "Комментарий: {comment}\n\n"
                        "да/нет?",
                'failure_text': 'Ошибка оформления, попробуем ещё раз?\n'
                                'попробовать - /ticket,\n'
                                'помощь - /help\n',
                'handler': 'handle_correct_data',
                'next_step': 'step8'
            },
            'step8': {
                'text': 'Укажите номер телефона для связи в формате '
                        '+7(XXX)XXX-XX-XX.',
                'failure_text': 'Неправильный номер телефона. Номер телефона '
                                'должен начинаться с 8, состоять из 11 цифр '
                                'и соответствовать шаблону +7(XXX)XXX-XX-XX.'
                                'Попробуйте еще раз.',
                'handler': 'handle_phone',
                'next_step': 'step9'
            },
            'step9': {
                'text': 'Спасибо за ваш заказ! Билет отправлен вам во вложении, '
                        'можно распечатать его и пройти регистрацию с ним.',
                'image': 'generate_ticket',
                'failure_text': None,
                'handler': None,
                'next_step': None
            }
        }
    }
}


class Timeline:
    """
        Класс Timeline предоставляет удобный интерфейс генерации расписания
        авиарейсов и доступа к ним на 2 следующих месяца от указанной даты.

        :param date: дата вылета
        :param cities: список городов вылета/прилета
        :return: возвращает все рейсы в виде списка словарей
            [    {'number': 'exmp10',
                'from': 'Москва',
                'to': 'Париж',
                'date': '01-02-2019',
                }, {...}
            ]
    """

    def __init__(self, date, cities=CITIES, no_flights=NO_FLIGHTS):
        self.date = datetime.datetime.strptime(date, '%d-%m-%Y')
        self.cities = cities
        self.no_flights = no_flights
        self.flights = []

    def generate(self, add_reg_flights=True):
        for from_ in self.cities:
            for to in self.cities:
                if to == from_:
                    continue
                for no_flight in self.no_flights:
                    if [from_, to] == no_flight or [to, from_] == no_flight:
                        break
                else:
                    self._add_flights(from_, to)
                continue
        if add_reg_flights:
            self._add_flights('Москва', 'Берлин', period='weekdays')
            self._add_flights('Тбилиси', 'Рим', period='monthdays')
        self.flights.sort(key=lambda x: x['date'])

    def _add_flights(self, from_, to, period=None):
        for day in range(60):
            hours = abs(23 - self.cities.index(from_))
            minutes = self.cities.index(from_) + self.cities.index(to)
            dt = self.date + datetime.timedelta(days=day)
            if (period == 'weekdays') and ((dt.weekday() == 0) or (dt.weekday() == 5)):
                dt = dt + datetime.timedelta(hours=7)
            elif (period == 'monthdays') and ((dt.day == 10) or (dt.day == 20)):
                dt = dt + datetime.timedelta(hours=15)
            elif period is None:
                dt = dt + datetime.timedelta(hours=hours, minutes=minutes)
            else:
                continue
            self.flights.append(
                {'date': f'{dt}',
                 'from': from_,
                 'to': to,
                 'number': f'{minutes*2}{dt.day}{hours*2}'})


def dispatcher(context, num_flights_show=5):
    """
    Диспетчер — функция, которая отдает список ближайших к заданной дате рейсов
     из города отправления в город назначения.
    :param context: контекст
    :param num_flights_show: кол-во рейсов в возвращаемом списке
    :return: list( {flight}, {flight}, {...})
    """
    from_to_flights = []
    timeline = Timeline(context['date'])
    timeline.generate()
    for flight in timeline.flights:
        if (context['from_city'], context['to_city']) == (flight['from'],
                                                          flight['to']):
            from_to_flights.append(flight)
            if len(from_to_flights) == num_flights_show:
                break
    if not from_to_flights:
        raise ValueError('Список рейсов для заданных параметров пуст. '
                         'Попробуйте поменять параметры.')
    return from_to_flights

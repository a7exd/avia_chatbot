# -*- coding: utf-8 -*-
import re
import datetime

from settings import CITIES, SEAT_LETTERS
from generate_ticket import make_ticket

re_name = re.compile(r'[а-яА-ЯёЁ\-]{3,10}')
re_phone_num = re.compile(r'(?:8|\+7)\(\d{3}\)\d{3}-\d{2}-\d{2}')
re_city = re.compile(r'^[а-яА-Я-\s]{3,20}$')


def handle_name(text, context):
    if 2 <= len(re.findall(re_name, text)) <= 3:
        context['name'] = text
        return True
    else:
        return False


def handle_from_(text, context):
    text = text.capitalize()
    match = re.match(re_city, text)
    if match:
        if text in CITIES:
            context['from_city'] = text
            return True
        else:
            return False


def handle_to(text, context):
    text = text.capitalize()
    match = re.match(re_city, text)
    if match:
        if text in CITIES:
            if text != context['from_city']:
                context['to_city'] = text
                return True
            else:
                return False
    else:
        return False


def handle_date(text, context):
    today_date_resolution = datetime.timedelta(days=-1)
    try:
        user_dt = datetime.datetime.strptime(text, '%d-%m-%Y')
        now = datetime.datetime.now()
        result = user_dt - now
        if result < today_date_resolution:
            return False
        context['date'] = text
        return True
    except Exception:
        return False


def handle_flights(text, context):
    for flight in context['from_to_flights']:
        if text == flight['number']:
            context['flight'] = flight
            return True
    else:
        return False


def handle_seat(text, context):
    row = context['date'].split('-')[0]
    if text.isdigit() and (1 <= int(text) <= 5):
        context['count_seats'] = text
        context['seats'] = [f'{row:02}{SEAT_LETTERS[_]}'
                            for _ in range(int(text))]
        return True
    else:
        return False


def handle_comment(text, context):
    if len(text) <= 250:
        context['comment'] = text
        return True
    else:
        return False


def handle_correct_data(text, context):
    if text == 'нет':
        return False
    else:
        return True


def handle_phone(text, context):
    match = re.match(re_phone_num, text)
    if match:
        context['phone'] = text
        return True
    else:
        return False


def generate_ticket(text, context):
    dt = datetime.datetime.strptime(context['flight']['date'],
                                    '%Y-%m-%d %H:%M:%S')
    return make_ticket(context['name'], context['from_city'],
                       context['to_city'], dt,
                       context['flight']['number'], context['seats'])

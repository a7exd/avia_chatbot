# -*- coding: utf-8 -*-
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from settings import TEMPLATE_PATH, FONT_PATH, \
    TIME_BTWN_DEPART_BOARDING, BLACK, FONT_SIZE, OFFSET


def make_ticket(fio, from_, to, date, flight_number, seats):
    font = ImageFont.truetype(FONT_PATH, size=FONT_SIZE)
    depart_date = datetime.strftime(date, '%d-%m-%Y')
    row = seats[0][:2]
    seats = [s[-1] for s in seats]
    seats = f"{', '.join(seats):>13s}"
    depart_time = datetime.strftime(date, '%H:%M')
    boarding_time = datetime.strftime(date - TIME_BTWN_DEPART_BOARDING,
                                      '%H:%M')
    ticket_data = {'fio': fio, 'from_': from_, 'to': to,
                   'depart_date': depart_date, 'depart_time': depart_time,
                   'flight_number': flight_number, 'seats': seats, 'row': row,
                   'boarding_time': boarding_time}
    with Image.open(TEMPLATE_PATH) as im:
        draw = ImageDraw.Draw(im)
        for key, val in ticket_data.items():
            draw.text(OFFSET[f'{key}'], val, font=font, fill=BLACK)
        temp_file = BytesIO()
        im.save(temp_file, 'png')
        temp_file.seek(0)
        return temp_file

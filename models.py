# -*- coding: utf-8 -*-
from datetime import datetime

from pony.orm import Database, Required, Json, StrArray

from settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    """Состояние пользователя внутри сценария"""
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class OrderTicket(db.Entity):
    """Заказ билета."""
    name = Required(str)
    date = Required(datetime)
    from_ = Required(str)
    to = Required(str)
    flight_num = Required(str)
    count_seats = Required(int)
    seats = Required(StrArray)
    comment = Required(str)


db.generate_mapping(create_tables=True)

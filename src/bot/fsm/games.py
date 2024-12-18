from aiogram.fsm.state import State, StatesGroup


class Games(StatesGroup):
    level = State()
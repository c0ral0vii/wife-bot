from aiogram.fsm.state import State, StatesGroup


class ChangeProfile(StatesGroup):
    username = State()
    new_photo = State()
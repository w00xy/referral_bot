from aiogram.fsm.state import StatesGroup, State


class UserStates(StatesGroup):
    help = State()

class Withdraw(StatesGroup):
    select_currency = State()
    enter_amount = State()
    enter_address = State()
    confirm = State()
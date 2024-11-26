from aiogram.fsm.state import StatesGroup, State


class Admin(StatesGroup):
    add_channel = State()
    change_link = State()
    confirm_channel = State()

    add_admin = State()
    grant_admin = State()

    edit_spam = State()
    start_spam = State()

    search_bids = State()

    search_stats = State()

    give_balance = State()

    help_answer = State()
    wait_answer_help_text = State()

    wait_check = State()

    update_link = State()
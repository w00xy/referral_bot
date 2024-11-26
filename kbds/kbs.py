from urllib.parse import quote

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, \
    KeyboardButtonRequestChat
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy import bitwise_not

from database.models import User, HelpMessage, UserHistory
from database.orm_query import orm_get_channels
from .inline import get_callback_btns, get_inlineMix_btns
from utils.extra import linkify


async def get_start_buttons(user_id):
    ref_link = await linkify(user_id)
    invite_text = f"📍 Вам отправлено 4 USDT\n{ref_link}"
    encoded_text = quote(invite_text)
    return get_inlineMix_btns(
        btns={
            "🔄 Обновить баланс": "refresh",
            "💸 Вывод средств": "want_withdraw",
            "🎁 Отправить подарок": f"https://t.me/share/url?url={encoded_text}",
            "📑 История вывода средств": "get_history",
            "💈 Топ траферов": "get_traffic"
        },
        sizes=(2,1,2)
    )

async def get_channels_btns():
    channels = await orm_get_channels()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[], row_width=1)

    for channel_data in channels:
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(
                text=channel_data['channel_name'],
                url=channel_data['channel_link'],
            )]
        )
    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscribe")]
    )
    return keyboard


choose_method_btns = get_callback_btns(
    btns={
        "USDT BEP20": "currency_usdt_bep20",
        "USDT TRC20": "currency_usdt_trc20",
        "TON": "currency_ton",
        "ETH": "currency_eth",
        "TRON": "currency_tron",
        "BTC": "currency_btc",
        "🔙 В главное меню": "refresh",
    },sizes=(1,1,1,1,1,1,1)
)

back_to_choose_currency = get_callback_btns(
    btns={
        "🔙Назад": "want_withdraw"
    }
)

decline_bid = get_callback_btns(
    btns={
        "✅ Создать заявку": "send_bid",
        "❌ Отменить заявку": "refresh"
    }
)

home_button = get_callback_btns(
    btns={
        "🏠 В главное меню": "refresh"
    }
)

async def get_bid_btns(call, bid: UserHistory, last_bid, i):
    if bid.status == "✅ Успешно":
        return
    if i + 1 == last_bid:
        return get_callback_btns(
            btns={
                "❌ Отменить заявку": f"close_bid_{bid.id}",
                "🆘 Написать в поддержку": f"user_help_bid_{bid.id}",
                "🏠 В главное меню": "refresh"
            }, sizes=(1, 1, 1)
        )
    return get_callback_btns(
        btns={
            "❌ Отменить заявку": f"close_bid_{bid.id}",
        }
    )

async def get_admin_panel():
    # keyboard.add(InlineKeyboardButton(text="Добавить админа", callback_data="add_admin"))
    return get_callback_btns(
        btns={
            "➕ Добавить/удалить канал": "handle_channels",
            "👥 Статистика человека": "view_stats",
            "📲 Рассылка": "spam",
            "⏳ Ожидают вывод": "view_bids",
            "💸 Закрытые выводы": "closed_bids",
            "🛠 Тех-поддержка": "help_menu",
        }, sizes=(1, 2, 2, 1 )
    )

async def create_del_channel():
    keyboard = ReplyKeyboardBuilder()

    keyboard.add(KeyboardButton(text="Выбрать канал", request_chat=KeyboardButtonRequestChat(
        chat_is_channel=True,
        request_id=1,
        request_username=True,
        request_title=True,
    )))
    keyboard.add(KeyboardButton(text="Просмотреть каналы"))

    return keyboard.as_markup(
        resize_keyboard=True
    )


async def handle_channel_btns(chat_link):
    if chat_link == "ЗАКРЫТЫЙ КАНАЛ":
        return get_callback_btns(
            btns={
                "Изменить ссылку": "channel_change_link",
                "Админ панель": "admin_panel"
            }
        )
    return get_callback_btns(
        btns={
            "Изменить ссылку": "channel_change_link",
            "Добавить канал": "add_channel",
            "Админ панель": "admin_panel"
        }
    )

async def delete_channel_button(chat_id):
    return get_callback_btns(
        btns={
            "Удалить канал": f"delete_channel_{chat_id}",
        }
    )

async def get_grant_admin(user_id):
    return get_callback_btns(
        btns={
            "Сделать админом": f"grant_admin_{user_id}",
        }
    )

async def get_back_to_admin():
    return get_callback_btns(
        btns={
            "Вернуться": f"admin_panel",
        }
    )

async def only_admin_panel():
    return get_callback_btns(
        btns={
            "🏠 Вернуться": f"admin_panel",
        }
    )

async def get_start_spam_btns():
    return get_callback_btns(
        btns={
            "Подвердить": "confirm_spam",
            "Вернуться": f"admin_panel",
        }
    )

async def bids_buttons(slide, total_bids):
    if not total_bids:
        return get_callback_btns(
            btns={
                "🏠 Вернуться": f"admin_panel",
            },
            sizes=(2,)
        )
    if slide * 3 >= total_bids:
        return get_callback_btns(
            btns={
                "◀️ Пред": f"view_bids_{slide - 1}",
                "🏠 Вернуться": f"admin_panel",
            }, sizes=(3,)
        )
    if not slide:
        if total_bids <= 3:
            return get_callback_btns(
                btns={
                    "🏠 Вернуться": f"admin_panel",
                },
                sizes=(2,)
            )
        return get_callback_btns(
            btns={
                "🏠 Вернуться": f"admin_panel",
                "След ➡️": f"view_bids_{slide + 1}"
            },
            sizes=(2, )
        )
    return get_callback_btns(
        btns={
            "◀️ Пред": f"view_bids_{slide - 1}",
            "🏠 Вернуться": f"admin_panel",
            "След ➡️": f"view_bids_{slide + 1}"
        }, sizes=(3, )
    )


async def closed_bids_btns(slide, total_bids):
    if not total_bids:
        return get_callback_btns(
            btns={
                "🏠 Вернуться": f"admin_panel",
            },
            sizes=(2,)
        )
    if slide * 3 >= total_bids:
        return get_callback_btns(
            btns={
                "◀️ Пред": f"closed_bids_{slide - 1}",
                "🏠 Вернуться": f"admin_panel",
            }, sizes=(3,)
        )
    if not slide:
        if total_bids <= 3:
            return get_callback_btns(
                btns={
                    "🏠 Вернуться": f"admin_panel",
                },
                sizes=(2,)
            )
        return get_callback_btns(
            btns={
                "🏠 Вернуться": f"admin_panel",
                "След ➡️": f"closed_bids_{slide + 1}"
            },
            sizes=(2, )
        )
    return get_callback_btns(
        btns={
            "◀️ Пред": f"closed_bids_{slide - 1}",
            "🏠 Вернуться": f"admin_panel",
            "След ➡️": f"closed_bids_{slide + 1}"
        }, sizes=(3, )
    )


async def users_buttons(slide, total_users):
    total_users_on_page = 20
    if slide * total_users_on_page >= total_users:
        return get_callback_btns(
            btns={
                "◀️ Пред": f"view_stats_{slide - 1}",
                "🏠 Вернуться": f"admin_panel",
            }, sizes=(3,)
        )
    if not slide:
        if total_users <= total_users_on_page:
            return get_callback_btns(
                btns={
                    "🏠 Вернуться": f"admin_panel",
                },
                sizes=(2,)
            )
        return get_callback_btns(
            btns={
                "🏠 Вернуться": f"admin_panel",
                "След ➡️": f"view_stats_{slide + 1}"
            },
            sizes=(2, )
        )
    return get_callback_btns(
        btns={
            "◀️ Пред": f"view_stats_{slide - 1}",
            "🏠 Вернуться": f"admin_panel",
            "След ➡️": f"view_stats_{slide + 1}"
        }, sizes=(3,)
    )


async def help_messages_btns(help_messages, slide):
    total = 5

    if not slide:
        if len(help_messages) == total:
            return get_callback_btns(
                btns={
                    "🏠 Вернуться": f"admin_panel",
                    "След ➡️": f"help_menu_{slide + 1}"
                }, sizes=(3,)
            )

        return get_callback_btns(
            btns={
                "🏠 Вернуться": f"admin_panel",
            }, sizes=(3,)
        )
    else:
        if len(help_messages) == total:
            return get_callback_btns(
                btns={
                    "◀️ Пред": f"help_menu_{slide - 1}",
                    "🏠 Вернуться": f"admin_panel",
                    "След ➡️": f"help_menu_{slide + 1}"
                }, sizes=(3,)
            )
        return get_callback_btns(
            btns={
                "◀️ Пред": f"help_menu_{slide - 1}",
                "🏠 Вернуться": f"admin_panel",
            }, sizes=(3,)
        )


async def detailed_info_user_buttons(user: User):
    return get_callback_btns(
        btns={
            "Заявки на вывод": f"get_user_bids_{user.user_id}",
            "Вся история заявок": f"get_user_all_bids_{user.user_id}",
            "Изменить баланс": f"change_balance_{user.user_id}",
            "Сделать админом": f"grant_admin_{user.user_id}",
            "Забрать админа": f"remove_admin_{user.user_id}",
            "🏠 Админ-панель": f"admin_panel",
        }, sizes=(2,2, )
    )

async def user_bid_admin_buttons(user_id, bid, last_bid, i):
    if i + 1 == last_bid:
        if bid.status == "❌ Отклонена":
            return get_callback_btns(
                btns={
                    "◀️ Обратно к стате": f"user_detailed_stats_{user_id}"
                }
            )
        return get_callback_btns(
            btns={
                "Отклонить заявку": f"deny_bid_{bid.id}",
                "◀️ Обратно к стате": f"user_detailed_stats_{user_id}"
            }
        )
    if bid.status == "❌ Отклонена":
        return
    return get_callback_btns(
        btns={
            "Отклонить заявку": f"deny_bid_{bid.id}"
        }
    )

async def get_detailed_bid_btns(bid: UserHistory):
    if bid.status == "🔄 В обработке":
        return get_callback_btns(
            btns={
                "Отклонить заявку": f"deny_bid_{bid.id}",
                "Принять заявку": f"confirm_withdraw_{bid.id}",
                "◀️ Обратно к заявкам": "view_bids"
            }, sizes=(2, 1)
        )
    else:
        return get_callback_btns(
            btns={
                "◀️ Обратно к заявкам": "closed_bids"
            }, sizes=(2, 1)
        )


async def get_check_btns(bid: UserHistory):
    return get_callback_btns(
        btns={
            "Подтвердить": f"send_check_{bid.id}",
            "Отменить": f"open_bid_{bid.id}",
            "◀️ Обратно к заявкам": "view_bids"
        }, sizes=(2, 1)
    )

async def get_back_to_bids():
    return get_callback_btns(
        btns={
            "◀️ Обратно к заявкам": "view_bids"
        }
    )


async def deny_balance(user_id):
    return get_callback_btns(
        btns={
            "◀️ Обратно к стате": f"user_detailed_stats_{user_id}"
        }
    )

async def help_user_btns(mess: HelpMessage):
    mess, user = mess[0]
    return get_callback_btns(
        btns={
            "Ответить и закрыть": f"answer_help_{mess.id}",
            "Обратно к заявкам": f"help_menu_{round(mess.id // 5)}"
        }
    )

async def admin_new_btns(help_mess: HelpMessage):
    return get_callback_btns(
        btns={
            "Ответить и закрыть": f"answer_help_{help_mess.id}",
        }
    )


async def confirm_answer_help_btns(help_mess: list[tuple[HelpMessage, User]]):
    return get_callback_btns(
        btns={
            "Подтвердить отправление": "confirm_help_answer",
            "Отменить отправку": "cancel_help_answer",
        }
    )

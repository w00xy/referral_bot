from config import MIN_BALANCE_CRYPTO, FAKE_BIDS
from database.models import User, UserHistory, HelpMessage
from utils.extra import linkify, truncate_text


async def get_ref_reg_text():
    return (
        f"<b>💸 Ваш друг отправил вам несколько USDT, чтобы получить их подпишитесь на каналы</b>"
    )


async def get_not_ref_reg_text():
    return (
        f"<b>💸 Ваш друг отправил вам несколько USDT, чтобы получить их подпишитесь на каналы</b>"
    )

async def get_start_text(user_id, referrals_total,  balance):
    ref_link = await linkify(user_id)

    balance_rub = balance * 95

    return (
        f"<b>🎉 Делись и зарабатывай</b>\n\n"
        f"<b>Пригласи друга и заработаете оба 💰</b>\n"
        f"<b>Вывод станет доступен при накоплении {MIN_BALANCE_CRYPTO} USDT</b>\n\n"
        f"<b>👤 Твоя реферальная ссылка:</b> <code>{ref_link}</code>\n\n"
        f"<b>Подтвержденных рефералов: </b> <code>{referrals_total}</code>\n\n"
        f"<b>👝 Твой баланс</b>: <code>{balance} USDT</code> (<code>{balance_rub:.1f}₽</code>)"
    )

async def get_subscribe_text():
    return (
        f"<b>📢 Что бы начать использовать бота нужно подписаться на все каналы спонсоров</b>"
    )

choose_method_text = (
    f"<b>💸 Доступные способы вывода:</b>\n\n"
    )

async def selected_currency_text(cur: str, user: User):
    return (
        f"<b>Выбранная валюта: <i>{cur}</i></b>\n\n"
        f"<b>Доступный для вывода баланс: <code>{user.balance} USDT</code></b>\n\n"
        f"<b>Введите сумму вывода: </b>"
    )

async def get_address_text(cur, amount):
    return (
        f"<b>Выбранная валюта: <i>{cur}</i></b>\n"
        f"<b>Сумма вывода: <code>{amount} USDT</code></b>\n\n"
        f"<b>Введите адрес вашего кошелька: </b>"
    )

async def get_confirm_text(user: User, amount, cur, address):
    return (
        f"<b><i>Проверьте введенные данные перед отправкой заявки!</i></b>\n\n"
        f"<b>Выбранная валюта: <i>{cur}</i></b>\n"
        f"<b>Адрес кошелька: <code>{address}</code></b>\n"
        f"<b>Сумма вывода: <code>{amount} USDT</code></b>\n"
    )

sent_bid_text = (
    f"<b>✅ Заявка успешно создана</b>\n\n"
    f"<b><i>Вы можете проверить статус заявки в истории выводов</i></b>"
)

async def get_bid_text(bid: UserHistory):
    text = (
        f"<b>📝 Заявка номер {bid.id + FAKE_BIDS}</b>\n\n"
        f"<b>Сумма: <code>{bid.amount}</code> USDT</b>\n"
        f"<b>Токен: {bid.token}</b>\n"
        f"<b>Адрес кошелька: <code>{bid.address}</code></b>\n"
        f"<b>Статус: {bid.status}</b>\n"
        f"<b>Дата создания: {bid.created}</b>"
    )
    return text

no_bids_text = f"<b>Заявок не обнаружено</b>"

async def no_bid_text(bid_id: int) -> str:
    return (
        f"<b>📝 Заявка {bid_id + FAKE_BIDS}</b>\n\n"
        f"<b><i>❌ Не найдено!</i></b>"
    )

async def bid_text(bid_id: int) -> str:
    return (
        f"<b>📝 Заявка {bid_id + FAKE_BIDS}</b>\n\n"
        f"<b><i>✅ Заявка успешно отменена</i></b>"
    )

max_limit_bids_text = (
    f"❗️ Максимальное количество заявок на вывод: 3\n\n"
    f"Ограничение введено в целях более быстрой обработки заявок со стороны Администрации"
)

async def traffic_text():
    return (
        f"<b>🏆 Топ трафферов</b>\n\n"
        f"<i>1. <b>youTIK - 2491 реферал💎</b></i>\n"
        f"<i>2. <b>Андрей - 1223 реферала</b></i>\n"
        f"<i>3. <b>sng_pon4ik - 993 реферала</b></i>\n"
    )

async def bids_text(bids, slide = 0):

    total_bids_on_page = 3  # На одной странице 3 заявки

    if slide:
        start_bid = slide + total_bids_on_page - 1
    else:
        start_bid = 0

    end_bid = start_bid + total_bids_on_page

    text = (
        f"📝<b> Заявки на вывод</b>\n"
    )

    for i in range(start_bid, end_bid):
        try:
            bid = bids[i]  # Access bid directly for better readability
        except:
            text += f"❌ Конец заявок"
            break
        # if bid["status"] == "❌ Отклонена":
        #     continue  # Skip rejected bids

        try:
            text += (
                f"ID заявки: {bid['id']} для юзера {bid['id'] + FAKE_BIDS}\n"
                f"Отправитель заявки: {bid['user_id']} | {'@' + bid['user'].username if bid['user'].username else 'Нет юзернейма'}\n"
                f"Сумма: {bid['amount']}\n"
                f"Токен: {bid['token']}\n"
                f"Адрес: {bid['address']}\n"
                f"Статус: {bid['status']}\n"
                f"Дата создания: {bid['created']}\n"  # Assuming 'created' exists in bid dictionary
                f"/open_bid_{bid['id']} - открыть заявку\n\n"
            )
        except IndexError:
            text += f"❌ Конец заявок"
            break

    return text


async def get_detailed_bid_text(bid: UserHistory):
    return (
        f"📝 ID заявки: {bid.id} для юзера {bid.id + FAKE_BIDS}\n"
        f"Отправитель заявки: {bid.user_id} | {'@' + bid.user.username if bid.user.username else 'Нет юзернейма'}\n"
        f"Сумма: {bid.amount} USDT\n"
        f"Токен: {bid.token}\n"
        f"Адрес: {bid.address}\n"
        f"Статус: {bid.status}\n"
        f"Дата создания: {bid.created}\n"
    )


async def users_text(users: list[User], slide: int = 0) -> str:
    total_users_on_page = 20  # На одной странице 20 юзерова

    if slide:
        start = total_users_on_page + (total_users_on_page * (slide - 1))
    else:
        start = 0

    end = start + total_users_on_page

    total_users = len(users)
    total_bal = sum(user.balance or 0 for user in users) 
    
    text = (
        f"👥 <b>Статистика пользоваталей</b>\n"
        f"<b>Всего пользователей:<i> {total_users}</i></b>\n"
        f"<b>В общем баксов:<i> {total_bal} USDT</i></b>\n"
        f"Отправьте в чат user_id что бы получить подробную инормацию о пользователе\n\n"
    )

    for i in range(start, end):
        try:
            user = users[i]  # Access bid directly for better readability
        except:
            text += f"\n❌ Конец юзеров"
            break

        try:
            text += (
                f"{i + 1}. user_id: {user.user_id} | {'@' + user.username if user.username else 'нет ссылки'} | "
                f"Баланс: {user.balance:.1f}\n"
            )
        except IndexError:
            text += f"\n❌ Конец заявок"
            break

    return text

async def get_check_text(check: str, bid: UserHistory):
    return (
        f"✍️ Сообщение для пользователя:\n{check}\n\n"
        f"ID заявки: {bid.id} для юзера {bid.id + FAKE_BIDS}\n"
        f"Отправитель заявки: {bid.user_id} | {'@' + bid.user.username if bid.user.username else 'Нет юзернейма'}\n"
        f"Сумма: {bid.amount}\n"
        f"Статус после отправления: ✅ Успешно"
    )

async def detailed_info_user_text(user: User):
    text = (
        f"👥 Подробная инфа о юзере\n\n"
        f"Имя: {user.user_first_name}\n"
        f"Юзер: {'@' + user.username if user.username else 'Нет юзернейма'}\n"
        f"user_id: {user.user_id}\n"
        f"Баланс: {user.balance} USDT\n"
        f"Статус: {'Admin' if user.is_admin else 'User'}\n"
        f"Дата регистрации: {user.created}"
    )
    return text


user_help_start_mess = (
    f"<b>📬 Следующее сообщение будет направлено Администратору!</b>\n\n"
    f"Администратор сможет увидеть всю вашу активность, включая заявки на вывод, баланс и тд.\n"
    f"Подробно опишите вашу проблему."
)

async def admin_answer_help_text(user_help: HelpMessage):
    return (
        f"📄 Предыдущий ответ от администратора\n\n"
        f"{user_help.answer}"
    )


async def user_help_added_text(text, user_id):
    return (
    f"<b>⏳ Ваша заявка добавлена в очередь!</b>\n"
    f"<b>Ожидайте ответа от Администратора.</b>\n\n"
    f"<b>Вопрос:</b> {text}\n\n"
    f"<b>User id:</b> {user_id}"
)

async def already_has_help_message_text(help: HelpMessage):
    return (
        f"🚫<b> У вас уже есть активное обращение в поддержку</b>\n"
        f"<b>Дождитесь ответа прежде чем снова задать вопрос.</b>\n\n"
        f"<b>Ваше обращение:</b> {help.text}\n\n"
        f"<b>User id:</b> {help.user_id}"
    )


async def help_messages_text(messages: list[tuple[HelpMessage, User]], slide: int = 0):
    text = (
        f"🆘 <b>Обращения в поддержку</b>\n\n"
    )

    for mess_tuple in messages:
        mess, user = mess_tuple
        try:
            text += (
                f"🔰 Заявка №{mess.id}\n"
                f"👥 Отправитель: {'@' + user.username if user.username else 'Нет юзернейма'} | {mess.user_id}\n"
                f"Текст: {truncate_text(mess.text)}\n"
                f"Ответить - /help_answer_{mess.id}\n\n"
            )
        except IndexError:
            text += f"\n❌ Конец сообщений"
            break

    return text

async def help_text(help_message: list[tuple[HelpMessage, User]]):
    mess, user = help_message[0]

    return (
        f"🔰 Обращение №{mess.id}\n\n"
        f"👥 Отправитель: {'@' + user.username if user.username else 'Нет юзернейма'} | {mess.user_id}\n\n"
        f"Текст: {mess.text}\n\n"
        f"Статус: {'⏳ Ожидает ответ' if not mess.answer else '✅ Решен'}\n"
        f"Дата создания: {mess.created}"
    )

admin_wait_help_text =(
    f"Напишите сообщение которое будет отправлено пользователю\n\n"
    f"А также после этого обращение в поддержку будет закрыто и пользователь сможет написать снова!"
)

async def help_text_confirm(help_mess: list[tuple[HelpMessage, User]], admin_text):
    mess, user = help_mess[0]
    return (
        f"📨 Ответ пользователю {'@' + user.username if user.username else 'Нет юзернейма'} | {mess.user_id}\n\n"
        f"Сообщение: {admin_text}\n\n"
        f"Обращение будет автоматически закрыто!"
    )

help_answered_text = (
    f"<b>Ответ успешно доставлен до пользователя!\n"
    f"Заявка считается закрытой</b>"
)
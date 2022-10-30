from telebot import types

from src.functions import thread
from src.tg_functions import bot
from src.user_methods import active_users, load_user


@thread
def check_message(person_id, body, message):
    if person_id not in active_users:
        load_user(person_id)
    active_users[person_id].check_msg(body, message)


@thread
def check_payload(person_id, payload):
    if person_id not in active_users:
        load_user(person_id)
    active_users[person_id].check_payload(payload)

@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    print(f"<{call.from_user.id}> {call.data} (event)")
    check_payload(call.from_user.id, call)

# message handler
@bot.message_handler(
    content_types=['animation', 'audio', 'contact', 'dice', 'document', 'location', 'photo', 'poll', 'sticker', 'text',
                   'venue', 'video', 'video_note', 'voice'])
def get_message(message: types.Message):
    # print(message)
    check_message(message.chat.id, message.text, message)


# start bot
bot.infinity_polling(skip_pending=True)

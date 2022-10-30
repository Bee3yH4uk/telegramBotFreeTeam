from keyboa import Keyboa
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from src.database import *


def create_keyboard_departments(departments):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for department in departments:
        markup.add(KeyboardButton(department))
    return markup


def create_keyboard_departments_inline():
    new_keyboard = []
    for department in get_table('department'):
        new_keyboard.append([(department['name'], str({'a': 'click_department', 'id': department['id']})),
                             ('❌Удалить', str({'a': 'delete_department', 'id': department['id']}))])
    new_keyboard.append([('Добавить отдел', str({'a': 'add_department'}))])
    new_keyboard.append([('Назад', str({'a': 'open_main_admin'}))])
    return Keyboa(items=new_keyboard)()


def create_keyboard_interest(user_id):
    selected_interest = get_table('user', {'telegram_id': user_id})[0]['interests']
    selected_interest = selected_interest.split(',') if selected_interest else []
    k = 0
    new_keyboard = []
    for interest in get_table('interest', current_query=f'telegram_id IS NULL or telegram_id={user_id}'):
        add_ok = False
        if selected_interest and interest['name'] in selected_interest:
            add_ok = True
        if k == 0:
            new_keyboard.append([])
        new_keyboard[-1].append((f"{interest['name']}{'[✅]' if add_ok else ''}",
                                 str({'a': 'set_interest', 'id': interest['id']})))
        k += 1
        if k == 2:
            k = 0
    new_keyboard.append([('Добавить свой интерес', str({'a': 'add_interest'}))])
    new_keyboard.append([('✅Готово✅', str({'a': 'finish_interest'}))])
    keyboard = Keyboa(items=new_keyboard)()
    return keyboard


skip_photo = Keyboa(items=[('Назад', str({'a': 'step_interest'})), ("Пропустить", str({'a': 'skip_photo'}))])()

skip_add_interest = Keyboa(items=[('Отмена', str({'a': 'skip_add_interest'}))])()

profile_markup = Keyboa(items=[
    [('Изменить фото', str({'a': 'change_photo'})),
     ('Заполнить заново', str({'a': 'refill_profile'}))],
    [('Начать поиск', str({'a': 'start_find'}))]
])()

admin_markup = Keyboa(items=[
    [('Отделы компании', str({'a': 'show_departments'})),
     ('Информация о пользователях', str({'a': 'users_info'}))]
])()


def send_feedback(id):
    return Keyboa(items=[('Оставить отзыв', str({'a': 'feedback', 'id': id}))])()

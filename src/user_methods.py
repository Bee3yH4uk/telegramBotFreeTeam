import base64
import json
from datetime import datetime
from io import BytesIO

import Levenshtein
from telebot.types import ReplyKeyboardRemove

from src.database import *
from src.tg_functions import bot, save_photo
from src.tg_keyboards import create_keyboard_departments, create_keyboard_interest, skip_photo, skip_add_interest, \
    profile_markup, admin_markup, create_keyboard_departments_inline, send_feedback

active_users = {}


class BotUser:

    def __init__(self, user_id):
        self.user_id = user_id
        person_info = get_table('user', {'telegram_id': user_id})[0]
        # print(person_info)
        self.step = person_info.get('step')
        self.id = person_info.get('id')
        self.registration_date = person_info.get('registration_date')
        self.role_id = person_info.get('role_id')
        self.surname = person_info.get('surname')
        self.name = person_info.get('name')
        self.patronymic = person_info.get('patronymic')
        self.age = person_info.get('age')
        self.interests = person_info.get('interests')
        self.city = person_info.get('city')
        self.photo = person_info.get('photo')
        self.department = person_info.get('department')
        self.feedback_id = None

    def msg(self, *args, **kwargs):
        bot.send_message(self.user_id, *args, **kwargs)

    def update_step(self, step_name):
        self.step = step_name
        update_table('user', {'telegram_id': self.user_id}, step=step_name)

    def check_msg(self, body, message):

        print(f"<{message.chat.id}> {message.text} {self.step} {self.role_id}")

        if self.role_id == 2:
            if self.step == 'wait_surname' and body:
                if body.isalpha():
                    self.surname = body.title()
                    update_table('user', {'telegram_id': self.user_id}, surname=self.surname)
                    self.msg("Напишите Ваше имя.")
                    self.update_step('wait_name')
                else:
                    self.msg("❗Фамилия должна содержать только буквы.\nНапишите Вашу фамилию.")

            elif self.step == 'wait_name' and body:
                if body.replace('-', '').isalpha():
                    self.name = body.title()
                    update_table('user', {'telegram_id': self.user_id}, name=self.name)
                    self.msg("Напишите Ваше отчество.")
                    self.update_step('wait_patronymic')
                else:
                    self.msg("❗Имя должно содержать только буквы.\nНапишите Ваше имя.")

            elif self.step == 'wait_patronymic' and body:
                if body.isalpha():
                    self.patronymic = body.title()
                    update_table('user', {'telegram_id': self.user_id}, patronymic=self.patronymic)
                    self.hr_profile()
                    self.update_step('registered')
                else:
                    self.msg("❗Отчество должно содержать только буквы.\nНапишите Ваше отчество.")


            elif not self.surname:
                self.msg("Приветствуем, для начала работы необходимо заполнить данные!\nНапишите Вашу фамилию.")
                self.update_step('wait_surname')

            elif not self.name:
                self.msg("Напишите Ваше имя.")
                self.update_step('wait_name')

            elif not self.patronymic:
                self.msg("Напишите Ваше отчество.")
                self.update_step('wait_patronymic')

            elif self.step == 'wait_add_department' and body:
                insert_table('department', name=body)
                self.update_step('registered')
                self.msg('Отделы компании:', reply_markup=create_keyboard_departments_inline())
            else:
                self.msg('Воспользуйтесь клавиатурой', reply_markup=admin_markup)

        if self.role_id == 1:
            if not self.step and not self.name:
                self.msg(
                    "👋Привет! Я помогу найти тебе друзей по интересам. Для начала необходимо узнать немного информации"
                    "о тебе.\nКак тебя зовут?")
                self.update_step('wait_name')

            elif self.step == 'wait_name' and body:
                if body.isalpha():
                    self.name = body.title()
                    update_table('user', {'telegram_id': self.user_id}, name=self.name)
                    self.msg("Сколько тебе лет?")
                    self.update_step('wait_age')
                else:
                    self.msg("❗Имя должно содержать только буквы.\nКак тебя зовут?")

            elif not self.name:
                self.msg("Как тебя зовут?")
                self.update_step('wait_name')

            elif self.step == 'wait_age' and body:
                if body.isdigit() and 0 < int(body) < 120:
                    self.age = int(body)
                    update_table('user', {'telegram_id': self.user_id}, age=self.age)
                    self.msg("Из какого ты города?")
                    self.update_step('wait_city')
                else:
                    self.msg("❗Возраст введен некорректно.\nСколько тебе лет?")

            elif not self.age:
                self.msg("Сколько тебе лет?")
                self.update_step('wait_age')

            elif self.step == 'wait_city' and body:
                departments = [el['name'] for el in get_table('department')]
                if body.replace('-', '').replace(' ', '').isalpha():
                    self.city = body.title()
                    update_table('user', {'telegram_id': self.user_id}, city=self.city)
                    self.msg("Выберите ваш отдел", reply_markup=create_keyboard_departments(departments))
                    self.update_step('wait_department')
                else:
                    self.msg("❗Город введен некорректно.\nИз какого ты города?")

            elif not self.city:
                self.msg("Из какого ты города?")
                self.update_step('wait_city')

            elif self.step == 'wait_department' and body:
                departments = [el['name'] for el in get_table('department')]
                if body in departments:
                    self.department = body
                    update_table('user', {'telegram_id': self.user_id}, department=self.department)
                    self.msg("Отделение успешно выбрано!", reply_markup=ReplyKeyboardRemove())
                    self.msg("Выберите интересы", reply_markup=create_keyboard_interest(self.user_id))
                    self.update_step('wait_interest')
                else:
                    self.msg("❗Ты выбрал неверный отдел.\nВыберите ваш отдел",
                             reply_markup=create_keyboard_departments(departments))

            elif not self.department:
                departments = [el['name'] for el in get_table('department')]
                self.msg("Выберите ваш отдел", reply_markup=create_keyboard_departments(departments))
                self.update_step('wait_department')

            elif self.step == 'wait_interest':
                self.msg("Выберите интересы", reply_markup=create_keyboard_interest(self.user_id))

            elif not self.interests:
                self.msg('Выберите интересы', reply_markup=create_keyboard_interest(self.user_id))
                self.update_step('wait_interest')

            elif self.step == 'wait_your_interest' and body:
                insert_table('interest', name=body, telegram_id=self.user_id)
                person_interests = get_table('user', {'telegram_id': self.user_id})[0]['interests']
                person_interests = person_interests.split(',') if person_interests else []
                person_interests.append(body)
                self.interests = ','.join(person_interests)
                update_table('user', {'telegram_id': self.user_id}, interests=self.interests)
                self.update_step('wait_interest')
                self.msg("Выберите интересы", reply_markup=create_keyboard_interest(self.user_id))

            elif self.step == 'wait_photo':
                if message.content_type == 'photo':
                    self.photo = save_photo(message)
                    update_table('user', {'telegram_id': self.user_id}, photo=self.photo)
                    self.update_step('registered')
                    self.my_profile()
                else:
                    self.msg('Пришлите ваше фото', reply_markup=skip_photo)

            elif self.step == 'registered':
                self.my_profile()
            elif self.step == 'wait_feedback' and body:
                self.msg('Спасибо за отзыв')
                insert_table('feedback', from_user_id=self.user_id, to_user_id=self.feedback_id, message=body)
                self.update_step('registered')
                self.my_profile()
            else:
                self.msg('Не понимаю тебя')

    def hr_profile(self):
        self.msg("Профиль HR-менеджера:\n"
                 f"{self.surname} {self.name} {self.patronymic}\n"
                 f"Функции:",
                 reply_markup=admin_markup)

    def my_profile(self):
        if self.photo:
            f = BytesIO(base64.b64decode(self.photo))
            bot.send_photo(self.user_id, f, 'Так выглядит твоя анкета:\n\n'
                                            f'{self.name}, {self.age}, {self.city}', reply_markup=profile_markup)
        else:
            self.msg('Так выглядит твоя анкета:\n\n'
                     f'{self.name}, {self.age}, {self.city}', reply_markup=profile_markup)

    def find_friend(self):
        my_interests = self.interests.split(',')
        find_users = {}
        for user in get_table('user'):
            if user.get('id') == self.id:
                continue
            total_result = 0
            user_interests = user.get('interests')
            if not user_interests:
                continue
            for user_interest in user_interests.split(','):
                current_interest_results = []
                for my_interest in my_interests:
                    current_interest_results.append(Levenshtein.distance(user_interest, my_interest))
                total_result += 20 - min(current_interest_results)
            find_users[user['id']] = total_result
        return find_users

    def check_payload(self, payload):
        msg_id = payload.message.message_id

        try:
            event = json.loads(payload.data.replace("'", '"'))
        except:
            event = {}
        print(event)

        if event.get('a') == 'step_interest':
            self.update_step('wait_interest')
            bot.edit_message_text("Выберите интересы", self.user_id, msg_id,
                                  reply_markup=create_keyboard_interest(self.user_id))

        if event.get('a') == 'set_interest':
            if self.step == 'wait_interest':
                person_interests = get_table('user', {'telegram_id': self.user_id})[0]['interests']
                person_interests = person_interests.split(',') if person_interests else []
                current_interest = get_table('interest', {'id': event.get('id')})[0]['name']
                if person_interests and current_interest in person_interests:
                    bot.answer_callback_query(callback_query_id=payload.id, text=f"Вы убрали {current_interest}")
                    person_interests.remove(current_interest)
                    self.interests = ','.join(person_interests)
                    update_table('user', {'telegram_id': self.user_id}, interests=self.interests)
                else:
                    person_interests.append(current_interest)
                    self.interests = ','.join(person_interests)
                    update_table('user', {'telegram_id': self.user_id}, interests=self.interests)
                    bot.answer_callback_query(callback_query_id=payload.id, text=f"Вы выбрали {current_interest}")
                bot.edit_message_text(chat_id=payload.from_user.id, message_id=msg_id,
                                      text='Выберите интересы',
                                      reply_markup=create_keyboard_interest(self.user_id))

        if event.get('a') == 'add_interest':
            bot.delete_message(self.user_id, msg_id)
            self.update_step('wait_your_interest')
            self.msg("Введите свой интерес", reply_markup=skip_add_interest)

        if event.get('a') == 'skip_add_interest':
            self.update_step('wait_interest')
            bot.edit_message_text("Выберите интересы", self.user_id, msg_id,
                                  reply_markup=create_keyboard_interest(self.user_id))

        if event.get('a') == 'finish_interest':
            self.update_step('wait_photo')
            bot.edit_message_text('Пришлите ваше фото', self.user_id, msg_id, reply_markup=skip_photo)

        if event.get('a') == 'skip_photo':
            self.update_step('registered')
            self.my_profile()

        if event.get('a') == 'change_photo':
            self.update_step('wait_photo')
            self.msg('Пришлите ваше фото', reply_markup=skip_photo)

        if event.get('a') == 'refill_profile':
            self.msg('Как тебя зовут?')
            self.update_step('wait_name')

        if event.get('a') == 'show_departments':
            bot.edit_message_text('Отделы компании:', self.user_id, msg_id,
                                  reply_markup=create_keyboard_departments_inline())

        if event.get('a') == 'open_main_admin':
            bot.delete_message(self.user_id, msg_id)
            self.hr_profile()

        if event.get('a') == 'click_department':
            bot.answer_callback_query(callback_query_id=payload.id, text=f"Ничего не произошло")

        if event.get('a') == 'delete_department':
            delete_table('department', {'id': event.get('id')})
            bot.answer_callback_query(callback_query_id=payload.id, text=f"Успешно удалено")
            bot.edit_message_text('Отделы компании:', self.user_id, msg_id,
                                  reply_markup=create_keyboard_departments_inline())

        if event.get('a') == 'add_department':
            self.update_step('wait_add_department')
            self.msg('Введите название отдела:')

        if event.get('a') == 'users_info':
            feedbacks = get_table('feedback')
            msg_text = f'Всего пользователей: {len(get_table("user"))}\n{"Фидбеки:" if feedbacks else ""}'
            for feedback in feedbacks:
                msg_text += f"[{feedback['id']}] Пользователь #{feedback['from_user_id']}: {feedback['message']}\n\n"
            self.msg(msg_text)

        if event.get('a') == 'feedback':
            self.msg('Напишите отзыв о собеседнике: ')
            self.update_step('wait_feedback')
            self.feedback_id = event.get('id')

        if event.get('a') == 'start_find':
            bot.answer_callback_query(callback_query_id=payload.id, text=f"Поиск собеседника")
            found_friends = self.find_friend()
            if found_friends:
                sorted_values = sorted(found_friends.values())
                sorted_dict = {}
                for i in sorted_values:
                    for k in found_friends.keys():
                        if found_friends[k] == i:
                            sorted_dict[k] = found_friends[k]
                            break
                best_find = list(sorted_dict.items())[-1]
                best_find_user = get_table('user', {'id': best_find[0]})[0]
                if best_find_user.get('photo'):
                    f = BytesIO(base64.b64decode(best_find_user.get('photo')))
                    bot.send_photo(self.user_id, f, 'Найден собеседник:\n'
                                                    f'{best_find_user.get("name")}, {best_find_user.get("age")},'
                                                    f' {best_find_user.get("city")}\n'
                                                    f'Telegram: @{best_find_user.get("telegram_nick")}',
                                   reply_markup=send_feedback(best_find_user.get('id')))
                else:
                    self.msg('Найден собеседник:\n'
                             f'{best_find_user.get("name")}, {best_find_user.get("age")},'
                             f' {best_find_user.get("city")}\n'
                             f'Telegram: @{best_find_user.get("telegram_nick")}',
                             reply_markup=send_feedback(best_find_user.get('id')))

            else:
                self.msg('Не удалось найти подходящего собеседника, попробуйте позже!')


def create_user(person_id):
    insert_table('user', telegram_id=person_id, registration_date=datetime.now())


def load_user(person_id):
    persons = get_table('user', {'telegram_id': person_id})
    if not persons:
        create_user(person_id)
    active_users[person_id] = BotUser(person_id)

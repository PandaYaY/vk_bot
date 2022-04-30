import traceback
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from config import bot_token
from config import test_bot_token

import time
import datetime
import json
from dateutil import relativedelta


def send_message(user_id, message, keyboard=None, message_id=None):
    if keyboard:
        keyboard = keyboard.get_keyboard()
    else:
        keyboard = VkKeyboard()
        keyboard = keyboard.get_empty_keyboard()
    vk.messages.send(random_id=int(time.time()),
                     user_id=user_id,
                     message=message,
                     reply_to=message_id,
                     keyboard=keyboard)


def data_message(user_id):
    with open('data_files/group_user.json', 'r', encoding='utf-8') as file:
        user_info = json.load(file)
    str_user_id = str(user_id)

    user = vk.users.get(user_ids=user_id)[0]
    message = f'{user["first_name"]} {user["last_name"]}\n\n' \
              f'Группа: {user_info[str_user_id]["group"]}'
    if "meta_group" in user_info[str_user_id].keys():
        message += f'\nМетагруппа: {user_info[str_user_id]["meta_group"]}'
    if "p_group" in user_info[str_user_id].keys():
        message += f'\nПодгруппы: '
        for p_group in user_info[str_user_id]["p_group"]:
            message += f'{p_group}, '
        message = message[: -2] + ' П.Гр.'

    return message


def get_main_keyboard():
    keyboard = VkKeyboard()
    weekday = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ']
    today_weekday = datetime.datetime.today().weekday()
    for i in range(today_weekday, today_weekday + 6):
        keyboard.add_button(weekday[i % 6], VkKeyboardColor.SECONDARY)
        if i == today_weekday + 4:
            keyboard.add_line()

    keyboard.add_button('Меню', VkKeyboardColor.POSITIVE)
    return keyboard


def get_menu_keyboard():
    keyboard = VkKeyboard()
    buttons = ['Группа', 'Метагруппа', 'Подгруппа']
    for label in buttons:
        keyboard.add_button(label, VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('Мои данные', VkKeyboardColor.PRIMARY)
    keyboard.add_button('Расписание', VkKeyboardColor.NEGATIVE)
    return keyboard


def get_back_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('Назад', VkKeyboardColor.NEGATIVE)
    return keyboard


def write_group(user_id, group):
    with open('data_files/group_user.json', 'r', encoding='utf-8') as file:
        users_group = json.load(file)

    if str(user_id) in users_group.keys():
        users_group[str(user_id)]['group'] = group
    else:
        user = {"group": group}
        users_group[str(user_id)] = user

    with open('data_files/group_user.json', 'w', encoding='utf-8') as file:
        json.dump(users_group, file, ensure_ascii=False)


def write_meta_group(user_id, group):
    with open('data_files/group_user.json', 'r', encoding='utf-8') as file:
        users_group = json.load(file)

    users_group[str(user_id)]["meta_group"] = group

    with open('data_files/group_user.json', 'w', encoding='utf-8') as file:
        json.dump(users_group, file, ensure_ascii=False)


def write_p_group(user_id, group):
    with open('data_files/group_user.json', 'r', encoding='utf-8') as file:
        users_group = json.load(file)

    if "p_group" not in users_group[str(user_id)].keys():
        users_group[str(user_id)]["p_group"] = [group]
    else:
        users_group[str(user_id)]["p_group"].append(group)

    users_group[str(user_id)]["p_group"] = sorted(list(set(users_group[str(user_id)]["p_group"])))

    with open('data_files/group_user.json', 'w', encoding='utf-8') as file:
        json.dump(users_group, file, ensure_ascii=False)


def delete_p_group(user_id):
    with open('data_files/group_user.json', 'r', encoding='utf-8') as file:
        users_group = json.load(file)

        p_group = users_group[str(user_id)].pop("p_group", None)
    with open('data_files/group_user.json', 'w', encoding='utf-8') as file:
        json.dump(users_group, file, ensure_ascii=False)

    message = 'Метагруппы ('
    message += ", ".join(p_group)
    message += ') удалены'
    return message


def set_p_group_message(user_id):
    message = ''

    with open('data_files/group_user.json', 'r', encoding='utf-8') as file:
        user = json.load(file)[str(user_id)]

    if "p_group" in user.keys():
        message += 'Список ваших подгрупп:'
        for i in range(len(user["p_group"])):
            message += f'\n{i+1}. {user["p_group"][i]}'

    message += '\nВведите номер подгруппы.\n' \
               'Если подгрупп больше, повторите операцию\n\n' \
               'Число от 1 до 9'

    return message


def lesson_text(lesson_dict):
    lesson_time = {"08:30 - 10:00": "1 пара",
                   "10:25 - 11:55": "2 пара",
                   "12:45 - 14:15": "3 пара",
                   "14:30 - 16:00": "4 пара",
                   "16:15 - 17:45": "5 пара",
                   "17:50 - 19:20": "6 пара",
                   "19:30 - 21:00": "7 пара"}

    message = f'{lesson_time[lesson_dict["time"]]}: {lesson_dict["time"]}\n' \
              f'{lesson_dict["name"]}'
    message += f' {lesson_dict["type"]}' if lesson_dict["type"] != 0 else ''
    if lesson_dict["teacher"] != 0:
        for i in lesson_dict["teacher"]:
            message += f'\n{i}'
    message += f'\n{lesson_dict["p_group"]}' if lesson_dict["p_group"] != 0 else ''
    message += f'\n{lesson_dict["cabinet"]} - {lesson_dict["building"]}'
    message += '\n\n'
    return message


def give_timetable(user_id, text, data):
    full_day = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

    weekday_index = days.index(text) % 6
    day = full_day[weekday_index]

    with open('data_files/group_user.json', 'r', encoding='utf-8') as file:
        users_group = json.load(file)

    user_id = str(user_id)
    group = users_group[user_id]['group']
    lessons = []
    if day in data[group].keys():
        lessons = data[group][day]
    elif 'meta_group' in users_group[user_id].keys():
        meta_group = users_group[user_id]['meta_group']
        if day in data[meta_group].keys():
            lessons.extend(data[meta_group][day])
    else:
        message = 'Пар нет,\n адыхай)'
        return message

    message = ''
    current_day = datetime.date.today() + relativedelta.relativedelta(weekday=weekday_index)
    for i in range(len(lessons)):
        for date in lessons[i]["date"]:
            if current_day == datetime.datetime.strptime(date, '%d.%m.%Y').date():
                if lessons[i]['p_group'] and "p_group" in users_group[user_id].keys():
                    if lessons[i]['p_group'][0] in users_group[user_id]["p_group"]:
                        message += lesson_text(lessons[i])
                    else:
                        break
                else:
                    message += lesson_text(lessons[i])
                    break

    if user_id == "339354339":
        message = 'Держи гад\n' + message
    if message.strip() == '':
        message = 'Пар нет, адыхай))'
    return message


def check_message(text):
    check = False
    messages_part = ['пример: "20-ИУ-1"', 'пример: "20-1-1"', 'Число от 1 до 9']

    for message in messages_part:
        if message in text:
            check = True
    return check


def bot_listen():
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text.lower()
            user_id = event.user_id
            message_id = event.message_id
            history = vk.messages.getHistory(user_id=user_id,
                                             count=3)

            if text in days:
                with open('data_files/timetable.json', 'r', encoding='utf-8') as data_file:
                    data = json.load(data_file)
                message = give_timetable(user_id, text, data)
                keyboard = get_main_keyboard()
                send_message(user_id, message, keyboard)

            elif text in ['меню', 'назад']:
                message = 'В меню можно:\n' \
                          '1. Изменить Группу\n' \
                          '2. Добавить\\Изменить Метагруппу\n' \
                          '3. Добавить\\Изменить Подгруппу'
                keyboard = get_menu_keyboard()
                send_message(user_id, message, keyboard)

            elif text == 'расписание':
                message = 'Выберите день, на который хотите посмотреть расписание'
                keyboard = get_main_keyboard()
                send_message(user_id, message, keyboard)

            elif text == 'удалить все':
                message = delete_p_group(user_id)
                keyboard = get_menu_keyboard()
                send_message(user_id, message, keyboard)

            elif text in ['начать', 'привет', 'хай', 'ку', 'q', 'асаламалейкум']:
                message = 'Привет, я бот с расписанием.\n' \
                          'Для начала давай определимся с номером группы\n' \
                          'пример: "20-ИУ-1"'
                send_message(user_id, message)

            elif history['count'] > 2 and check_message(history['items'][1]['text']):
                if 'пример: "20-ИУ-1"' in history['items'][1]['text']:
                    with open('data_files/timetable.json', 'r', encoding='utf-8') as data_file:
                        data = json.load(data_file)
                    if text in data.keys():
                        write_group(user_id, text)
                        message = 'Отлично, можете пользоваться кнопками или писать день недели'
                        keyboard = get_main_keyboard()
                        send_message(user_id, message, keyboard)
                    else:
                        message = 'Такая группа не найдена, повторите попытку\nпример: "20-ИУ-1"'
                        with open('data_files/group_user.json', 'r', encoding='utf-8') as file:
                            users = json.load(file).keys()
                        if str(user_id) in users:
                            keyboard = get_back_keyboard()
                        else:
                            keyboard = None
                        send_message(user_id, message, keyboard)

                elif 'пример: "20-1-1"' in history['items'][1]['text']:
                    if text in meta_groups:
                        write_meta_group(user_id, text)
                        message = 'Метагруппа добавлена'
                        keyboard = get_menu_keyboard()
                        send_message(user_id, message, keyboard, message_id)
                    else:
                        message = 'Такая метагруппа не найдена\nпример: "20-1-1"'
                        keyboard = get_back_keyboard()
                        send_message(user_id, message, keyboard)

                elif 'Число от 1 до 9' in history['items'][1]['text']:
                    if text in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                        write_p_group(user_id, text)
                        message = 'Подгруппа добавлена'
                        keyboard = get_menu_keyboard()
                        send_message(user_id, message, keyboard, message_id)
                    else:
                        message = 'Такая подгруппа не найдена\nпример: "20-1-1"'
                        keyboard = get_back_keyboard()
                        send_message(user_id, message, keyboard)

            elif text in ['группа', '1']:
                message = 'Введите номер группы\n' \
                          'пример: "20-ИУ-1"'
                keyboard = get_back_keyboard()
                send_message(user_id, message, keyboard)

            elif text in ['метагруппа', '2']:
                message = 'Введите номер метагруппы\n' \
                          'пример: "20-1-1"'
                keyboard = get_back_keyboard()
                send_message(user_id, message, keyboard)

            elif text in ['подгруппа', '3']:
                message = set_p_group_message(user_id)
                keyboard = get_back_keyboard()
                if 'Список ваших подгрупп:' in message:
                    keyboard.add_button('Удалить все', VkKeyboardColor.PRIMARY)
                send_message(user_id, message, keyboard)

            elif text == 'мои данные':
                message = data_message(user_id)
                keyboard = get_menu_keyboard()
                send_message(user_id, message, keyboard)

            else:
                with open('data_files/group_user.json', 'r', encoding='utf-8') as file:
                    users_group = json.load(file)
                if str(user_id) in users_group.keys():
                    message = 'Не пон, попробуйте воспользоваться кнопками'
                    keyboard = get_main_keyboard()
                    send_message(user_id, message, keyboard, message_id)
                else:
                    message = 'Не пон, напишите "Начать", чтобы продолжить'
                    keyboard = VkKeyboard(inline=True)
                    keyboard.add_button('Начать', VkKeyboardColor.POSITIVE)
                    send_message(user_id, message, keyboard, message_id)


days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб',
        'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота']

meta_groups = ["20-5-1", "20-5-2", "20-5-3", "20-7-1", "20-7-2", "20-8-1", "20-8-2", "20-1-1", "20-1-2", "20-1-3",
               "20-1-4", "20-1-5", "20-9-1", "20-9-2", "20-2-1", "20-2-2", "20-3-1", "20-3-2", "20-3-3", "20-4-1",
               "20-4-2", "20-4-3", "20-4-4", "20-4-5", "20-4-6"]

if __name__ == '__main__':
    while True:
        try:
            vk_session = vk_api.VkApi(token=bot_token)
            # vk_session = vk_api.VkApi(token=test_bot_token)

            longpoll = VkLongPoll(vk_session)
            vk = vk_session.get_api()

            print(f'{str(datetime.datetime.now())[:-10]} start')
            bot_listen()
        except Exception as e:
            print(f'{"Exception":-^60}')
            print(f'Name: {e}\n')
            print(traceback.format_exc())
            print('-' * 60)

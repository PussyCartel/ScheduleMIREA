import telebot
import requests as rq
import datetime as dt
from telebot import types
from math import floor
import json
import re

ALL_GROUP = [group for group in open('groups.txt')]
URL = 'https://mirea-scheduler-api.herokuapp.com/'
EMPTY_JSON = {'telegram_id': 0, 'group': '', 'CreatedAt': '0001-01-01T00:00:00Z', 'UpdatedAt': '0001-01-01T00:00:00Z', 'DeletedAt': None}
EMPTY_JSON_GROUP = {"ID":0,"CreatedAt":"0001-01-01T00:00:00Z","UpdatedAt":"0001-01-01T00:00:00Z","DeletedAt":None,"title":"","schedule_json":""}
FIRST_DAY = dt.date(year=2021, month=2, day=8)
WEEK = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
WEEK_RUS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
LESSON_TIME = ['9:00-10:30', '10:40-12:10', '12:40-14:10', '14:20-15:50', "16:20-17:50", "18:00-19:30"]

bot = telebot.TeleBot('1797367615:AAF72KmgWgQ_I1wNmlD6r52LV19l5Q5PfTs')


def start_msg(id):
    user_schema = rq.get(URL + 'users/get/' + str(id)).json()
    if user_schema == EMPTY_JSON:
        return f'/group XXXX-99-99'
    else:
        help_list = '''
                    /day -- Расписание на день\n/tomorrow -- Расписание на завтра\n/week -- Расписание на неделю\n/group ХХХХ-00-00 -- Сменить/поставить группу 
                '''
        return help_list


def group_change(text, id):
    group = re.findall('....-[0-9][0-9]-[0-9][0-9]', text.lower())
    print(group)
    if bool(group):
        print(group[0].upper())
        if group[0].upper() not in ALL_GROUP[0]:
            return 'Группы нет'
        else:
            user_schema = rq.get(URL + 'users/get/' + str(id)).json()
            if user_schema == EMPTY_JSON:
                rq.post(URL + "users", json={'telegram_id': id, 'group': group[0].upper()})
                return 'добавил'
            else:
                rq.put(URL + f"users/update/{id}", json={'telegram_id': id, 'group': group[0].upper()})
                return 'обновил'
    else:
        return 'Неверный ввод'


def get_schedule(id, command='') -> str:
    user_schema = rq.get(URL + 'users/get/' + str(id)).json()
    schedule = rq.get(URL + 'groups/get/' + user_schema['group']).json()['schedule_json']
    curr_day = WEEK.index(dt.date.today().strftime('%A')) + 1
    curr_week = floor(int(str(dt.date.today() - FIRST_DAY).split(" ")[0]) / 7) + 1
    schedule_for_week = json.loads(schedule)['idAndTitleOfLessons']
    if command != '':
        curr_day += 1
    schedule_for_day = [v for k, v in schedule_for_week.items()][(curr_day - 1) * 12: (curr_day) * 12]
    final_schedule = f'{WEEK_RUS[curr_day-1]}   Неделя - {curr_week}\nРасписание на сегодня:\n'
    even_or_not = 0
    if not (curr_week % 2):
        even_or_not += 1
    for p in range(even_or_not, 12, 2):
        print(str(schedule_for_day[p]))
        if str(schedule_for_day[p]) == 'None' or str(schedule_for_day[p]) == '…………………':
            continue
        final_schedule += '\n' + f"{floor(p * 0.5)+1}. " + f"{LESSON_TIME[floor(p * 0.5)]}\n" + str(schedule_for_day[p]) + '\n'
    return final_schedule


@bot.message_handler(commands=['start'])
def start_message(message):
    if message.chat.type == 'private':
        callback = start_msg(message.chat.id)
        bot.send_message(message.chat.id, callback)
    elif message.chat.type == 'group' or message.chat.type == 'supergroup':
        user_schema = rq.get(URL + 'users/get/' + str(message.from_user.id)).json()
        print(message)
        if user_schema == EMPTY_JSON:
            bot.send_message(message.chat.id, f'/group XXXX-99-99')
        else:
            help_list = '''
                        /day -- Расписание на день\n/tomorrow -- Расписание на завтра\n/week -- Расписание на неделю\n/group ХХХХ-00-00 -- Сменить/поставить группу 
                    '''
            bot.send_message(message.chat.id, help_list)


@bot.message_handler(commands=['day', 'group', 'tomorrow', 'save'])
def schedule(message):
    if message.chat.type == 'private':
        if message.text[:6] == '/group':
            string = group_change(message.text, message.chat.id)
            bot.send_message(message.chat.id, string)
        if message.text[:4] == '/day':
            bot.send_message(message.chat.id, get_schedule(message.chat.id))
        if message.text[:9] == '/tomorrow':
            bot.send_message(message.chat.id, get_schedule(message.chat.id, message.text[:9]))
    elif message.chat.type == 'group' or message.chat.type == 'supergroup':
        if message.text[:6] == '/group':
            string = group_change(message.text, message.from_user.id)
            bot.send_message(message.chat.id, string)
        if message.text[:4] == '/day':
            bot.send_message(message.chat.id, get_schedule(message.from_user.id))
        if message.text[:9] == '/tomorrow':
            bot.send_message(message.chat.id, get_schedule(message.from_user.id, message.text[:9]))


@bot.message_handler(commands=["buttons"])
def inline(message):
  key = types.InlineKeyboardMarkup()
  but_1 = types.InlineKeyboardButton(text="Сегодня", callback_data="day")
  but_2 = types.InlineKeyboardButton(text="Завтра", callback_data="tomorrow")
  but_3 = types.InlineKeyboardButton(text="Неделя", callback_data="week")
  key.add(but_1, but_2, but_3)
  bot.send_message(message.chat.id, "Расписание на", reply_markup=key)

@bot.callback_query_handler(func=lambda c:True)
def inline(c):
    if c.message.chat.type == 'private':
        if c.data == 'day':
            bot.send_message(c.message.chat.id, get_schedule(c.message.chat.id))
        if c.data == 'tomorrow':
            bot.send_message(c.message.chat.id, get_schedule(c.message.chat.id, c.data))
    elif c.message.chat.type == 'group' or c.message.chat.type == 'supergroup':
        if c.data == 'day':
            bot.send_message(c.message.chat.id, get_schedule(c.message.from_user.id))
        if c.data == 'tomorrow':
            bot.send_message(c.message.chat.id, get_schedule(c.message.from_user.id, c.message.text[:9]))


bot.polling()

import telebot
import requests as rq
import datetime as dt
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

bot = telebot.TeleBot('1797367615:AAF72KmgWgQ_I1wNmlD6r52LV19l5Q5PfTs')


def get_schedule(id, command='') -> str:
    user_schema = rq.get(URL + 'users/get/' + str(id)).json()
    schedule = rq.get(URL + 'groups/get/' + user_schema['group']).json()['schedule_json']
    curr_day = WEEK.index(dt.date.today().strftime('%A')) + 1
    curr_week = floor(int(str(dt.date.today() - FIRST_DAY).split(" ")[0]) / 7) + 1
    schedule_for_week = json.loads(schedule)['idAndTitleOfLessons']
    if command == '/tomorrow':
        curr_day += 1
    schedule_for_day = [v for k, v in schedule_for_week.items()][(curr_day - 1) * 12: (curr_day) * 12]
    final_schedule = f'{WEEK_RUS[curr_day-1]}   Неделя - {curr_week}\nРасписание на сегодня:\n'
    even_or_not = 0
    if not (curr_week % 2):
        even_or_not += 1
    for p in range(even_or_not, 12, 2):
        print(str(schedule_for_day[p]))
        if str(schedule_for_day[p]) == 'None':
            continue
        final_schedule += '\n' + f"{floor(p * 0.5)+1}. " + str(schedule_for_day[p]) + '\n'
    return final_schedule


@bot.message_handler(commands=['start'])
def start_message(message):
    print(message.chat.type)
    if message.chat.type == 'private':
        user_schema = rq.get(URL + 'users/get/' + str(message.chat.id)).json()
        if user_schema == EMPTY_JSON:
            bot.send_message(message.chat.id, f'/group XXXX-99-99')
        else:
            help_list = '''
                /day -- Расписание на день\n/tomorrow -- Расписание на завтра\n/week -- Расписание на неделю\n/group ХХХХ-00-00 -- Сменить/поставить группу 
            '''
            bot.send_message(message.chat.id, help_list)
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
            group = re.findall('....-[0-9][0-9]-[0-9][0-9]', message.text.lower())
            if bool(group):
                print(group[0].upper())
                if group[0].upper() not in ALL_GROUP[0]:
                    bot.send_message(message.chat.id, 'Группы нет')
                else:
                    user_schema = rq.get(URL + 'users/get/' + str(message.chat.id)).json()
                    if user_schema == EMPTY_JSON:
                        rq.post(URL + "users", json={'telegram_id': message.chat.id, 'group': group[0].upper()})
                        bot.send_message(message.chat.id, 'добавил')
                    else:
                        rq.put(URL + f"users/update/{message.chat.id}", json={'telegram_id': message.chat.id, 'group': group[0].upper()})
                        bot.send_message(message.chat.id, 'обновил')
            else:
                bot.send_message(message.chat.id, 'Неверный ввод')
        if message.text[:4] == '/day':
            bot.send_message(message.chat.id, get_schedule(message))
        if message.text[:9] == '/tomorrow':
            bot.send_message(message.chat.id, get_schedule(message, message.text[:9]))
    elif message.chat.type == 'group' or message.chat.type == 'supergroup':
        if message.text[:6] == '/group':
            group = re.findall('....-[0-9][0-9]-[0-9][0-9]', message.text.lower())
            if bool(group):
                print(group[0].upper())
                if group[0].upper() not in ALL_GROUP[0]:
                    bot.send_message(message.chat.id, 'Группы нет')
                else:
                    user_schema = rq.get(URL + 'users/get/' + str(message.from_user.id)).json()
                    print(message.from_user.id)
                    if user_schema == EMPTY_JSON:
                        rq.post(URL + "users", json={'telegram_id': message.from_user.id, 'group': group[0].upper()})
                        bot.send_message(message.chat.id, 'добавил')
                    else:
                        rq.put(URL + f"users/update/{message.from_user.id}", json={'telegram_id': message.from_user.id, 'group': group[0].upper()})
                        bot.send_message(message.chat.id, 'обновил')
            else:
                bot.send_message(message.chat.id, 'Неверный ввод')
        if message.text[:4] == '/day':
            bot.send_message(message.chat.id, get_schedule(message.from_user.id))
        if message.text[:9] == '/tomorrow':
            bot.send_message(message.chat.id, get_schedule(message.from_user.id, message.text[:9]))


bot.polling()

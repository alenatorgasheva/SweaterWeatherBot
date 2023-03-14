import telebot
from telebot import types

import tzlocal
from datetime import datetime

import requests
from apscheduler.schedulers.background import BackgroundScheduler

from user import User
from users import Users

users = Users('users.txt')
try:
    with open('token.txt', 'r') as f:
        TOKEN = f.read()
except:
    print("! Проблема с чтением токена.")
bot = telebot.TeleBot(TOKEN)

try:
    with open('appid.txt', 'r') as f:
        APPID = f.read()
except:
    print("! Проблема с чтением APPID.")

scheduler = BackgroundScheduler(timezone=str('Europe/Moscow'))
scheduler.start()

print("Bot is working now...")
current_datetime = datetime.now()
print(current_datetime)


@bot.message_handler(commands=['start'])
def start(message):
    """Первое сообщение бота"""
    bot_text = ["Привет! Чтобы получать сообщения с рекомендациями, введи название своего города:"]
    sent = bot.send_message(message.chat.id, bot_text[0], reply_markup=types.ReplyKeyboardRemove())
    save_reply(message.chat.id, message.text, bot_text)

    bot.register_next_step_handler(sent, set_city)

    user = User(message.chat.id)
    users.add_new(user)


@bot.message_handler(commands=['now'])
def now(message):
    """Кнопка СЕЙЧАС"""
    if users.is_exist(message.chat.id):
        user = users.find(message.chat.id)
        city = user.get_city()
        city_id = check_city(message.chat.id, city)
        try:
            bot_text, condition = now_weather(message.chat.id, city, city_id)
            # отправляем мем
            meme = send_meme(message.chat.id, user.get_img_num(), condition)
            if meme is not None:
                bot_text.append(meme)
        except Exception as e:
            print("Что-то сломалось в функции now")
            bot_text = "Что-то сломалось, позовите мою маму @danielalina :("
            bot.send_message(message.chat.id, bot_text)
            pass
        save_reply(message.chat.id, message.text, bot_text)

        return bot_text
    return None


@bot.message_handler(commands=['tomorrow'])
def tomorrow(message):
    """Кнопка ЗАВТРА"""
    if users.is_exist(message.chat.id):
        user = users.find(message.chat.id)
        s_city = user.get_city()
        city_id = check_city(message.chat.id, s_city)
        bot_text = []

        try:
            res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                               params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': APPID})
            data = res.json()
            dates = []
            tomm_temp = []
            rain = 0
            for i in data['list'][:8]:
                dates.append(i['dt_txt'].split(" ")[0])
                tomm_temp.append(i['main']['feels_like'])
                if 'snow' in i:
                    rain = 2
                elif 'rain' in i:
                    rain = 1
            if len(set(dates)) == 1:
                temperature = round(sum(tomm_temp) / len(tomm_temp))
            else:
                rain = 0
                today = dates[0]
                tomm_temp = []
                count = 0
                for i in data['list']:
                    if 'snow' in i:
                        rain = 2
                    elif 'rain' in i:
                        rain = 1
                    if i['dt_txt'].split(" ")[0] != today:
                        tomm_temp.append(i['main']['feels_like'])
                        count += 1
                    if count == 8:
                        break
                temperature = round(sum(tomm_temp) / len(tomm_temp))
            bot_text.append(f"Завтра в городе {s_city} средняя температура ощущается как {temperature}°C")
            bot.send_message(message.chat.id, bot_text[0], reply_markup=menu())
            txt, condition = clothes(message.chat.id, temperature, rain, False)
            bot_text.append(txt)

            # отправляем мем
            meme = send_meme(message.chat.id, users.find(message.chat.id).get_img_num(), condition)
            if meme is not None:
                bot_text.append(meme)
        except Exception as e:
            print("Что-то сломалось в функции tomorrow")
            bot_text.append("Что-то сломалось, позовите мою маму @danielalina :(")
            bot.send_message(message.chat.id, bot_text)
            pass
        save_reply(message.chat.id, message.text, bot_text)
        return bot_text
    return None


@bot.message_handler(commands=['future'])
def future(message):
    """Кнопка ЧЕМОДАН"""
    if users.is_exist(message.chat.id):
        bot_text = ["""Ты отправляешься в поездку или путешествие?
Я помогу тебе собрать ЧЕМОДАН с нужными вещами на 5 ближайших дней!

Для того, чтобы это сделать введи название города:"""]
        sent = bot.send_message(message.chat.id, bot_text[0], reply_markup=types.ReplyKeyboardRemove())
        save_reply(message.chat.id, message.text, bot_text)

        bot.register_next_step_handler(sent, luggage)

        return bot_text
    return None


@bot.message_handler(commands=['help'])
def help_menu(message):
    """Кнопка ПОМОЩЬ"""
    if users.is_exist(message.chat.id):
        bot_text = [""]
        with open('help.txt', 'r', encoding='UTF-8') as f:
            for line in f.readlines():
                bot_text[0] += line
        bot.send_message(message.chat.id, bot_text[0], reply_markup=menu())
        save_reply(message.chat.id, message.text, bot_text)

        return bot_text
    return None


@bot.message_handler(commands=['alarm'])
def alarm(message):
    """Кнопка УВЕДОМЛЕНИЯ"""
    if users.is_exist(message.chat.id):
        bot_text = [
            """Для того, чтобы УВЕДОМЛЕНИЯ об одежде приходили в удобное для тебя время введи время по МСК (0-23):

А если ты больше не хочешь получать уведомления, напиши мне кодовое слово ‘непишимне’"""]
        sent = bot.send_message(message.chat.id, bot_text[0], reply_markup=types.ReplyKeyboardRemove())
        save_reply(message.chat.id, message.text, bot_text)

        bot.register_next_step_handler(sent, set_alarm)

        return bot_text
    return None


@bot.message_handler(commands=['change'])
def change(message):
    """Кнопка ДРУГОЙ ГОРОД"""
    if users.is_exist(message.chat.id):
        bot_text = ["Введи город:"]
        sent = bot.send_message(message.chat.id, bot_text[0], reply_markup=types.ReplyKeyboardRemove())
        save_reply(message.chat.id, message.text, bot_text)

        bot.register_next_step_handler(sent, change_city)  # получаем ответ

        return bot_text
    return None


@bot.message_handler(commands=['open', 'menu'])
def open_menu(message):
    """Открыть меню"""
    if users.is_exist(message.chat.id):
        bot_text = ["открываю..."]
        bot.send_message(message.chat.id, bot_text[0], reply_markup=menu())
        save_reply(message.chat.id, message.text, bot_text)

        return bot_text
    return None


@bot.message_handler(commands=['close'])
def close_menu(message):
    """Закрыть меню"""
    if users.is_exist(message.chat.id):
        bot_text = ["закрываю..."]
        bot.send_message(message.chat.id, bot_text[0], reply_markup=types.ReplyKeyboardRemove())
        save_reply(message.chat.id, message.text, bot_text)

        return bot_text
    return None


@bot.message_handler(commands=['off'])
def stop(message):
    """Остановка бота"""
    if users.is_exist(message.chat.id):
        users.remove(message.chat.id)

        bot_text = ["Если станет скучно, возвращайся ❣\n"
                    "Для этого просто нажми на /start"]
        bot.send_message(message.chat.id, bot_text[0],
                         reply_markup=types.ReplyKeyboardRemove())
        save_reply(message.chat.id, message.text, bot_text)

        return bot_text
    return None


@bot.message_handler(content_types="text")
def get_user_text(message):
    """Обработка сообщений"""
    if users.is_exist(message.chat.id):
        user_text = message.text
        bot_text = []

        if user_text in ['СЕГОДНЯ', 'СЕЙЧАС']:
            bot_text.append(now(message))
        elif user_text == 'ЗАВТРА':
            bot_text.append(tomorrow(message))
        elif user_text == 'ЧЕМОДАН':
            bot_text.append(future(message))
        elif user_text == 'ПОМОЩЬ':
            bot_text.append(help_menu(message))
        elif user_text == 'УВЕДОМЛЕНИЯ':
            bot_text.append(alarm(message))
        elif user_text == 'ДРУГОЙ ГОРОД':
            bot_text.append(change(message))
        elif user_text in ['menu', 'меню', 'open']:
            bot_text.append(open_menu(message))
        elif user_text == 'close':
            bot_text.append(close_menu(message))
        else:
            # если ввели название города
            city_id = check_city(message.chat.id, message.text)
            if city_id:
                try:
                    bot_text, condition = now_weather(message.chat.id, message.text, city_id)
                    # отправляем мем
                    meme = send_meme(message.chat.id, users.find(message.chat.id).get_img_num(), condition)
                    if meme is not None:
                        bot_text.append(meme)
                except Exception as e:
                    print("Что-то сломалось в функции get_user_text")
                    bot_text.append("Что-то сломалось, позовите мою маму @danielalina :(")
                    bot.send_message(message.chat.id, bot_text)
                    pass
            else:
                bot_text.append(f"Я не знаю города с названием {message.text}.\n")

            save_reply(message.chat.id, message.text, bot_text)


def now_weather(user_id, s_city, city_id, notify=False):
    """Погода и подбор одежды на сейчас"""
    res = requests.get("http://api.openweathermap.org/data/2.5/weather",
                       params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': APPID})
    data = res.json()
    message = ""
    bot_text = []
    rain = 0
    temperature_feel = round(data['main']['feels_like'])
    if 'снег' in data['weather'][0]['description']:
        rain = 2
    elif 'дождь' in data['weather'][0]['description']:
        rain = 1
    if notify:
        message += "Привет! Это ежедневное уведомление :)\n"
    if rain == 0:
        bot_text.append(
            message + f"Сейчас в городе {s_city} {data['weather'][0]['description']}, "
                      f"температура по ощущениям {temperature_feel}°C")
    else:
        bot_text.append(f"Сейчас в городе {s_city} температура по ощущениям {temperature_feel}°C")

    bot.send_message(user_id, bot_text[0], reply_markup=menu())
    clothes_text, condition = clothes(user_id, temperature_feel, rain, True)
    bot_text.append(clothes_text)

    return bot_text, condition


def check_city(user_id, s_city):
    """Находим id города"""
    bot_text = []

    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/find",
                           params={'q': s_city, 'type': 'like', 'units': 'metric', 'APPID': APPID})
        data = res.json()
        city_id = data['list'][0]['id']
        return city_id
    except Exception as e:
        bot_text.append(f"Я не знаю города с названием {s_city}.\n")
        bot.send_message(user_id, bot_text[0], reply_markup=menu())
        return False


def clothes(user_id, temperature, is_raining, today):
    """Подбираем одежду"""
    bot_text = ""
    condition = None
    shoes = [{"угги.": list(range(-60, -31))},
             {"зимние ботинки.": list(range(-31, -13))},
             {"осенние/весенние ботинки.": list(range(0, -14, -1))},
             {"кроссовки.": list(range(1, 16))},
             {"кеды.": list(range(16, 26))},
             {"сандали.": list(range(26, 51))}]

    bottom_clothes = [{"брюки и термобелье": list(range(-30, -61, -1))},
                      {"джинсы": list(range(0, -31, -1))},
                      {"брюки": list(range(1, 26))},
                      {"шорты": list(range(26, 51))}]

    up_clothes = [{"толстовка и термобелье": list(range(-31, -61, -1))},
                  {"свитер": list(range(-10, -31, -1))},
                  {"джемпер": list(range(-9, 21))},
                  {"футболка": list(range(21, 31))},
                  {"майка": list(range(31, 51))}]

    outerwear = [{"Шуба": list(range(-31, -61, -1))},
                 {"Зимняя куртка": list(range(-11, -31, -1))},
                 {"Осенняя/весенняя куртка": list(range(-1, -11, -1))},
                 {"Ветровка": list(range(0, 15))}]

    look = [outerwear, up_clothes, bottom_clothes, shoes]

    # рекомендации
    weather = [{"Брр, на улице экстримальный холод, утепляйтесь по максимуму!\n": list(range(-60, -31))},
               {"Брр, на улице сейчас оочень холодно, утепляйтесь!\n": list(range(-31, -20))},
               {"Сейчас прохладно, лучше захвати шапку:)\n": list(range(0, -20, -1))},
               {"Сейчас прохладно, лучше надень шарф!\n": list(range(1, 15))},
               {"На улице сейчас супер, гоу гулять!\n": list(range(15, 25))},
               {"На улице сейчас жара, лучше воспользоваться солнцезащитным кремом!\n": list(range(25, 51))}]
    # цикл по рекомендациям
    if today:
        for diction in weather:
            for dict_key, dict_val in diction.items():
                for degree in dict_val:
                    if int(degree) == int(temperature):
                        bot_text += dict_key

    # цикл подбор лука
    total_look = []
    for item_of_clothing in look:
        for dictionary in item_of_clothing:
            for dict_key, dict_val in dictionary.items():
                for degree in dict_val:
                    if int(degree) == int(temperature):
                        total_look.append(dict_key)

    if int(temperature) < -10:
        condition = 'cold'
    elif int(temperature) >= 22:
        condition = 'heat'

    bot_text += "Тебе стоит надеть -> " + ", ".join(total_look) + "\n"

    if int(is_raining) == 1:
        bot_text += "Ожидается дождь, захвати зонт!"
        condition = 'rain'
    elif int(is_raining) == 2:
        bot_text += "Ожидается снег, не забудь про головной убор!"
    else:
        bot_text += "Осадков не ожидается"

    bot.send_message(user_id, bot_text, reply_markup=menu())
    return bot_text, condition


def luggage(message):
    """Подбираем одежду на несколько дней вперед"""
    s_city = message.text
    bot_text = []

    if s_city == "/off":
        stop(message)
        return
    if message.text[0] == "/":
        bot_text.append(f"Необходимо ввести название города:")
        sent = bot.send_message(message.chat.id, bot_text[0], reply_markup=types.ReplyKeyboardRemove())
        save_reply(message.chat.id, s_city, bot_text)
        bot.register_next_step_handler(sent, luggage)
    else:
        city_id = check_city(message.chat.id, s_city)
        if city_id:
            try:
                res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                                   params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': APPID})
                data = res.json()
                my_temp = []
                rain = 0
                for i in data['list']:
                    my_temp.append(i['main']['feels_like'])
                    if 'snow' in i:
                        rain = 2
                    elif 'rain' in i:
                        rain = 1
                temperature = round(sum(my_temp) / len(my_temp))
                bot_text.append(f"Ты отправляешься в поездку, завидую!\n"
                                f"Средняя температура в городе {s_city} на следующие 5 дней: {temperature}°C")
                bot.send_message(message.chat.id, bot_text[0], reply_markup=menu())

                txt, condition = clothes(message.chat.id, temperature, rain, False)
                bot_text.append(txt)
            except Exception as e:
                print("Что-то сломалось в функции chemodan")
                bot_text.append("Что-то сломалось, позовите мою маму @danielalina :(")
                bot.send_message(message.chat.id, bot_text, reply_markup=menu())
                pass
            save_reply(message.chat.id, message.text, bot_text)


def set_alarm(message):
    """Устанавливаем уведомления"""
    bot_text = []

    notify_time = message.text

    user = users.find(message.chat.id)
    s_city = user.get_city()
    id_city = check_city(message.chat.id, s_city)
    #users.set_time(message.chat.id, notify_time) #перезапись
    print(users.find(message.chat.id).get_time())
    print(notify_time)
    if notify_time == "непишимне":
        if "непишимне" in users.find(message.chat.id).get_time():
            bot_text.append("Ранее ты не был подписан на уведомления")
        else:
            scheduler.remove_job(str(message.chat.id))
            bot_text.append("Уведомления отключены.")
            users.set_time(message.chat.id, notify_time)
    elif notify_time.isdigit() and -1 < int(notify_time) < 24:
        if users.find(message.chat.id).get_time() != "непишимне":
            scheduler.remove_job(str(message.chat.id))
        bot_text.append(f"Буду писать тебе рекомендации каждый день в {notify_time}.")
        scheduler.add_job(now_weather, "cron", day_of_week='*', hour=int(notify_time), jitter=10,
                          args=(message.chat.id, s_city, id_city, True), id=str(message.chat.id))
        users.set_time(message.chat.id, notify_time)
    else:
        bot_text.append(f'не похоже на время, пытаешься меня обмануть?)0')  # тут нужно придумать сообщение
    bot.send_message(message.chat.id, bot_text[0], reply_markup=menu())
    save_reply(message.chat.id, message.text, bot_text)
    return bot_text


def send_meme(id, num=1, img_dir=None):
    """Отправляем мем"""
    if img_dir is not None:
        img_path = f"img/{img_dir}/{str(num)}.jpg"
        img = open(img_path, 'rb')
        bot.send_photo(id, img)
        return f"*картинка {img_dir}*"
    return None


def set_city(message):
    """Устанавливаем город пользователя"""
    user_text = message.text
    bot_text = []

    if user_text == "/off":
        stop(message)
        return
    elif message.text[0] == "/":
        bot_text.append("Необходимо ввести название города:")
        sent = bot.send_message(message.chat.id, bot_text[0], reply_markup=types.ReplyKeyboardRemove())
        save_reply(message.chat.id, user_text, bot_text)

        bot.register_next_step_handler(sent, set_city)
    else:
        city_id = check_city(message.chat.id, user_text)
        if city_id:
            users.set_city(message.chat.id, user_text)
            bot_text.append("Город установлен.")
            bot.send_message(message.chat.id, bot_text[0], reply_markup=menu())
            save_reply(message.chat.id, user_text, bot_text)
            return bot_text
        else:
            bot_text.append(f"Я не знаю города с названием {user_text}.\n")
            bot_text.append(f"Введи название города:")
            sent = bot.send_message(message.chat.id, bot_text[1], reply_markup=types.ReplyKeyboardRemove())
            save_reply(message.chat.id, user_text, bot_text)

            bot.register_next_step_handler(sent, set_city)

    return bot_text


def change_city(message):
    """Меняем город пользователя"""
    user_text = message.text
    bot_text = []

    if user_text == "/off":
        stop(message)
        return

    if message.text[0] == "/":
        bot_text.append(f"Необходимо ввести название города:")
        sent = bot.send_message(message.chat.id, bot_text[0], reply_markup=types.ReplyKeyboardRemove())
        save_reply(message.chat.id, user_text, bot_text)
        bot.register_next_step_handler(sent, change_city)
    else:
        city_id = check_city(message.chat.id, user_text)
        if city_id:
            bot_text.append("Город успешно изменен.")
            users.set_city(message.chat.id, user_text)
            bot.send_message(message.chat.id, bot_text[0], reply_markup=menu())
        else:
            bot_text.append(f"Я не знаю города с названием {user_text}.")
        save_reply(message.chat.id, user_text, bot_text)
    return bot_text


def save_reply(user_id, user_text, bot_text):
    """Сохраняем сообщение в журнал"""
    try:
        with open('messages.txt', 'a', encoding='UTF-8') as f:
            f.write(str(datetime.today().strftime("%Y-%m-%d %H:%M:%S")) + "\n")
            f.write("id: " + str(user_id) + "\n")
            f.write("< " + user_text + "\n")
            for txt in bot_text:
                f.write("> " + txt + "\n")
            f.write("\n")
    except:
        print("Ошибка при сохранении в файл 'messages.txt'")
        print(bot_text)
        print()


def menu():
    """Создание меню с кнопками"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    but_names = [["СЕЙЧАС", "ЗАВТРА", "ЧЕМОДАН"],
                 ["ПОМОЩЬ", "УВЕДОМЛЕНИЯ", "ДРУГОЙ ГОРОД"]]
    for but_group in but_names:
        buttons = []
        for but_name in but_group:
            but = types.KeyboardButton(text=but_name)
            buttons.append(but)
        markup.add(buttons[0], buttons[1], buttons[2])
    return markup


bot.polling(none_stop=True)

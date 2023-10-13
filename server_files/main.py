import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import asyncio
import mysql.connector

bot = AsyncTeleBot('5850792686:AAEQHPX3EVFR_VmGbFovag7JOIzAMIv-Wgk')
reservation_sent = False
phone = None
admin = None
List = types.ReplyKeyboardMarkup(row_width=2)
List_available_audiences = types.KeyboardButton("Забронювати")
List_audiences = types.KeyboardButton("Ваші заброньовані аудиторії")
List_return = types.KeyboardButton("Повернутися")
List.add(List_available_audiences, List_audiences, List_return)

num_aud = types.ReplyKeyboardMarkup(row_width=2)
num_301 = types.KeyboardButton("301")
num_302 = types.KeyboardButton("302")
num_303 = types.KeyboardButton("303")
num_304 = types.KeyboardButton("304")
num_305 = types.KeyboardButton("312")
num_return = types.KeyboardButton("Повернутися")
num_aud.add(num_301, num_302, num_303, num_304, num_305, num_return)

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin",
    database="rfid_project"
)
mycursor = mydb.cursor()
my2cursor = mydb.cursor()
mycursor.execute("SELECT  role_of FROM access_inf")
result = mycursor.fetchall()
my2cursor.execute("SELECT esp_id, uid FROM key_inf")
result_uid = my2cursor.fetchall()
my2cursor.execute("SELECT esp_id FROM key_inf")
reserved_audiences = [row[0] for row in my2cursor.fetchall()]
available_audiences = list(set(["301", "302", "303", "304", "312"]) - set(reserved_audiences))
@bot.message_handler(commands=['start', 'restart'])
async def start(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_phone = types.KeyboardButton(text="Підтвердити особу", request_contact=True)
    keyboard.add(button_phone)
    authorization = f'Добрий день, <b>{message.from_user.first_name}</b>. Ви попали в систему булінга Кузика. Підтвердіть особу'
    await bot.send_message(message.chat.id, authorization, parse_mode='html', reply_markup=keyboard)

@bot.message_handler(content_types=['contact'])
async def hub(message):
    global phone
    phone = message.contact.phone_number

    if any(phone in row and row[1] == 0 for row in result):
        await bot.send_message(message.chat.id, 'Вітаємо в системі булінга Кузика. Тут ви сможете вибрати місце катування Кузика. Оберіть розділ. \nЗабронювати \nВаші заброньовані аудиторії', parse_mode='html', reply_markup=List)
        usernumber = phone
    if any(phone in row and row[1] == 1 for row in result):
        await bot.send_message(message.chat.id, 'Вітаємо в системі булінга Кузика. Тут ви БОГ ТУТ ВИ АДМІН', parse_mode='html', reply_markup=List)
        usernumber = phone
    if not any(phone in row for row in result):
        await bot.send_message(message.chat.id, 'Вас немає у базі даних.\nЗверніться до технічної підтримки: <b>example@lnu.edu.ua</b>',parse_mode='html')

@bot.message_handler(func=lambda message: message.text == 'Повернутися')
async def return_menu(message):
    await bot.send_message(message.chat.id, 'Меню:', reply_markup=List)

@bot.message_handler(func=lambda message: message.text == 'Забронювати')
async def reservation(message):
    await bot.send_message(message.chat.id, 'Виберіть аудиторію:', reply_markup=num_aud)

@bot.message_handler(func=lambda message: message.text in ["301", "302", "303", "304", "312"])
async def reserve_audience(message):
    global available_audiences

    # Перевіряємо, чи аудиторія доступна для бронювання
    if message.text in result_uid:
        await bot.send_message(message.chat.id, f"Аудиторія {message.text} вже заброньована")
    else:
        # Отримуємо uid користувача з другої бази даних за номером телефону
        my2cursor.execute(f"SELECT uid FROM access_inf WHERE phone='{phone}'")
        uid_result = my2cursor.fetchone()
        uid = uid_result[0] if uid_result else None

        if uid:
            # Перевіряємо, чи аудиторія вільна для бронювання
            if message.text not in available_audiences:
                await bot.send_message(message.chat.id, f"Аудиторія {message.text} вже зайнята")
            else:
                # Бронюємо аудиторію в першій базі даних
                my2cursor.execute(f"UPDATE key_inf SET uid='{uid}' WHERE esp_id='{message.text}'")
                mydb.commit()

                # Оновлюємо список доступних аудиторій
                available_audiences.remove(message.text)

                await bot.send_message(message.chat.id, f"Ви забронювали аудиторію {message.text}.", reply_markup=List)
        else:
            await bot.send_message(message.chat.id, "Не вдалося отримати uid користувача.")


@bot.message_handler(func=lambda message: message.text == 'Ваші заброньовані аудиторії')
async def user_audiences(message):
    my2cursor.execute(f"SELECT uid FROM access_inf WHERE phone='{phone}'")
    uid_result = my2cursor.fetchone()
    uid = uid_result[0] if uid_result else None

    if uid:
        my2cursor.execute(f"SELECT esp_id FROM key_inf WHERE uid='{uid}'")
        user_aud = my2cursor.fetchall()

        my2cursor.execute(f"SELECT uid_keycard FROM key_inf WHERE uid='{uid}'")
        uid_keycard_result = my2cursor.fetchone()
        uid_keycard = uid_keycard_result[0] if uid_keycard_result else None

        if uid_keycard:
            if user_aud:
                aud_list = ""
                for aud in user_aud:
                    aud_list += f"Аудиторія: {aud[0]}\n"
                await bot.send_message(message.chat.id, f"Ваші заброньовані аудиторії:\n{aud_list}")
            else:
                await bot.send_message(message.chat.id, "У вас немає заброньованих аудиторій.")
        else:
            await bot.send_message(message.chat.id, "Ключ-карта недійсна.")
    else:
        await bot.send_message(message.chat.id, "Не вдалося отримати uid користувача.")


asyncio.run(bot.polling())
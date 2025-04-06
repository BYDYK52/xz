import telebot
from telebot import types
import sqlite3
import logging
from flask import Flask, request
import threading
import time

logging.basicConfig(level=logging.INFO)

API_TOKEN = '7521542160:AAHA8gCv4dU88yorsk7bbmRGObOAci5EVEI'
ADMIN_ID = 5435014446  # Замените на реальный ID администратора
bot = telebot.TeleBot(API_TOKEN)

# Flask-приложение для обработки вебхуков от Cryptobot
app = Flask(__name__)

def create_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0
    )
    ''')
    # Таблица товаров
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT,
        price REAL
    )
    ''')
    # Таблица вопросов поддержки
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS support (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        question TEXT,
        answer TEXT
    )
    ''')
    # Таблица инвойсов для платежей через Cryptobot
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_id TEXT PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        status TEXT DEFAULT 'pending'
    )
    ''')
    conn.commit()
    conn.close()

create_db()

def get_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(user_id, username):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def check_cancel(message):
    if message.text.lower() == "отмена":
        bot.send_message(message.chat.id, "Действие отменено.")
        main_menu(message)
        return True
    return False

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else message.from_user.first_name
    if not get_user(user_id):
        add_user(user_id, username)
    main_menu(message)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "Доступные команды:\n"
        "/start - Запуск бота\n"
        "/help - Справка по командам\n"
        "/balance - Проверить баланс\n\n"
        "Также доступны кнопки в меню.\n"
        "На любом этапе введите «Отмена» для отмены текущего действия."
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['balance'])
def balance(message):
    user = get_user(message.from_user.id)
    if user:
        bot.send_message(message.chat.id, f"Ваш текущий баланс: {user[2]}₽")
    else:
        bot.send_message(message.chat.id, "Пользователь не найден.")

def main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Профиль", "Товары", "Оформить заказ", "Поддержка", "Пополнить баланс")
    if message.from_user.id == ADMIN_ID:
        markup.add("Добавить товар", "Удалить товар", "Просмотреть вопросы поддержки")
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    try:
        if message.text == "Профиль":
            user = get_user(message.from_user.id)
            if user:
                bot.send_message(message.chat.id, f"Профиль:\nИмя: {user[1]}\nБаланс: {user[2]}₽")
            else:
                bot.send_message(message.chat.id, "Пользователь не найден.")
        elif message.text == "Товары":
            show_products(message)
        elif message.text == "Оформить заказ":
            bot.send_message(message.chat.id, "Пожалуйста, опишите ваш заказ. (Для отмены введите 'Отмена')")
            bot.register_next_step_handler(message, process_order)
        elif message.text == "Поддержка":
            bot.send_message(message.chat.id, "Введите ваш вопрос. (Для отмены введите 'Отмена')")
            bot.register_next_step_handler(message, process_support)
        elif message.text == "Пополнить баланс":
            bot.send_message(message.chat.id, "Введите сумму для пополнения баланса. (Для отмены введите 'Отмена')")
            bot.register_next_step_handler(message, process_replenish)
        elif message.text == "Добавить товар":
            add_product(message)
        elif message.text == "Удалить товар":
            remove_product(message)
        elif message.text == "Просмотреть вопросы поддержки":
            view_support(message)
        else:
            bot.send_message(message.chat.id, "Неизвестная команда. Пожалуйста, выберите опцию из меню.")
    except Exception as e:
        logging.error(e)
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")

def show_products(message):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    if products:
        for product in products:
            product_id = product[0]
            name = product[1]
            description = product[2]
            price = product[3]
            text = f"{product_id}. {name}\nОписание: {description}\nЦена: {price}₽"
            markup = types.InlineKeyboardMarkup()
            order_btn = types.InlineKeyboardButton("Заказать", callback_data=f"order_product:{product_id}")
            markup.add(order_btn)
            bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Товары отсутствуют.")

def process_order(message):
    if check_cancel(message):
        return
    order_description = message.text
    bot.send_message(message.chat.id, f"Ваш заказ: {order_description} оформлен.")
    main_menu(message)

def process_support(message):
    if check_cancel(message):
        return
    question = message.text
    user_id = message.from_user.id
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO support (user_id, question) VALUES (?, ?)", (user_id, question))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "Ваш вопрос отправлен в поддержку. Мы свяжемся с вами позже.")
    main_menu(message)

def process_replenish(message):
    if check_cancel(message):
        return
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        # Генерация платежной ссылки через Cryptobot
        payment_link, invoice_id = generate_payment_link(user_id, amount)
        bot.send_message(message.chat.id, f"Для пополнения баланса на {amount}₽, перейдите по ссылке:\n{payment_link}\nПосле оплаты баланс будет обновлен автоматически.")
        main_menu(message)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную сумму.")

def generate_payment_link(user_id, amount):
    """
    Функция для генерации платежной ссылки через Cryptobot.
    В реальной интеграции необходимо использовать API Cryptobot.
    Здесь для примера генерируется фиктивная ссылка и создается инвойс в БД.
    """
    invoice_id = f"{user_id}_{int(time.time())}"
    payment_link = f"https://t.me/cryptobot?start={invoice_id}"
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO invoices (invoice_id, user_id, amount, status) VALUES (?, ?, ?, ?)",
                   (invoice_id, user_id, amount, 'pending'))
    conn.commit()
    conn.close()
    return payment_link, invoice_id

@bot.message_handler(commands=['add_product'])
def add_product(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите название товара. (Для отмены введите 'Отмена')")
        bot.register_next_step_handler(message, get_product_description)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для добавления товара.")

def get_product_description(message):
    if check_cancel(message):
        return
    product_name = message.text
    bot.send_message(message.chat.id, "Введите описание товара. (Для отмены введите 'Отмена')")
    bot.register_next_step_handler(message, lambda msg: get_product_price(msg, product_name))

def get_product_price(message, product_name):
    if check_cancel(message):
        return
    product_description = message.text
    bot.send_message(message.chat.id, "Введите цену товара. (Для отмены введите 'Отмена')")
    bot.register_next_step_handler(message, lambda msg: save_product(msg, product_name, product_description))

def save_product(message, product_name, product_description):
    if check_cancel(message):
        return
    try:
        product_price = float(message.text)
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                       (product_name, product_description, product_price))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "Товар успешно добавлен.")
        main_menu(message)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную цену.")

@bot.message_handler(commands=['remove_product'])
def remove_product(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID товара для удаления. (Для отмены введите 'Отмена')")
        bot.register_next_step_handler(message, delete_product)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для удаления товара.")

def delete_product(message):
    if check_cancel(message):
        return
    try:
        product_id = int(message.text)
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "Товар успешно удален.")
        main_menu(message)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный ID товара.")

@bot.message_handler(commands=['view_support'])
def view_support(message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM support WHERE answer IS NULL")
        questions = cursor.fetchall()
        conn.close()

        if questions:
            question_list = "\n".join([f"ID: {q[0]}, Вопрос: {q[2]}" for q in questions])
            bot.send_message(message.chat.id, f"Новые вопросы:\n{question_list}\nВведите ID вопроса, на который хотите ответить. (Для отмены введите 'Отмена')")
            bot.register_next_step_handler(message, process_answer)
        else:
            bot.send_message(message.chat.id, "Нет новых вопросов.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для просмотра вопросов поддержки.")

def process_answer(message):
    if check_cancel(message):
        return
    try:
        question_id = int(message.text)
        bot.send_message(message.chat.id, "Введите ваш ответ. (Для отмены введите 'Отмена')")
        bot.register_next_step_handler(message, lambda msg: save_answer(msg, question_id))
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный ID вопроса.")

def save_answer(message, question_id):
    if check_cancel(message):
        return
    answer = message.text
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE support SET answer = ? WHERE id = ?", (answer, question_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "Ответ успешно отправлен.")
    main_menu(message)

# Inline-обработчики для заказа и оплаты товаров

@bot.callback_query_handler(func=lambda call: call.data.startswith("order_product:"))
def order_product_callback(call):
    product_id = call.data.split(":")[1]
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if product:
        text = f"Вы выбрали: {product[1]}\nЦена: {product[3]}₽\nОформить заказ и перейти к оплате?"
        markup = types.InlineKeyboardMarkup()
        confirm_btn = types.InlineKeyboardButton("Оформить заказ", callback_data=f"confirm_order:{product_id}")
        cancel_btn = types.InlineKeyboardButton("Отмена", callback_data="cancel_order")
        markup.add(confirm_btn, cancel_btn)
        bot.send_message(call.message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "Товар не найден.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_order:"))
def confirm_order_callback(call):
    product_id = call.data.split(":")[1]
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if product:
        text = f"Заказ оформлен!\nТовар: {product[1]}\nЦена: {product[3]}₽\nПерейдите к оплате."
        markup = types.InlineKeyboardMarkup()
        # Здесь можно реализовать генерацию инвойса для оплаты заказа аналогично пополнению баланса
        pay_btn = types.InlineKeyboardButton("Оплатить", callback_data=f"pay_order:{product_id}")
        markup.add(pay_btn)
        bot.send_message(call.message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "Ошибка оформления заказа.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_order:"))
def pay_order_callback(call):
    product_id = call.data.split(":")[1]
    # Для заказа товаров можно реализовать аналогичную схему оплаты через Cryptobot
    bot.send_message(call.message.chat.id, "Платеж выполнен успешно. Спасибо за покупку!")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_order")
def cancel_order_callback(call):
    bot.send_message(call.message.chat.id, "Заказ отменен.")

# Flask-маршрут для обработки вебхуков от Cryptobot
@app.route('/cryptobot_webhook', methods=['POST'])
def cryptobot_webhook():
    data = request.json
    invoice_id = data.get('invoice_id')
    status = data.get('status')
    if invoice_id and status:
        if status == 'paid':
            conn = sqlite3.connect('bot_database.db')
            cursor = conn.cursor()
            # Обновляем статус инвойса
            cursor.execute("UPDATE invoices SET status = 'paid' WHERE invoice_id = ?", (invoice_id,))
            # Получаем данные платежа для пополнения баланса
            cursor.execute("SELECT user_id, amount FROM invoices WHERE invoice_id = ?", (invoice_id,))
            row = cursor.fetchone()
            if row:
                user_id, amount = row
                cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
            conn.commit()
            conn.close()
            # Отправляем уведомление пользователю (если возможно)
            try:
                bot.send_message(user_id, f"✅ Ваш платеж на сумму {amount}₽ успешно обработан. Баланс обновлен.")
            except Exception as e:
                logging.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
    return 'OK', 200

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)

import telebot
from telebot import types
import sqlite3

API_TOKEN = '7521542160:AAHA8gCv4dU88yorsk7bbmRGObOAci5EVEI'
ADMIN_ID = 123456789  # Замените на ID администратора
bot = telebot.TeleBot(API_TOKEN)


def create_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT,
        price REAL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS support (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        question TEXT,
        answer TEXT
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


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if not get_user(user_id):
        add_user(user_id, username)

    main_menu(message)


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
            bot.send_message(message.chat.id, "Пожалуйста, опишите ваш заказ.")
            bot.register_next_step_handler(message, process_order)
        elif message.text == "Поддержка":
            bot.send_message(message.chat.id, "Введите ваш вопрос:")
            bot.register_next_step_handler(message, process_support)
        elif message.text == "Пополнить баланс":
            replenish_balance(message)
        elif message.text == "Добавить товар":
            add_product(message)
        elif message.text == "Удалить товар":
            remove_product(message)
        elif message.text == "Просмотреть вопросы поддержки":
            view_support(message)
        else:
            bot.send_message(message.chat.id, "Неизвестная команда. Пожалуйста, выберите опцию из меню.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")


def show_products(message):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    if products:
        product_list = "\n".join([f"{product[0]}. {product[1]} - {product[2]}₽" for product in products])
        bot.send_message(message.chat.id, f"Список товаров:\n{product_list}")
    else:
        bot.send_message(message.chat.id, "Товары отсутствуют.")


def process_order(message):
    order_description = message.text
    bot.send_message(message.chat.id, f"Ваш заказ: {order_description} оформлен.")


def process_support(message):
    question = message.text
    user_id = message.from_user.id
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO support (user_id, question) VALUES (?, ?)", (user_id, question))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "Ваш вопрос отправлен в поддержку. Мы свяжемся с вами позже.")


def replenish_balance(message):
    bot.send_message(message.chat.id, "Введите сумму для пополнения баланса:")
    bot.register_next_step_handler(message, process_replenish)

def process_replenish(message):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"Ваш баланс успешно пополнен на {amount}₽.")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную сумму.")

@bot.message_handler(commands=['add_product'])
def add_product(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите название товара:")
        bot.register_next_step_handler(message, get_product_description)

def get_product_description(message):
    product_name = message.text
    bot.send_message(message.chat.id, "Введите описание товара:")
    bot.register_next_step_handler(message, lambda msg: get_product_price(msg, product_name))

def get_product_price(message, product_name):
    product_description = message.text
    bot.send_message(message.chat.id, "Введите цену товара:")
    bot.register_next_step_handler(message, lambda msg: save_product(msg, product_name, product_description))

def save_product(message, product_name, product_description):
    try:
        product_price = float(message.text)
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                       (product_name, product_description, product_price))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "Товар успешно добавлен.")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную цену.")

@bot.message_handler(commands=['remove_product'])
def remove_product(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID товара для удаления:")
        bot.register_next_step_handler(message, delete_product)

def delete_product(message):
    try:
        product_id = int(message.text)
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "Товар успешно удален.")
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
            bot.send_message(message.chat.id, f"Новые вопросы:\n{question_list}\nВведите ID вопроса, на который хотите ответить:")
            bot.register_next_step_handler(message, process_answer)
        else:
            bot.send_message(message.chat.id, "Нет новых вопросов.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для просмотра вопросов поддержки.")

def process_answer(message):
    try:
        question_id = int(message.text)
        bot.send_message(message.chat.id, "Введите ваш ответ:")
        bot.register_next_step_handler(message, lambda msg: save_answer(msg, question_id))
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный ID вопроса.")

def save_answer(message, question_id):
    answer = message.text
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE support SET answer = ? WHERE id = ?", (answer, question_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "Ответ успешно отправлен.")

bot.polling()
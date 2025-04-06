import telebot
from telebot import types
import sqlite3

TOKEN = '7973090650:AAFNei-6Z_uIQggNQaiKEW6bFJ95LPvXSZY'
ADMIN_ID = 5435014446

bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect('sessions.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        status TEXT NOT NULL
    )
''')
conn.commit()

def create_session(user_id, question, status='pending'):
    cursor.execute(
        'INSERT INTO sessions (user_id, question, status) VALUES (?, ?, ?)',
        (user_id, question, status)
    )
    conn.commit()
    return cursor.lastrowid

def get_session(qid):
    cursor.execute('SELECT id, user_id, question, status FROM sessions WHERE id=?', (qid,))
    row = cursor.fetchone()
    if row:
        return {'id': row[0], 'user_id': row[1], 'question': row[2], 'status': row[3]}
    return None

def get_sessions_by_status(status):
    cursor.execute('SELECT id, user_id, question, status FROM sessions WHERE status=?', (status,))
    rows = cursor.fetchall()
    return [{'id': row[0], 'user_id': row[1], 'question': row[2], 'status': row[3]} for row in rows]

def update_session_status(qid, new_status):
    cursor.execute('UPDATE sessions SET status=? WHERE id=?', (new_status, qid))
    conn.commit()

def delete_session(qid):
    cursor.execute('DELETE FROM sessions WHERE id=?', (qid,))
    conn.commit()

def get_admin_keyboard(in_dialog=False):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if in_dialog:
        kb.row("Вопрос решён", "Отложить")
    else:
        kb.row("Вопросы", "Отложенные вопросы")
    return kb

user_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
user_keyboard.row("Связаться с поддержкой")

current_admin_reply_session = None

@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "Добро пожаловать, администратор!", reply_markup=get_admin_keyboard())
    else:
        bot.send_message(
            message.chat.id,
            "Здравствуйте!\n\nЧтобы связаться со службой поддержки, нажмите кнопку «Связаться с поддержкой» и опишите вашу проблему.",
            reply_markup=user_keyboard
        )

@bot.message_handler(func=lambda m: m.from_user.id != ADMIN_ID)
def user_handler(message):
    global current_admin_reply_session

    if message.text == "Связаться с поддержкой":
        bot.send_message(message.chat.id, "Пожалуйста, опишите ваш вопрос или проблему.")
        return

    if current_admin_reply_session:
        sess = get_session(current_admin_reply_session)
        if sess and sess['user_id'] == message.chat.id:
            bot.send_message(ADMIN_ID, f"Сообщение от пользователя {message.chat.id}: {message.text}")
            return

    qid = create_session(message.chat.id, message.text, status='pending')
    bot.send_message(message.chat.id, "Ваш вопрос отправлен администратору. Ожидайте ответа.")
    bot.send_message(ADMIN_ID, f"Новый вопрос #{qid} от пользователя {message.chat.id}:\n{message.text}")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_handler(message):
    global current_admin_reply_session

    if message.text == "Вопросы":
        pending = get_sessions_by_status('pending')
        if not pending:
            bot.send_message(ADMIN_ID, "Новых вопросов нет.")
            return
        for sess in pending:
            kb = types.InlineKeyboardMarkup()
            kb.row(types.InlineKeyboardButton("Ответить", callback_data=f"answer_{sess['id']}"))
            bot.send_message(
                ADMIN_ID,
                f"Вопрос #{sess['id']} от пользователя {sess['user_id']}:\n{sess['question']}",
                reply_markup=kb
            )
        return

    if message.text == "Отложенные вопросы":
        deferred = get_sessions_by_status('deferred')
        if not deferred:
            bot.send_message(ADMIN_ID, "Отложенных вопросов нет.")
            return
        for sess in deferred:
            kb = types.InlineKeyboardMarkup()
            kb.row(types.InlineKeyboardButton("Ответить", callback_data=f"answer_{sess['id']}"))
            bot.send_message(
                ADMIN_ID,
                f"Отложенный вопрос #{sess['id']} от пользователя {sess['user_id']}:\n{sess['question']}",
                reply_markup=kb
            )
        return

    if message.text == "Вопрос решён" and current_admin_reply_session:
        qid = current_admin_reply_session
        sess = get_session(qid)
        if sess:
            bot.send_message(sess['user_id'], "Ваш вопрос решён. Спасибо за обращение!")
            delete_session(qid)
            bot.send_message(ADMIN_ID, f"Сессия #{qid} завершена.", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(ADMIN_ID, "Сессия не найдена или уже завершена.")
        current_admin_reply_session = None
        return

    if message.text == "Отложить" and current_admin_reply_session:
        qid = current_admin_reply_session
        update_session_status(qid, 'deferred')
        bot.send_message(ADMIN_ID, f"Вопрос #{qid} отложен.", reply_markup=get_admin_keyboard())
        return

    if current_admin_reply_session:
        qid = current_admin_reply_session
        sess = get_session(qid)
        if sess:
            bot.send_message(sess['user_id'], f"Администратор: {message.text}")
        else:
            bot.send_message(ADMIN_ID, "Сессия не найдена или уже завершена.")
            current_admin_reply_session = None

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global current_admin_reply_session
    data = call.data

    if data.startswith("answer_"):
        qid = int(data.split("_")[1])
        sess = get_session(qid)
        if not sess:
            bot.answer_callback_query(call.id, "Сессия не найдена или уже обработана.")
            return
        current_admin_reply_session = qid
        update_session_status(qid, 'active')
        bot.answer_callback_query(call.id, f"Ответьте на вопрос #{qid} обычным сообщением.")
        bot.send_message(
            ADMIN_ID,
            f"Вы начали диалог с пользователем {sess['user_id']} по вопросу #{qid}.",
            reply_markup=get_admin_keyboard(in_dialog=True)
        )

bot.polling(none_stop=True)

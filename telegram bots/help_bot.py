import telebot
from telebot import types
import sqlite3
import random
import json
import os
from datetime import datetime

TOKEN = '7973090650:AAFNei-6Z_uIQggNQaiKEW6bFJ95LPvXSZY'
ADMINS_FILE = 'admins.json'
LOG_FILE = 'admin_actions.log'
CREATOR_ID = 5435014446

bot = telebot.TeleBot(TOKEN)

def get_db_connection():
    return sqlite3.connect('sessions.db')

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_admin INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                admin_id INTEGER PRIMARY KEY,
                resolved INTEGER DEFAULT 0,
                deferred INTEGER DEFAULT 0,
                last_activity TEXT DEFAULT NULL
            )
        ''')
        conn.commit()

        cursor.execute("PRAGMA table_info(sessions)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'assigned_admin' not in columns:
            cursor.execute('ALTER TABLE sessions ADD COLUMN assigned_admin INTEGER')
            conn.commit()

init_db()

def log_action(action):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action}\n")

def load_admin_ids():
    if not os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'w') as f:
            json.dump([CREATOR_ID], f)
    with open(ADMINS_FILE, 'r') as f:
        return json.load(f)

def save_admin_ids(admins):
    with open(ADMINS_FILE, 'w') as f:
        json.dump(admins, f)

ADMIN_IDS = load_admin_ids()

def create_session(user_id, question, status='pending'):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO sessions (user_id, question, status, assigned_admin) VALUES (?, ?, ?, ?)',
            (user_id, question, status, None)
        )
        conn.commit()
        return cursor.lastrowid

def get_sessions_by_status(status):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, user_id, question, status, assigned_admin FROM sessions WHERE status=?', (status,))
        return cursor.fetchall()

def update_session_status(qid, new_status, admin_id=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE sessions SET status=?, assigned_admin=? WHERE id=?', (new_status, admin_id, qid))
        conn.commit()

def update_stats(admin_id, field):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO stats (admin_id) VALUES (?)', (admin_id,))
        cursor.execute(f'UPDATE stats SET {field} = {field} + 1, last_activity = ? WHERE admin_id = ?',
                       (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), admin_id))
        conn.commit()

def get_creator_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Добавить админа", "Удалить админа")
    kb.row("Список админов", "Статистика", "Логи")
    kb.row("Вопросы", "Отложенные вопросы")  # Добавим сюда кнопки, чтобы создатель мог управлять
    return kb

def admin_handler(message):
    if message.from_user.id not in ADMIN_IDS and message.from_user.id != CREATOR_ID:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
        return

    if message.text == "Вопросы":
        sessions = get_sessions_by_status("pending")
        if sessions:
            for session in sessions:
                session_id, user_id, question, _, assigned = session
                if assigned is None:
                    update_session_status(session_id, 'processing', message.from_user.id)
                    bot.send_message(message.chat.id, f"Вопрос от пользователя {user_id} (ID {session_id}):\n{question}", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row("Решено", "Отложить"))
                    log_action(f"Админ {message.from_user.id} взял вопрос ID {session_id}")
                    return
            bot.send_message(message.chat.id, "Нет доступных вопросов.")
        else:
            bot.send_message(message.chat.id, "Вопросов нет.")
    elif message.text == "Отложенные вопросы":
        sessions = get_sessions_by_status("deferred")
        for session in sessions:
            session_id, user_id, question, _, assigned = session
            if assigned == message.from_user.id:
                update_session_status(session_id, 'processing', message.from_user.id)
                bot.send_message(message.chat.id, f"Возврат к отложенному вопросу ID {session_id} от пользователя {user_id}:\n{question}", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row("Решено", "Отложить"))
                log_action(f"Админ {message.from_user.id} вернулся к отложенному вопросу ID {session_id}")
                return
        bot.send_message(message.chat.id, "Нет отложенных вопросов.")
    elif message.text == "Решено":
        bot.send_message(message.chat.id, "Вопрос помечен как решён.")
        update_stats(message.from_user.id, 'resolved')
    elif message.text == "Отложить":
        bot.send_message(message.chat.id, "Вопрос отложен.")
        update_stats(message.from_user.id, 'deferred')

@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.from_user.id == CREATOR_ID:
        bot.send_message(message.chat.id, "Привет, создатель", reply_markup=get_creator_keyboard())
    elif message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "Привет, админ", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row("Вопросы", "Отложенные вопросы"))
    else:
        bot.send_message(message.chat.id, "Вы пользователь. Напишите вашу проблему.")

@bot.message_handler(func=lambda m: m.from_user.id == CREATOR_ID)
def creator_handler(message):
    if message.text == "Добавить админа":
        bot.send_message(message.chat.id, "Введите ID нового админа:")
        bot.register_next_step_handler(message, lambda m: add_admin(m, message))
    elif message.text == "Удалить админа":
        bot.send_message(message.chat.id, "Введите ID админа для удаления:")
        bot.register_next_step_handler(message, lambda m: remove_admin(m, message))
    elif message.text == "Список админов":
        bot.send_message(message.chat.id, f"Список: {', '.join(map(str, ADMIN_IDS))}")
    elif message.text == "Статистика":
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM stats")
            stats = cursor.fetchall()
            msg = '\n'.join([f"ID {s[0]}: Решено: {s[1]}, Отложено: {s[2]}, Последняя активность: {s[3]}" for s in stats])
            bot.send_message(message.chat.id, msg or "Нет данных")
    elif message.text == "Логи":
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = f.read()
                bot.send_message(message.chat.id, logs[-4000:] or "Лог пуст")
        else:
            bot.send_message(message.chat.id, "Лог-файл не найден.")
    else:
        admin_handler(message)

def add_admin(m, original):
    try:
        new_id = int(m.text)
        if new_id not in ADMIN_IDS:
            ADMIN_IDS.append(new_id)
            save_admin_ids(ADMIN_IDS)
            bot.send_message(original.chat.id, f"Админ {new_id} добавлен")
        else:
            bot.send_message(original.chat.id, "Админ уже есть")
    except:
        bot.send_message(original.chat.id, "Некорректный ID")

def remove_admin(m, original):
    try:
        rm_id = int(m.text)
        if rm_id in ADMIN_IDS:
            ADMIN_IDS.remove(rm_id)
            save_admin_ids(ADMIN_IDS)
            bot.send_message(original.chat.id, f"Админ {rm_id} удалён")
        else:
            bot.send_message(original.chat.id, "Нет такого админа")
    except:
        bot.send_message(original.chat.id, "Некорректный ID")

bot.polling(none_stop=True)

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

# ========== БАЗА ДАННЫХ ========== #
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
init_db()

# ========== ЛОГИ ========== #
def log_action(action):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action}\n")

# ========== АДМИНЫ ========== #
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

# ========== СЕССИИ ========== #
def create_session(user_id, question, status='pending'):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO sessions (user_id, question, status, assigned_admin) VALUES (?, ?, ?, ?)', (user_id, question, status, None))
        conn.commit()
        return cursor.lastrowid

def get_sessions_by_status(status):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, user_id, question, status, assigned_admin FROM sessions WHERE status=?', (status,))
        return cursor.fetchall()

def get_session_by_id(session_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, user_id, question, status, assigned_admin FROM sessions WHERE id=?', (session_id,))
        return cursor.fetchone()

def update_session_status(qid, new_status, admin_id=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE sessions SET status=?, assigned_admin=? WHERE id=?', (new_status, admin_id, qid))
        conn.commit()

# ========== СТАТИСТИКА ========== #
def update_stats(admin_id, field):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO stats (admin_id) VALUES (?)', (admin_id,))
        cursor.execute(f'UPDATE stats SET {field} = {field} + 1, last_activity = ? WHERE admin_id = ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), admin_id))
        conn.commit()

# ========== КНОПКИ ========== #
def get_creator_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Добавить админа", "Удалить админа")
    kb.row("Список админов", "Статистика", "Логи")
    kb.row("Вопросы", "Отложенные вопросы")
    return kb

def get_admin_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Вопросы", "Отложенные вопросы")
    return kb

def get_response_keyboard():
    return types.ReplyKeyboardMarkup(resize_keyboard=True).row("Решено", "Отложить")

# ========== ОБРАБОТКА СООБЩЕНИЙ ========== #
@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.from_user.id == CREATOR_ID:
        bot.send_message(message.chat.id, "Привет, создатель", reply_markup=get_creator_keyboard())
    elif message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "Привет, админ", reply_markup=get_admin_keyboard())
    else:
        bot.send_message(message.chat.id, "Привет! Опишите свою проблему, и админ свяжется с вами.")

@bot.message_handler(func=lambda m: m.from_user.id not in ADMIN_IDS and m.from_user.id != CREATOR_ID)
def user_message_handler(message):
    create_session(message.from_user.id, message.text)
    bot.send_message(message.chat.id, "Спасибо! Ваш вопрос отправлен. Ожидайте ответа от администратора.")

@bot.message_handler(func=lambda m: m.from_user.id in ADMIN_IDS or m.from_user.id == CREATOR_ID)
def admin_handler(message):
    if message.text == "Вопросы":
        sessions = get_sessions_by_status("pending")
        if not sessions:
            bot.send_message(message.chat.id, "Нет новых вопросов.")
        for session in sessions:
            sid, uid, question, _, assigned = session
            if assigned is None:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Ответить", callback_data=f"answer_{sid}"))
                bot.send_message(message.chat.id, f"ID {sid} | Пользователь {uid}\nВопрос: {question}", reply_markup=markup)

    elif message.text == "Отложенные вопросы":
        sessions = get_sessions_by_status("deferred")
        if not sessions:
            bot.send_message(message.chat.id, "Нет отложенных вопросов.")
        for session in sessions:
            sid, uid, question, _, assigned = session
            bot.send_message(message.chat.id, f"ID {sid} | Пользователь {uid}\nВопрос: {question}")

    elif message.text == "Решено" or message.text == "Отложить":
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM sessions WHERE assigned_admin=? AND status="processing" ORDER BY id DESC LIMIT 1', (message.from_user.id,))
            row = cursor.fetchone()
            if row:
                sid = row[0]
                new_status = "resolved" if message.text == "Решено" else "deferred"
                update_session_status(sid, new_status)
                update_stats(message.from_user.id, 'resolved' if new_status == "resolved" else 'deferred')
                bot.send_message(message.chat.id, f"Вопрос ID {sid} помечен как {new_status}.", reply_markup=get_admin_keyboard())
            else:
                bot.send_message(message.chat.id, "Нет активного вопроса.", reply_markup=get_admin_keyboard())

    elif message.text == "Список админов" and message.from_user.id == CREATOR_ID:
        usernames = []
        for aid in ADMIN_IDS:
            try:
                user = bot.get_chat(aid)
                usernames.append(f"{user.first_name} (@{user.username})")
            except:
                usernames.append(str(aid))
        bot.send_message(message.chat.id, "Список админов:\n" + '\n'.join(usernames))

    elif message.text == "Статистика" and message.from_user.id == CREATOR_ID:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM stats")
            stats = cursor.fetchall()
            msg = '\n'.join([f"ID {s[0]}: Решено: {s[1]}, Отложено: {s[2]}, Последняя активность: {s[3]}" for s in stats])
            bot.send_message(message.chat.id, msg or "Нет данных")

    elif message.text == "Логи" and message.from_user.id == CREATOR_ID:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = f.read()
                bot.send_message(message.chat.id, logs[-4000:] or "Лог пуст")
        else:
            bot.send_message(message.chat.id, "Лог-файл не найден.")

    elif message.text == "Добавить админа" and message.from_user.id == CREATOR_ID:
        bot.send_message(message.chat.id, "Введите ID нового админа:")
        bot.register_next_step_handler(message, add_admin)

    elif message.text == "Удалить админа" and message.from_user.id == CREATOR_ID:
        bot.send_message(message.chat.id, "Введите ID админа для удаления:")
        bot.register_next_step_handler(message, remove_admin)

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def handle_answer_button(call):
    sid = int(call.data.split("_")[1])
    session = get_session_by_id(sid)
    if session:
        _, uid, question, status, assigned = session
        if status == "pending":
            update_session_status(sid, "processing", call.from_user.id)
            bot.send_message(call.message.chat.id, f"Вы выбрали вопрос ID {sid}\nПользователь: {uid}\nВопрос: {question}", reply_markup=get_response_keyboard())
        else:
            bot.send_message(call.message.chat.id, "Этот вопрос уже обрабатывается другим админом.")

# ========== ДОБАВЛЕНИЕ И УДАЛЕНИЕ АДМИНА ========== #
def add_admin(message):
    try:
        new_id = int(message.text)
        if new_id not in ADMIN_IDS:
            ADMIN_IDS.append(new_id)
            save_admin_ids(ADMIN_IDS)
            bot.send_message(message.chat.id, f"Админ {new_id} добавлен")
        else:
            bot.send_message(message.chat.id, "Админ уже есть")
    except:
        bot.send_message(message.chat.id, "Некорректный ID")

def remove_admin(message):
    try:
        rm_id = int(message.text)
        if rm_id in ADMIN_IDS:
            ADMIN_IDS.remove(rm_id)
            save_admin_ids(ADMIN_IDS)
            bot.send_message(message.chat.id, f"Админ {rm_id} удалён")
        else:
            bot.send_message(message.chat.id, "Нет такого админа")
    except:
        bot.send_message(message.chat.id, "Некорректный ID")

# ========== СТАРТ БОТА ========== #
bot.polling(none_stop=True)

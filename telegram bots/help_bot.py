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

conn = sqlite3.connect('sessions.db', check_same_thread=False)
cursor = conn.cursor()

# Ensure column exists for backward compatibility
cursor.execute("PRAGMA table_info(sessions)")
columns = [col[1] for col in cursor.fetchall()]
if 'assigned_admin' not in columns:
    cursor.execute('ALTER TABLE sessions ADD COLUMN assigned_admin INTEGER')
    conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        status TEXT NOT NULL,
        assigned_admin INTEGER
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS stats (
        admin_id INTEGER PRIMARY KEY,
        resolved INTEGER DEFAULT 0,
        deferred INTEGER DEFAULT 0,
        last_activity TEXT DEFAULT NULL
    )
''')
conn.commit()

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
    cursor.execute(
        'INSERT INTO sessions (user_id, question, status, assigned_admin) VALUES (?, ?, ?, ?)',
        (user_id, question, status, None)
    )
    conn.commit()
    return cursor.lastrowid

def get_session(qid):
    cursor.execute('SELECT id, user_id, question, status, assigned_admin FROM sessions WHERE id=?', (qid,))
    row = cursor.fetchone()
    if row:
        return {'id': row[0], 'user_id': row[1], 'question': row[2], 'status': row[3], 'assigned_admin': row[4]}
    return None

def get_sessions_by_status(status):
    cursor.execute('SELECT id, user_id, question, status, assigned_admin FROM sessions WHERE status=?', (status,))
    rows = cursor.fetchall()
    return [{'id': row[0], 'user_id': row[1], 'question': row[2], 'status': row[3], 'assigned_admin': row[4]} for row in rows]

def update_session_status(qid, new_status, admin_id=None):
    cursor.execute('UPDATE sessions SET status=?, assigned_admin=? WHERE id=?', (new_status, admin_id, qid))
    conn.commit()

def update_stats(admin_id, field):
    cursor.execute('INSERT OR IGNORE INTO stats (admin_id) VALUES (?)', (admin_id,))
    cursor.execute(f'UPDATE stats SET {field} = {field} + 1, last_activity = ? WHERE admin_id = ?',
                   (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), admin_id))
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

def get_creator_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Добавить админа", "Удалить админа")
    kb.row("Список админов", "Статистика")
    kb.row("Вопросы", "Отложенные вопросы", "Логи")
    return kb

user_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
user_keyboard.row("Связаться с поддержкой")

admin_sessions = {}  # {admin_id: session_id}

@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.from_user.id == CREATOR_ID:
        bot.send_message(message.chat.id, "Добро пожаловать, создатель!", reply_markup=get_creator_keyboard())
    elif message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "Добро пожаловать, администратор!", reply_markup=get_admin_keyboard())
    else:
        bot.send_message(
            message.chat.id,
            "Здравствуйте!\n\nЧтобы связаться со службой поддержки, нажмите кнопку «Связаться с поддержкой» и опишите вашу проблему.",
            reply_markup=user_keyboard
        )

@bot.message_handler(func=lambda m: m.from_user.id == CREATOR_ID)
def creator_handler(message):
    if message.text == "Добавить админа":
        bot.send_message(message.chat.id, "Введите ID пользователя, которого хотите назначить админом:")
        bot.register_next_step_handler(message, add_admin_step)
    elif message.text == "Удалить админа":
        bot.send_message(message.chat.id, "Введите ID администратора, которого хотите удалить:")
        bot.register_next_step_handler(message, remove_admin_step)
    elif message.text == "Список админов":
        admins_list = '\n'.join([str(a) for a in ADMIN_IDS])
        bot.send_message(message.chat.id, f"Текущие администраторы:\n{admins_list}")
    elif message.text == "Статистика":
        cursor.execute('SELECT admin_id, resolved, deferred, last_activity FROM stats ORDER BY resolved DESC')
        rows = cursor.fetchall()
        if rows:
            stat_msg = "📊 Статистика по администраторам:\n"
            for r in rows:
                last = r[3] if r[3] else "Нет активности"
                stat_msg += f"ID {r[0]} — Решено: {r[1]}, Отложено: {r[2]}, Последняя активность: {last}\n"
            bot.send_message(message.chat.id, stat_msg)
        else:
            bot.send_message(message.chat.id, "Статистика пока пуста.")
    elif message.text == "Логи":
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = f.read()
                bot.send_message(message.chat.id, f"📄 Логи:\n{logs[-4000:]}")
        else:
            bot.send_message(message.chat.id, "Лог-файл пока пуст.")
    else:
        admin_handler(message)

@bot.message_handler(func=lambda m: m.from_user.id in ADMIN_IDS)
def admin_handler(message):
    admin_id = message.from_user.id
    if message.text == "Вопросы":
        pending = get_sessions_by_status("pending")
        available = [s for s in pending if s['assigned_admin'] is None]
        if not available:
            bot.send_message(admin_id, "Нет новых вопросов.")
            return
        session = random.choice(available)
        admin_sessions[admin_id] = session['id']
        update_session_status(session['id'], "in_progress", admin_id)
        log_action(f"Админ {admin_id} взял вопрос {session['id']}")
        bot.send_message(admin_id, f"📩 Вопрос от пользователя {session['user_id']}:\n{session['question']}", reply_markup=get_admin_keyboard(in_dialog=True))
    elif message.text == "Отложенные вопросы":
        deferred = get_sessions_by_status("deferred")
        mine = [s for s in deferred if s['assigned_admin'] == admin_id]
        if not mine:
            bot.send_message(admin_id, "У вас нет отложенных вопросов.")
            return
        session = random.choice(mine)
        admin_sessions[admin_id] = session['id']
        update_session_status(session['id'], "in_progress", admin_id)
        log_action(f"Админ {admin_id} вернулся к вопросу {session['id']}")
        bot.send_message(admin_id, f"📩 Возврат к вопросу пользователя {session['user_id']}:\n{session['question']}", reply_markup=get_admin_keyboard(in_dialog=True))
    elif message.text == "Вопрос решён":
        qid = admin_sessions.get(admin_id)
        if qid:
            delete_session(qid)
            update_stats(admin_id, 'resolved')
            log_action(f"Админ {admin_id} решил вопрос {qid}")
            admin_sessions.pop(admin_id, None)
            bot.send_message(admin_id, "✅ Вопрос удалён как решённый", reply_markup=get_admin_keyboard())
    elif message.text == "Отложить":
        qid = admin_sessions.get(admin_id)
        if qid:
            update_session_status(qid, "deferred", admin_id)
            update_stats(admin_id, 'deferred')
            log_action(f"Админ {admin_id} отложил вопрос {qid}")
            admin_sessions.pop(admin_id, None)
            bot.send_message(admin_id, "⏸ Вопрос отложен", reply_markup=get_admin_keyboard())

@bot.message_handler(func=lambda m: m.text == "Связаться с поддержкой")
def user_handler(message):
    bot.send_message(message.chat.id, "Опишите вашу проблему. Один из администраторов скоро свяжется с вами.")
    bot.register_next_step_handler(message, handle_question)

def handle_question(message):
    qid = create_session(message.chat.id, message.text)
    bot.send_message(message.chat.id, "Ваш вопрос принят. Ожидайте ответа от поддержки. ID запроса: " + str(qid))

def add_admin_step(message):
    try:
        new_id = int(message.text)
        if new_id not in ADMIN_IDS:
            ADMIN_IDS.append(new_id)
            save_admin_ids(ADMIN_IDS)
            bot.send_message(message.chat.id, f"Пользователь {new_id} добавлен в администраторы.")
            log_action(f"Создатель добавил админа {new_id}")
        else:
            bot.send_message(message.chat.id, "Этот пользователь уже является админом.")
    except ValueError:
        bot.send_message(message.chat.id, "Некорректный ID.")

def remove_admin_step(message):
    try:
        remove_id = int(message.text)
        if remove_id in ADMIN_IDS and remove_id != CREATOR_ID:
            ADMIN_IDS.remove(remove_id)
            save_admin_ids(ADMIN_IDS)
            bot.send_message(message.chat.id, f"Администратор {remove_id} удалён.")
            log_action(f"Создатель удалил админа {remove_id}")
        else:
            bot.send_message(message.chat.id, "Нельзя удалить этого администратора.")
    except ValueError:
        bot.send_message(message.chat.id, "Некорректный ID.")

bot.polling(none_stop=True)

import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY)')

def save_chat_id(chat_id):
    cursor.execute('INSERT OR IGNORE INTO users (chat_id) VALUES (?)', (chat_id,))
    conn.commit()

def get_all_chat_ids():
    cursor.execute('SELECT chat_id FROM users')
    return cursor.fetchall()


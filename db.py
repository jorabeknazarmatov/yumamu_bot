import sqlite3, os, dotenv
dotenv.load_dotenv()

conn = sqlite3.connect("bot_db.sqlite3")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_file_id TEXT NOT NULL,
    description TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    first_name TEXT,
    last_name TEXT,
    current_lesson INTEGER DEFAULT 1
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    lesson_id INTEGER,
    status TEXT CHECK(status IN ('watched', 'skipped', 'delayed')),
    UNIQUE(user_id, lesson_id)
)
''')

try:
    cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN pay BOOLEAN DEFAULT 0")
except sqlite3.OperationalError:
    pass


conn.commit()

def add_lesson(video_file_id: str, description: str):
    cursor.execute("INSERT INTO lessons (video_file_id, description) VALUES (?, ?)", (video_file_id, description))
    conn.commit()

def get_lesson_by_id(lesson_id: int):
    cursor.execute("SELECT video_file_id, description FROM lessons WHERE id = ?", (lesson_id,))
    return cursor.fetchone()

def get_next_lesson(current_id: int):
    cursor.execute("SELECT id, video_file_id, description FROM lessons WHERE id > ? ORDER BY id ASC LIMIT 1", (current_id,))
    return cursor.fetchone()

def get_user(telegram_id: int):
    cursor.execute("SELECT id, current_lesson FROM users WHERE telegram_id = ?", (telegram_id,))
    return cursor.fetchone()

def add_or_get_user(telegram_id: int, first_name: str = '', last_name: str = '', phone: str = '', pay: bool = False):
    user = get_user(telegram_id)
    if not user:
        cursor.execute(
            "INSERT INTO users (telegram_id, first_name, last_name, phone, pay) VALUES (?, ?, ?, ?, ?)",
            (telegram_id, first_name, last_name, phone, pay)
        )
        conn.commit()
        return get_user(telegram_id)
    return user



def update_user_lesson(telegram_id: int, lesson_id: int):
    cursor.execute("UPDATE users SET current_lesson = ? WHERE telegram_id = ?", (lesson_id, telegram_id))
    conn.commit()

def record_view(user_id: int, lesson_id: int, status: str):
    cursor.execute("REPLACE INTO views (user_id, lesson_id, status) VALUES (?, ?, ?)", (user_id, lesson_id, status))
    conn.commit()

def get_user_lesson_stats(admin_id: int):
    cursor.execute("""
        SELECT id, current_lesson FROM users WHERE telegram_id != ?
    """, (admin_id,))
    users = cursor.fetchall()

    stats = {}
    for _, current_lesson in users:
        stats[current_lesson] = stats.get(current_lesson, 0) + 1

    return stats, len(users)  # darslar statistikasi, jami foydalanuvchi

def delete_lesson_and_reorder(lesson_id: int):
    cursor.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
    conn.commit()
    # Tartibni qayta tiklash
    cursor.execute("SELECT id, video_file_id, description FROM lessons ORDER BY id")
    lessons = cursor.fetchall()

    cursor.execute("DELETE FROM lessons")
    conn.commit()

    for idx, (_, video_id, desc) in enumerate(lessons, start=1):
        cursor.execute(
            "INSERT INTO lessons (id, video_file_id, description) VALUES (?, ?, ?)",
            (idx, video_id, desc)
        )
    conn.commit()


def get_all_lessons():
    cursor.execute("SELECT id, video_file_id, description FROM lessons ORDER BY id")
    return cursor.fetchall()

def update_user_pay(telegram_id: int, pay: bool):
    cursor.execute("UPDATE users SET pay = ? WHERE telegram_id = ?", (pay, telegram_id))
    conn.commit()

def is_user_paid(telegram_id: int) -> bool:
    cursor.execute("SELECT pay FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    return result[0] == 1 if result else False

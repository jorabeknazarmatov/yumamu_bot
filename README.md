# 🎓 Yumamu Bot

Telegram bot for managing educational content with admin and user roles. Built using `aiogram` and SQLite.

## 🔧 Features

### 👤 User:
- Step-by-step course structure
- Tracks personal progress
- Interacts via inline buttons
- Automatically continues to the next lesson

### 👨‍🏫 Admin:
- Uploads video lessons
- Monitors each user’s progress
- Views total number of users and lessons
- Future: Can assign free or paid access

## 🧠 Tech Stack
- `Python 3`
- `Aiogram` (Telegram Bot Framework)
- `SQLite` (via `db.py`)
- `Inline Keyboards`

### 📂 Project Structure

```text
yumamu_bot/

├── main.py              # Main entry point
├── db.py                # Database interaction
├── keyboards.py         # Inline keyboard definitions
├── requirements.txt     # Python dependencies
├── handlers/
│   ├── admin.py         # Admin-specific handlers
│   └── user.py          # User-specific handlers
├── config/
│   └── settings.py      # Configuration variables
```

## 🚀 Getting Started

```bash
git clone https://github.com/jorabeknazarmatov/yumamu_bot
cd yumamu_bot
pip install -r requirements.txt
python main.py
```

📈 Future Plans
Inline interface improvements (avoid message stacking)

Payment integration (paid vs free content)

Admin panel with charts & control

Hosting via webhook (for 24/7 availability)

📞 Contact
Created by @jorabeknazarmatov

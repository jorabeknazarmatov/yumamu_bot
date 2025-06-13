from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Darsni yuklash", callback_data="upload_lesson")],
        [InlineKeyboardButton(text="O'quvchilar soni", callback_data="student_stats")]
    ])


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Darsni boshlash", callback_data="start_lesson")]
    ])


def lesson_feedback_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Ha", callback_data="learned_yes"),
            InlineKeyboardButton(text="Yo'q", callback_data="learned_no"),
            InlineKeyboardButton(text="Endi", callback_data="learned_later")
        ]
    ])

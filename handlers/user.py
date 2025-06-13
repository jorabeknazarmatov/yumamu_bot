from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from db import add_or_get_user, get_lesson_by_id, get_next_lesson, update_user_lesson, record_view

router = Router()

@router.message(Command("start"))
async def user_start(message: Message):
    add_or_get_user(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Darsni boshlash", callback_data="start_lesson")]
    ])
    await message.answer(f"Assalomu alaykum, {message.from_user.first_name}! O'qishni boshlash uchun quyidagi tugmani bosing:", reply_markup=keyboard)

@router.callback_query(F.data == "start_lesson")
async def start_lesson(callback: CallbackQuery):
    user = add_or_get_user(
        telegram_id=callback.from_user.id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name
    )
    user_id, current_lesson = user
    lesson = get_lesson_by_id(current_lesson)
    if lesson:
        video_id, description = lesson
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Ha", callback_data="learned_yes"),
                InlineKeyboardButton(text="Yo'q", callback_data="learned_no"),
                InlineKeyboardButton(text="Endi", callback_data="learned_later")
            ]
        ])
        await callback.message.answer_video(video_id, caption=description)
        await callback.message.answer("Darsni o'zlashtirdingizmi?", reply_markup=keyboard)
    else:
        await callback.message.answer("Siz uchun hozircha dars mavjud emas. Iltimos, keyinroq urinib ko'ring.")

@router.callback_query(F.data.startswith("learned_"))
async def handle_lesson_response(callback: CallbackQuery):
    user = add_or_get_user(
        telegram_id=callback.from_user.id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name
    )
    user_id, current_lesson = user
    response = callback.data.split("_")[1]

    if response == "yes":
        record_view(user_id, current_lesson, "watched")
        next_lesson = get_next_lesson(current_lesson)
        if next_lesson:
            next_id, video_id, description = next_lesson
            update_user_lesson(callback.from_user.id, next_id)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Ha", callback_data="learned_yes"),
                    InlineKeyboardButton(text="Yo'q", callback_data="learned_no"),
                    InlineKeyboardButton(text="Endi", callback_data="learned_later")
                ]
            ])
            await callback.message.answer("Barakalla! Keyingi darsga o'tdingiz.")
            await callback.message.answer_video(video_id, caption=description)
            await callback.message.answer("Darsni o'zlashtirdingizmi?", reply_markup=keyboard)
        else:
            await callback.message.answer("Tabriklaymiz! Barcha darslarni tugatdingiz.")
    elif response == "no":
        record_view(user_id, current_lesson, "skipped")
        await callback.message.answer("Iltimos, ushbu darsni yaxshilab o'rganing.")
    elif response == "later":
        record_view(user_id, current_lesson, "delayed")
        await callback.message.answer("Vaqtingiz ketmoqda. Iltimos, darsni o'zlashtiring.")

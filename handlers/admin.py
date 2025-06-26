from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from db import add_lesson, get_user_lesson_stats, get_all_lessons, delete_lesson_and_reorder, update_user_pay
import os, dotenv
dotenv.load_dotenv()

router = Router()

class UploadLesson(StatesGroup):
    waiting_for_video = State()
    waiting_for_description = State()

class Broadcast(StatesGroup):
    waiting_for_message = State()

keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Darsni yuklash", callback_data="upload_lesson")],
        [InlineKeyboardButton(text="👥 O'quvchilar statistikasi", callback_data="student_stats")],
        [InlineKeyboardButton(text="📚 Darslar ro'yxati", callback_data="lesson_list")],
        [InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="broadcast_message")]
    ])

@router.message(Command("start"))
async def admin_start(message: Message):
    
    await message.answer("👋 Assalomu alaykum, hurmatli Admin!\nQuyidagi tugmalar orqali boshqaruvni amalga oshirishingiz mumkin:", reply_markup=keyboard)


@router.callback_query(F.data == "upload_lesson")
async def upload_lesson_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UploadLesson.waiting_for_video)
    await callback.message.answer("🎬 Iltimos, dars videosini yuboring.")


@router.message(UploadLesson.waiting_for_video, F.video)
async def lesson_video_received(message: Message, state: FSMContext):
    await state.update_data(video_file_id=message.video.file_id)
    await state.set_state(UploadLesson.waiting_for_description)
    await message.answer("📝 Endi esa dars tavsifini (izohini) yuboring.")


@router.message(UploadLesson.waiting_for_video)
async def invalid_video_received(message: Message):
    await message.delete()
    await message.answer("❗ Iltimos, faqat video fayl yuboring.")


@router.message(UploadLesson.waiting_for_description, F.text)
async def lesson_description_received(message: Message, state: FSMContext):
    data = await state.get_data()
    video_id = data["video_file_id"]
    description = message.text
    add_lesson(video_id, description)
    await state.clear()
    await message.answer(" Darsni muvaffaqiyatli yuklaganingiz bilan tabriklayman!", reply_markup=keyboard)


@router.callback_query(F.data == "student_stats")
async def show_student_stats(callback: CallbackQuery):
    ADMIN_ID = os.getenv('ADMIN_ID')
    stats, total = get_user_lesson_stats(ADMIN_ID)
    msg = f"📊 Umumiy o‘quvchilar soni: {total} ta\n\n"
    for lesson_id in sorted(stats.keys()):
        msg += f"📘 {lesson_id}-dars: {stats[lesson_id]} ta o‘quvchi\n"
    msg += f"\n🏁 Darslarni yakunlaganlar: {total} ta"
    await callback.message.answer(msg)


@router.callback_query(F.data == "lesson_list")
async def show_lesson_list(callback: CallbackQuery):
    lessons = get_all_lessons()
    if not lessons:
        await callback.message.answer("⛔ Hozircha hech qanday dars mavjud emas.")
        return

    msg = "📚 Mavjud darslar ro'yxati:\n\n"
    for lesson_id, _, description in lessons:
        msg += f"📘 {lesson_id}-dars: {description[:50]}...\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ Darslarni to‘liq yuklash", callback_data='all_video')],
        [InlineKeyboardButton(text="🗑 Darsni o‘chirish", callback_data='delete_lesson')]
    ])
    await callback.message.answer(msg, reply_markup=kb)

@router.callback_query(F.data == "all_video")
async def send_all_lessons(callback: CallbackQuery):
    lessons = get_all_lessons()
    if not lessons:
        await callback.message.answer("🤷‍♂️ Hech qanday dars topilmadi.")
        return

    for lesson_id, video_file_id, description in lessons:
        await callback.message.answer_video(video_file_id, caption=f"{lesson_id}-dars: {description}")
    await callback.message.answer("Barcha darslar", reply_markup=keyboard)


@router.callback_query(F.data == "delete_lesson")
async def delete_lesson_menu(callback: CallbackQuery):
    lessons = get_all_lessons()
    if not lessons:
        await callback.message.answer("⚠️ Hech qanday dars mavjud emas.")
        return

    buttons = []
    row = []
    for i, (lesson_id, _, _) in enumerate(lessons, start=1):
        row.append(InlineKeyboardButton(text=f"{lesson_id}-dars", callback_data=f"confirm_delete:{lesson_id}"))
        if i % 4 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("🗂 O‘chirmoqchi bo‘lgan darsni tanlang:", reply_markup=kb)


@router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_and_delete(callback: CallbackQuery):
    lesson_id = int(callback.data.split(":")[1])
    delete_lesson_and_reorder(lesson_id)
    await callback.message.answer(f"❌ {lesson_id}-dars o‘chirildi. Darslar tartibi yangilandi.")

@router.callback_query(F.data.startswith("approve_payment:"))
async def approve_payment(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    update_user_pay(user_id, True)

    # foydalanuvchiga xabar
    await callback.bot.send_message(user_id, "✅ To‘lovingiz tasdiqlandi! Endi darsni boshlashingiz mumkin.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Darsni boshlash", callback_data="start_lesson")]
    ]))

    await callback.answer("Foydalanuvchiga ruxsat berildi.")

@router.callback_query(F.data == "broadcast_message")
async def ask_broadcast_message(callback: CallbackQuery, state: FSMContext):
    if str(callback.from_user.id) != os.getenv("ADMIN_ID"):
        return
    await callback.message.answer("📢 Iltimos, yubormoqchi bo‘lgan xabar/matn/faylni yuboring.")
    await state.set_state(Broadcast.waiting_for_message)


@router.message(Broadcast.waiting_for_message)
async def handle_broadcast_content(message: Message, state: FSMContext):
    from db import get_all_paid_users
    from aiogram.exceptions import TelegramBadRequest

    users = get_all_paid_users()
    sent = 0

    for user_id in users:
        try:
            if message.text:
                await message.bot.send_message(user_id, message.text)
            elif message.photo:
                await message.bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.video:
                await message.bot.send_video(user_id, message.video.file_id, caption=message.caption)
            elif message.voice:
                await message.bot.send_voice(user_id, message.voice.file_id, caption=message.caption)
            elif message.document:
                await message.bot.send_document(user_id, message.document.file_id, caption=message.caption)
            sent += 1
        except TelegramBadRequest:
            continue  # foydalanuvchi bloklagan bo'lishi mumkin

    await message.answer(f"✅ {sent} ta foydalanuvchiga xabar yuborildi.", reply_markup=keyboard)
    await state.clear()

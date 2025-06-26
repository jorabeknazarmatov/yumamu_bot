from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from db import add_or_get_user, get_lesson_by_id, get_next_lesson, update_user_lesson, record_view, get_user, is_user_paid
import os
router = Router()
    
@router.message(Command("start"))
async def user_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ro‘yxatdan o‘tish", callback_data="register")]
    ])

    text = f"""🎯 Daromadingizni 2 barobardan 5 barobargacha oshirmoqchimisiz?

Unda hoziroq pastdagi tugmani bosing va mening 1 MILLION SO‘MLIK
🧠 “Xunardan Brendgacha” kursimni atigi 97 000 so‘m evaziga qo‘lga kiriting!

⏳ DIQQAT! Taklif muddati faqat 72 soat!
Shoshiling, imkoniyatni boy bermang!

👇 Ro‘yxatdan o‘tish uchun pastdagi tugmani bosing
"""
    await message.answer(text, reply_markup=keyboard)

class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_lastname = State()
    waiting_for_phone = State()

class Payment(StatesGroup):
    waiting_for_receipt = State()


@router.callback_query(F.data == "register")
async def ask_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Ma'lumotingizni kiriting.\n\n1️⃣ Ismingizni yozing:")
    await state.set_state(Registration.waiting_for_name)

@router.message(Registration.waiting_for_name)
async def ask_lastname(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("2️⃣ Familiyangizni yozing:")
    await state.set_state(Registration.waiting_for_lastname)

@router.message(Registration.waiting_for_lastname)
async def ask_phone(message: Message, state: FSMContext):
    await state.update_data(lastname=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("3️⃣ Telefon raqamingizni yuboring:", reply_markup=keyboard)
    await state.set_state(Registration.waiting_for_phone)

@router.message(Registration.waiting_for_phone)
async def finish_registration(message: Message, state: FSMContext):
    if not message.contact:
        await message.answer("❗️ Iltimos, telefon raqamini yuborish tugmasidan foydalaning.")
        return

    data = await state.get_data()
    name = data["name"]
    lastname = data["lastname"]
    phone = message.contact.phone_number

    # DB-ga saqlash
    add_or_get_user(
        telegram_id=message.from_user.id,
        first_name=name,
        last_name=lastname,
        phone=phone,
        pay=False
    )

    await message.answer(
    "💳 To‘lov qilish uchun karta raqami: 5614 6821 1932 9110 (Uzcard: Murodova Yulduz)\nChet eldagilar uchun 4023060238783806 (Visa: Murodova Yulduz)\n\nIltimos, to‘lovni amalga oshirib, to‘lov chekini yuboring."
)
    await state.set_state(Payment.waiting_for_receipt)

@router.message(Payment.waiting_for_receipt)
async def process_receipt(message: Message, state: FSMContext):
    if not message.photo and not message.document:
        await message.delete()
        await message.answer("❗️ Iltimos, faqat to‘lov chekini (rasm yoki fayl ko‘rinishida) yuboring.")
        return

    # adminga yuborish
    admin_id = int(os.getenv("ADMIN_ID"))
    caption = f"💰 Yangi to‘lov!\n👤 {message.from_user.full_name}\n🆔 {get_user(message.from_user.id)}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ruxsat berish", callback_data=f"approve_payment:{message.from_user.id}")]
    ])

    if message.photo:
        await message.bot.send_photo(admin_id, message.photo[-1].file_id, caption=caption, reply_markup=kb)
    elif message.document:
        await message.bot.send_document(admin_id, message.document.file_id, caption=caption, reply_markup=kb)

    await message.answer("✅ Chek yuborildi. Admin tomonidan tekshiruvdan o‘tishini kuting.")
    await state.clear()



@router.callback_query(F.data == "start_lesson")
async def start_lesson(callback: CallbackQuery):
    # Bazadan foydalanuvchini olamiz (yangisini yaratmaymiz!)
    user = get_user(callback.from_user.id)

    if not user:
        await callback.message.answer("❗️ Siz hali ro‘yxatdan o‘tmagansiz. Iltimos, avval ro‘yxatdan o‘ting.")
        return

    user_id, current_lesson = user

    if not is_user_paid(callback.from_user.id):
        await callback.message.answer("❗️ Hali to‘lov qilmagansiz yoki tasdiqlanmagan.")
        return

    lesson = get_lesson_by_id(current_lesson)    
    if lesson:
        video_id, description = lesson
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Ha", callback_data="learned_yes"),
            InlineKeyboardButton(text="Yo'q", callback_data="learned_no"),
            InlineKeyboardButton(text="Endi", callback_data="learned_later")
        ]])
        await callback.message.answer_video(video_id, caption=description)
        await callback.message.answer("Darsni o'zlashtirdingizmi?", reply_markup=keyboard)
    else:
        await callback.message.answer("Siz uchun hozircha dars mavjud emas.")

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

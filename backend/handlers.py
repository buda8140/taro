
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, URLInputFile, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID, PAYMENT_OPTIONS, BOT_USERNAME
from database import db
from keyboards import (
    main_menu_keyboard, readings_submenu_keyboard, profile_submenu_keyboard,
    support_submenu_keyboard, payment_options_keyboard, cards_number_keyboard,
    reading_type_keyboard, confirmation_keyboard, referral_keyboard,
    examples_keyboard, achievements_keyboard, questions_keyboard,
    achievements_progress_keyboard, examples_category_keyboard,
    user_stats_keyboard, referral_stats_keyboard, feedback_keyboard,
    achievements_bonus_keyboard
)
from utils import (
    get_random_quote, monitor_tasks, format_tarot_response,
    parse_custom_cards, get_user_level, get_user_achievements,
    create_welcome_gif, generate_tarot_cards, get_cards_description
)
from ohmygpt_api import get_tarot_response

logger = logging.getLogger(__name__)
router = Router()

class ReadingStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_cards_count = State()
    waiting_for_custom_cards = State()
    waiting_for_reading_type = State()

class SupportStates(StatesGroup):
    waiting_for_feedback = State()

@router.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or ""
    
    # Реферальная система
    args = message.text.split()
    referral_id = None
    if len(args) > 1 and args[1].isdigit():
        referral_id = int(args[1])
        if referral_id == user_id: referral_id = None
            
    is_new = await db.add_user(user_id, username, first_name, "", referral_id)
    
    user_data = await db.get_user(user_id)
    if not user_data: return

    welcome_text = (
        f"🌙 <b>Здравствуй, {first_name}!</b>\n\n"
        "Я — Луна, твой проводник в мир Таро. ✨\n"
        "Здесь ты найдешь ответы на свои вопросы и узнаешь, что скрыто за завесой тайны.\n\n"
        f"🔮 У тебя есть <b>{user_data['requests_left']} бесплатных</b> раскладов.\n"
        "💎 И <b>1 премиум</b> расклад в подарок!\n\n"
        "Чего желает твоя душа сегодня?"
    )
    
    gif_id = create_welcome_gif()
    try:
        await message.answer_animation(gif_id, caption=welcome_text, reply_markup=await main_menu_keyboard(user_data), parse_mode='HTML')
    except:
        await message.answer(welcome_text, reply_markup=await main_menu_keyboard(user_data), parse_mode='HTML')

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    user_data = await db.get_user(callback.from_user.id)
    if user_data:
        await callback.message.edit_text(
            f"🌙 <b>Главное меню</b>\n\n"
            f"🔮 Бесплатные: {user_data['requests_left']}\n"
            f"💎 Премиум: {user_data['premium_requests']}\n\n"
            "Что мы изучим сегодня?",
            reply_markup=await main_menu_keyboard(user_data),
            parse_mode='HTML'
        )

@router.callback_query(F.data == "readings_submenu")
async def readings_submenu(callback: CallbackQuery):
    await callback.message.edit_text("🔮 <b>Выберите тип расклада:</b>", reply_markup=readings_submenu_keyboard(), parse_mode='HTML')

@router.callback_query(F.data == "new_reading")
async def new_reading_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ReadingStates.waiting_for_question)
    await state.update_data(reading_type="classic", use_premium=False)
    await callback.message.answer("✨ Напиши свой вопрос картам...", reply_markup=None)
    await callback.answer()

@router.message(ReadingStates.waiting_for_question)
async def process_question(message: Message, state: FSMContext):
    question = message.text.strip()
    if len(question) > 300:
        await message.answer("⚠️ Вопрос слишком длинный. Попробуй короче.")
        return
        
    await state.update_data(question=question)
    await message.answer("🃏 Сколько карт вытянем?", reply_markup=cards_number_keyboard())
    await state.set_state(ReadingStates.waiting_for_cards_count)

@router.callback_query(ReadingStates.waiting_for_cards_count)
async def process_cards_count(callback: CallbackQuery, state: FSMContext):
    count = int(callback.data.split("_")[1])
    await state.update_data(cards_count=count)
    
    data = await state.get_data()
    # Запускаем генерацию
    await perform_reading(callback.message, callback.from_user.id, data)
    await state.clear()
    await callback.answer()

async def perform_reading(message: Message, user_id: int, data: dict):
    # Проверка баланса
    user = await db.get_user(user_id)
    if not user: return
    
    use_premium = data.get("use_premium", False)
    
    if use_premium:
        if user['premium_requests'] <= 0:
            await message.answer("💎 Недостаточно премиум-запросов.", reply_markup=await payment_options_keyboard())
            return
    else:
        if user['requests_left'] <= 0:
             # Авто-свитч на премиум если есть
             if user['premium_requests'] > 0:
                 await message.answer("ℹ️ Бесплатные закончились, используем премиум 💎")
                 use_premium = True
             else:
                 await message.answer("😔 Запросы закончились. Приходите завтра или купите еще.", reply_markup=await payment_options_keyboard())
                 return

    await message.answer("🔮 Тасую колоду... Соединяюсь с космосом...")
    
    # Генерация карт
    cards = generate_tarot_cards(data.get("cards_count", 3))
    
    # История
    history = await db.get_history(user_id, limit=3)
    history_context = "\n".join([f"Q: {h['question']} A: {h['cards']}" for h in history])
    
    # Запрос к AI
    response = await get_tarot_response(
        question=data['question'],
        cards=cards,
        is_premium=use_premium,
        full_history=history_context,
        user_id=user_id,
        username=user['username'],
        reading_type=data.get("reading_type")
    )
    
    if not response or 'choices' not in response:
        await message.answer("⚠️ Связь с космосом прервалась. Попробуйте позже.")
        return
        
    interpretation = response['choices'][0]['message']['content']
    
    # Списание
    await db.use_request(user_id, use_premium=use_premium)
    await db.add_history(user_id, data['question'], ",".join(cards), interpretation, data.get("reading_type"), use_premium)
    
    formatted_msgs = format_tarot_response(interpretation, data['question'], cards, use_premium)
    
    for msg in formatted_msgs:
        await message.answer(msg, parse_mode='HTML')
    
    # Предложить еще
    await asyncio.sleep(1)
    await message.answer("🌙 Что дальше, путник?", reply_markup=await main_menu_keyboard(await db.get_user(user_id)))

@router.callback_query(F.data == "profile_submenu")
async def profile_menu(callback: CallbackQuery):
    await callback.message.edit_text("👤 <b>Ваш профиль</b>", reply_markup=profile_submenu_keyboard(), parse_mode='HTML')

@router.callback_query(F.data == "history")
async def history_handler(callback: CallbackQuery):
    hist = await db.get_history(callback.from_user.id, limit=5)
    if not hist:
        await callback.message.edit_text("📜 История пуста.", reply_markup=profile_submenu_keyboard())
        return
    
    text = "📜 <b>Ваша история:</b>\n\n"
    for item in hist:
        text += f"📅 {item['timestamp']}\n❓ {item['question']}\n🃏 {item['cards']}\n\n"
    
    await callback.message.edit_text(text, reply_markup=profile_submenu_keyboard(), parse_mode='HTML')

@router.callback_query(F.data == "buy_premium")
async def buy_premium_handler(callback: CallbackQuery):
    await callback.message.edit_text("💎 <b>Магазин магии</b>\n\nВыберите пакет:", reply_markup=await payment_options_keyboard(), parse_mode='HTML')

@router.callback_query(F.data.startswith("buy_")) # buy_1, buy_3...
async def process_buy(callback: CallbackQuery):
    key = callback.data
    # Use yoomoney
    from yoomoney import yoomoney_payment
    rate = PAYMENT_OPTIONS.get(key)
    if not rate: return
    
    url, label = await yoomoney_payment.generate_payment_link(callback.from_user.id, rate['price'], rate['requests'], key)
    if url:
        builder = InlineKeyboardBuilder()
        builder.button(text="💳 Оплатить", url=url)
        builder.button(text="✅ Проверить", callback_data=f"check_pay_{label}")
        builder.button(text="🔙 Отмена", callback_data="buy_premium")
        builder.adjust(1)
        await callback.message.edit_text(
            f"🔮 <b>Оплата: {rate['label']}</b>\n\n"
            f"Сумма: {rate['price']} руб.\n"
            f"Нажмите кнопку ниже для оплаты.",
            reply_markup=builder.as_markup(),
            parse_mode='HTML'
        )

@router.callback_query(F.data.startswith("check_pay_"))
async def check_payment_btn(callback: CallbackQuery):
    # Manual check handle if needed, or just tell user to wait
    await callback.answer("⏳ Проверяем платеж...", show_alert=True)
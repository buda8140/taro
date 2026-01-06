
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import PAYMENT_OPTIONS
from database import db

async def main_menu_keyboard(user_data):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f"🔮 Расклад (🆓{user_data['requests_left']} 💎{user_data['premium_requests']})", callback_data="readings_submenu")
    keyboard.button(text="👤 Профиль", callback_data="profile_submenu")
    keyboard.button(text="💎 Купить", callback_data="buy_premium")
    keyboard.adjust(1)
    return keyboard.as_markup()

def readings_submenu_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✨ Классический", callback_data="new_reading")
    keyboard.button(text="🎭 Ситуация", callback_data="situation_reading")
    keyboard.button(text="💖 Отношения", callback_data="relationship_reading")
    keyboard.button(text="🔙 Назад", callback_data="main_menu")
    keyboard.adjust(1)
    return keyboard.as_markup()

def profile_submenu_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📜 История", callback_data="history")
    keyboard.button(text="🏆 Достижения", callback_data="achievements")
    keyboard.button(text="🔙 Назад", callback_data="main_menu")
    keyboard.adjust(1)
    return keyboard.as_markup()

def support_submenu_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💌 Отзыв", callback_data="feedback")
    keyboard.button(text="🔙 Назад", callback_data="main_menu")
    keyboard.adjust(1)
    return keyboard.as_markup()

async def payment_options_keyboard():
    keyboard = InlineKeyboardBuilder()
    rates = await db.get_all_rates()
    if rates:
        for rate in rates:
            keyboard.button(text=rate.get("label", f"{rate['requests']} з."), callback_data=rate["package_key"])
    else:
        for key, opt in PAYMENT_OPTIONS.items():
            keyboard.button(text=opt["label"], callback_data=key)
    keyboard.button(text="🔙 Назад", callback_data="main_menu")
    keyboard.adjust(1)
    return keyboard.as_markup()

def cards_number_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="1 карта", callback_data="cards_1")
    keyboard.button(text="3 карты", callback_data="cards_3")
    keyboard.button(text="5 карт", callback_data="cards_5")
    keyboard.button(text="🔙 Назад", callback_data="readings_submenu")
    keyboard.adjust(1)
    return keyboard.as_markup()

def reading_type_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🎯 Чёткий вопрос", callback_data="type_specific")
    keyboard.button(text="🔙 Назад", callback_data="readings_submenu")
    keyboard.adjust(1)
    return keyboard.as_markup()

def history_pagination_keyboard(page, total_pages):
    keyboard = InlineKeyboardBuilder()
    if page > 0: keyboard.button(text="⬅️", callback_data=f"history_prev_{page}")
    keyboard.button(text=f"{page+1}/{total_pages}", callback_data="noop")
    if page < total_pages - 1: keyboard.button(text="➡️", callback_data=f"history_next_{page}")
    keyboard.button(text="🔙", callback_data="profile_submenu")
    keyboard.adjust(3, 1)
    return keyboard.as_markup()

def confirmation_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Да", callback_data="confirm_yes")
    keyboard.button(text="❌ Нет", callback_data="confirm_no")
    keyboard.adjust(2)
    return keyboard.as_markup()

def referral_keyboard(link):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📤 Поделиться", url=f"https://t.me/share/url?url={link}")
    keyboard.button(text="🔙 Назад", callback_data="profile_submenu")
    keyboard.adjust(1)
    return keyboard.as_markup()

def examples_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="main_menu")
    keyboard.adjust(1)
    return keyboard.as_markup()

def achievements_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="profile_submenu")
    keyboard.adjust(1)
    return keyboard.as_markup()

def pending_payment_keyboard(payment_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅", callback_data=f"confirm_payment_{payment_id}")
    keyboard.button(text="❌", callback_data=f"reject_payment_{payment_id}")
    keyboard.adjust(2)
    return keyboard.as_markup()

def broadcast_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📤 Отправить", callback_data="confirm_broadcast")
    keyboard.adjust(1)
    return keyboard.as_markup()

def admin_panel_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 Статистика", callback_data="admin_stats")
    keyboard.button(text="💸 Платежи", callback_data="admin_pending_payments")
    keyboard.adjust(1)
    return keyboard.as_markup()

def achievements_progress_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="achievements")
    keyboard.adjust(1)
    return keyboard.as_markup()

def examples_category_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="examples")
    keyboard.adjust(1)
    return keyboard.as_markup()

def user_stats_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="profile_submenu")
    keyboard.adjust(1)
    return keyboard.as_markup()

def referral_stats_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="referral")
    keyboard.adjust(1)
    return keyboard.as_markup()

def feedback_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="support_submenu")
    keyboard.adjust(1)
    return keyboard.as_markup()

def achievements_bonus_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Back", callback_data="achievements")
    return keyboard.as_markup()
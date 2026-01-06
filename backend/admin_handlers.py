
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_ID
from database import db
from keyboards import admin_panel_keyboard

router = Router()

@router.message(Command("admin"))
async def admin_start(message: Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("🔧 Админ панель", reply_markup=admin_panel_keyboard())

@router.callback_query(F.data == "admin_stats")
async def admin_stats_show(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    users = await db.get_all_users()
    await callback.message.edit_text(f"👥 Пользователей: {len(users)}", reply_markup=admin_panel_keyboard())
    
@router.callback_query(F.data == "admin_pending_payments")
async def admin_pending(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    # Simplified
    await callback.message.edit_text("Список платежей...", reply_markup=admin_panel_keyboard())
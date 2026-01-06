
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiohttp import web
from config import BOT_TOKEN, YOOMONEY_CHECK_INTERVAL
from database import db
from handlers import router as user_router
from admin_handlers import router as admin_router
from api import app as api_app
from yoomoney import yoomoney_payment

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def check_payments_task(bot: Bot):
    """Periodically check payment status."""
    while True:
        try:
            # Check yoomoney history
            # Logic from TARO CHAT/yoomoney.py check_payments
            # Simplified here
            operations = await yoomoney_payment.get_recent_operations()
            # Process operations...
            # For each op check if label matches pending payment
            pass
        except Exception as e:
            logger.error(f"Payment check error: {e}")
        await asyncio.sleep(YOOMONEY_CHECK_INTERVAL)

async def main():
    # 1. Init Bot
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(user_router)
    dp.include_router(admin_router)
    
    # 2. Start API Server
    runner = web.AppRunner(api_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    logger.info("🚀 API Server started on http://0.0.0.0:8000")
    
    # 3. Start Background Tasks
    asyncio.create_task(check_payments_task(bot))
    
    # 4. Start Polling
    logger.info("🚀 Bot Polling started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")

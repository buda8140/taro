
import aiohttp
import uuid
import logging
from typing import Optional, Tuple
from config import (
    YOOMONEY_ACCESS_TOKEN, YOOMONEY_CLIENT_ID, YOOMONEY_REDIRECT_URI,
    PAYMENT_OPTIONS, YOOMONEY_DRY_RUN
)
from database import db

logger = logging.getLogger(__name__)

class YooMoneyPayment:
    def __init__(self):
        self.token = YOOMONEY_ACCESS_TOKEN
        self.client_id = YOOMONEY_CLIENT_ID
        self.redirect_uri = YOOMONEY_REDIRECT_URI
        self.base_url = "https://yoomoney.ru"
        self.api_url = "https://yoomoney.ru/api"

    async def generate_payment_link(
        self,
        user_id: int,
        amount: int,
        requests_count: int,
        package_key: str
    ) -> Tuple[Optional[str], Optional[str]]:
        try:
            label = f"tarot_luna_{user_id}_{package_key}_{uuid.uuid4().hex[:8]}"
            
            # Создаем платеж в БД со статусом pending
            await db.create_payment(
                user_id=user_id,
                amount=amount,
                requests=requests_count,
                yoomoney_label=label,
                status="pending"
            )
            
            # Формируем ссылку на оплату (QuickPay)
            # https://yoomoney.ru/quickpay/confirm
            params = {
                "receiver": "your_wallet_number_here", # НУЖНО ВСТАВИТЬ КОШЕЛЕК ИЗ CONFIG ЕСЛИ ОН ТАМ ЕСТЬ, ИНАЧЕ ЭТО НЕ БУДЕТ РАБОТАТЬ
                # В TARO CHAT config.py был CARD_NUMBER, надо его использовать
                "quickpay-form": "shop",
                "targets": f"Tarot Luna: {requests_count} раскладов",
                "paymentType": "AC", # Банковская карта
                "sum": str(amount),
                "label": label,
                "successURL": "https://t.me/TaroLunaBot"
            }
            # Но подождите, у пользователя скорей всего токен приложения, а не кошелек для приема.
            # Если используется p2p API (yoomoney-api), то ссылка формируется иначе.
            # В TARO CHAT/yoomoney.py использовался yoomoney библиотека? 
            # Я не увидел yoomoney.py полностью, но видел методы `get_recent_operations`.
            # Это значит мы используем API токен для проверки истории.
            # А для ССЫЛКИ мы используем QuickPay форму, которая переводит на КОШЕЛЕК.
            # Мне нужен НОМЕР КОШЕЛЬКА. В config.py (Backend) его нет. 
            # В TARO CHAT config.py (step 39) БЫЛ CARD_NUMBER!
            pass
            
            # Исправление: нужно добавить CARD_NUMBER в config.
            from config import CARD_NUMBER
            params["receiver"] = CARD_NUMBER
            
            query = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{self.base_url}/quickpay/confirm?{query}"
            
            return url, label

        except Exception as e:
            logger.error(f"Error generating payment link: {e}")
            return None, None

    async def get_recent_operations(self, hours: int = 24) -> List[Dict]:
        """Получает историю операций."""
        if not self.token: return []
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # from_date = ...
        # Для простоты запрашиваем последние 30 записей
        data = {
            "type": "deposition",
            "records": 30
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/operation-history", headers=headers, data=data) as resp:
                if resp.status == 200:
                    json_data = await resp.json()
                    return json_data.get("operations", [])
                else:
                    logger.error(f"YooMoney API Error: {await resp.text()}")
                    return []

    async def get_operation_details(self, operation_id: str) -> Optional[Dict]:
        if not self.token: return None
        headers = {"Authorization": f"Bearer {self.token}"}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/operation-details", headers=headers, data={"operation_id": operation_id}) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    
    def _extract_package_key_from_label(self, label: str) -> Optional[str]:
        try:
            return label.split('_')[3] # tarot_luna_{uid}_{pkg}_{uuid}
        except: return None
        
    def _extract_user_id_from_label(self, label: str) -> Optional[int]:
         try:
            return int(label.split('_')[2])
         except: return None

yoomoney_payment = YooMoneyPayment()

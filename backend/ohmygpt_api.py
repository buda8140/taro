
import httpx
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from config import OHMYGPT_API_KEY, OHMYGPT_API_URL, OHMYGPT_MODEL, OHMYGPT_FALLBACK_MODELS
from utils import get_cards_description

logger = logging.getLogger(__name__)

class OhMyGPTAPI:
    def __init__(self):
        self.api_key = OHMYGPT_API_KEY
        self.base_url = OHMYGPT_API_URL
        self.default_model = OHMYGPT_MODEL
        self.fallback_models = OHMYGPT_FALLBACK_MODELS
        
    async def get_tarot_response(
        self,
        question: str,
        cards: List[str],
        is_premium: bool,
        full_history: str,
        user_id: int,
        username: str,
        reading_type: str = None
    ) -> Optional[Dict[str, Any]]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Упрощенные промпты для сокращения
        system_prompt = "Ты — Мастер Таро 'Луна'. Ты помогаешь людям найти ответы."
        user_prompt = f"Вопрос: {question}\nКарты: {', '.join(cards)}\nТип: {reading_type}\nИсторя: {full_history}"
        
        data = {
            "model": self.default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.9,
            "max_tokens": 2000 if is_premium else 1000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(self.base_url, headers=headers, json=data)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"API Error: {response.status_code} {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Exception requesting AI: {e}")
                return None

ohmygpt_api = OhMyGPTAPI()

async def get_tarot_response(*args, **kwargs):
    return await ohmygpt_api.get_tarot_response(*args, **kwargs)
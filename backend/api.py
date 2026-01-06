
import logging
import json
import uuid
from aiohttp import web
from config import BOT_TOKEN, ADMIN_ID, PAYMENT_OPTIONS
from database import db

logger = logging.getLogger(__name__)

def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-User-Id'
    }

@web.middleware
async def cors_middleware(request, handler):
    if request.method == 'OPTIONS':
        return web.Response(headers=cors_headers())
    res = await handler(request)
    for k, v in cors_headers().items():
        res.headers[k] = v
    return res

async def handle_auth(request):
    try:
        data = await request.json()
        init_data = data.get('initData')
        # В реальном проде можно валидировать initData
        # Для простоты берем user_id из заголовка или 'user' объекта
        # Но фронтенд шлет initData. 
        # Допустим, мы верим, или лучше распарсим, 
        # но для MVP просто вернем успех если есть ID.
        pass
    except: pass
    
    # Для MVP просто мок авторизации по X-User-Id для разработки
    user_id_hdr = request.headers.get("X-User-Id")
    if not user_id_hdr:
        # Пытаемся достать из body
        try:
           body = await request.json()
           # Тут логика парсинга initData, упростим
        except: pass
        return web.json_response({"success": False}, status=401)
        
    user_id = int(user_id_hdr)
    user = await db.get_user_with_stats(user_id)
    if not user:
        # Auto-register logic if needed or return 404
        # Лучше 404
        pass

    if user:
         return web.json_response({"success": True, "user": user})
    return web.json_response({"success": True, "user": {"id": user_id, "requests_left": 3, "premium_requests": 1}}) # Fallback

async def handle_user_get(request):
    uid = request.headers.get("X-User-Id")
    if not uid: return web.json_response({"error": "No User ID"}, status=401)
    user = await db.get_user_with_stats(int(uid))
    return web.json_response({"success": True, "user": user})

async def handle_payment_create(request):
    uid = request.headers.get("X-User-Id")
    if not uid: return web.json_response({"error": "Auth req"}, status=401)
    data = await request.json()
    pkg_key = data.get("package_key")
    
    from yoomoney import yoomoney_payment
    opt = PAYMENT_OPTIONS.get(pkg_key)
    if not opt: return web.json_response({"error": "Invalid package"}, status=400)
    
    url, label = await yoomoney_payment.generate_payment_link(int(uid), opt['price'], opt['requests'], pkg_key)
    return web.json_response({
        "success": True, 
        "payment": {
            "url": url, 
            "label": label, 
            "amount": opt['price'], 
            "requests": opt['requests']
        }
    })

async def handle_history(request):
    uid = request.headers.get("X-User-Id")
    if not uid: return web.json_response({"error": "Auth req"}, status=401)
    page = int(request.query.get("page", 0))
    limit = int(request.query.get("limit", 10))
    hist = await db.get_history(int(uid), limit, page * limit)
    total = await db.get_total_history_count(int(uid))
    return web.json_response({
        "success": True,
        "history": hist,
        "pagination": {"page": page, "total": total, "total_pages": (total + limit - 1) // limit}
    })

async def handle_reading(request):
    uid = request.headers.get("X-User-Id")
    if not uid: return web.json_response({"error": "Auth req"}, status=401)
    uid = int(uid)
    data = await request.json()
    question = data.get("question")
    use_premium = data.get("use_premium", False)
    
    success = await db.use_request(uid, use_premium=use_premium)
    if not success:
         return web.json_response({"success": False, "error": "no_requests"}, status=402)
    
    # Generate cards
    from utils import generate_tarot_cards
    cards = generate_tarot_cards(3)
    
    # AI response
    from ohmygpt_api import get_tarot_response
    user = await db.get_user(uid)
    resp = await get_tarot_response(question, cards, use_premium, "", uid, user['username'] if user else "User")
    
    content = ""
    if resp and 'choices' in resp:
        content = resp['choices'][0]['message']['content']
        
    await db.add_history(uid, question, ",".join(cards), content, "classic", use_premium)
    
    return web.json_response({
        "success": True,
        "reading": {
            "cards": cards,
            "interpretation": content,
            "is_premium": use_premium
        }
    })

app = web.Application(middlewares=[cors_middleware])
app.router.add_post('/api/auth', handle_auth)
app.router.add_get('/api/user', handle_user_get)
app.router.add_post('/api/payment/create', handle_payment_create)
app.router.add_get('/api/history', handle_history)
app.router.add_post('/api/reading', handle_reading)

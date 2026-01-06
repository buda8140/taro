
try:
    import aiogram
    import aiohttp
    import asyncpg
    import sqlalchemy
    import logger
    import config
    import database
    import utils
    import ohmygpt_api
    import keyboards
    import yoomoney
    import handlers
    import admin_handlers
    import api
    import main
    print("Imports successful")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")

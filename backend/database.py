"""
database.py
Обновленная версия с поддержкой системы достижений и уровней.
"""

import sqlite3
import logging
from datetime import datetime
from pytz import timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import DB_PATH, TIMEZONE

logger = logging.getLogger(__name__)

class Database:
    def __init__(self) -> None:
        """
        Инициализация базы данных SQLite.
        """
        self.db_path: Path = Path(DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
    
    def init_db(self) -> None:
        """
        Инициализация структуры базы данных.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица пользователей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        requests_left INTEGER DEFAULT 3,
                        premium_requests INTEGER DEFAULT 1,
                        referral_id INTEGER,
                        referrals_count INTEGER DEFAULT 0,
                        last_free_request_time TEXT,
                        is_banned BOOLEAN DEFAULT FALSE,
                        ban_expires TEXT,
                        forbidden_attempts INTEGER DEFAULT 0,
                        agreed_rules BOOLEAN DEFAULT FALSE,
                        last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Таблица истории
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        question TEXT,
                        cards TEXT,
                        response TEXT,
                        reading_type TEXT DEFAULT 'classic',
                        is_premium BOOLEAN DEFAULT FALSE,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Таблица платежей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        amount INTEGER,
                        requests INTEGER,
                        status TEXT DEFAULT 'pending',
                        screenshot_id TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        yoomoney_label TEXT,
                        admin_id INTEGER,
                        yoomoney_operation_id TEXT,
                        amount_received REAL,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Таблица отзывов
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        feedback TEXT,
                        rating INTEGER DEFAULT 5,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Таблица реферальных начислений
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS referral_rewards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        referrer_id INTEGER,
                        referred_id INTEGER,
                        reward_type TEXT,
                        amount INTEGER,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                        FOREIGN KEY (referred_id) REFERENCES users(user_id)
                    )
                """)
                
                # Таблица достижений пользователей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_achievements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        achievement_name TEXT,
                        achievement_emoji TEXT,
                        description TEXT,
                        unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        UNIQUE(user_id, achievement_name)
                    )
                """)
                
                # Таблица уровней пользователей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_levels (
                        user_id INTEGER PRIMARY KEY,
                        level INTEGER DEFAULT 1,
                        experience INTEGER DEFAULT 0,
                        total_readings INTEGER DEFAULT 0,
                        premium_readings INTEGER DEFAULT 0,
                        referrals_count INTEGER DEFAULT 0,
                        last_level_up TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Таблица активности пользователей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        activity_type TEXT,
                        details TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Таблица статистики пользователей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_stats (
                        user_id INTEGER PRIMARY KEY,
                        total_readings INTEGER DEFAULT 0,
                        total_cards INTEGER DEFAULT 0,
                        total_words INTEGER DEFAULT 0,
                        favorite_reading_type TEXT,
                        most_used_cards TEXT,
                        reading_days_active INTEGER DEFAULT 0,
                        last_7_days_active INTEGER DEFAULT 0,
                        streak_days INTEGER DEFAULT 0,
                        last_streak_date TEXT,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Индексы для оптимизации запросов
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_user_id ON history(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_reading_type ON history(reading_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_referral_id ON users(referral_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id)")
                
                # Таблица тарифов
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rates (
                        package_key TEXT PRIMARY KEY,
                        requests INTEGER NOT NULL,
                        price INTEGER NOT NULL,
                        label TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Инициализация тарифов из config.PAYMENT_OPTIONS, если таблица пуста
                cursor.execute("SELECT COUNT(*) FROM rates")
                if cursor.fetchone()[0] == 0:
                    from config import PAYMENT_OPTIONS
                    for package_key, package_data in PAYMENT_OPTIONS.items():
                        cursor.execute("""
                            INSERT INTO rates (package_key, requests, price, label)
                            VALUES (?, ?, ?, ?)
                        """, (
                            package_key,
                            package_data["requests"],
                            package_data["price"],
                            package_data.get("label", f"{package_data['requests']} запросов ({package_data['price']} руб.)")
                        ))
                    logger.info("🔮 Initialized rates table with default values")

                from config import PAYMENT_OPTIONS
                for package_key, package_data in PAYMENT_OPTIONS.items():
                    cursor.execute(
                        "INSERT OR IGNORE INTO rates (package_key, requests, price, label) VALUES (?, ?, ?, ?)",
                        (
                            package_key,
                            package_data["requests"],
                            package_data["price"],
                            package_data.get("label", f"{package_data['requests']} запросов ({package_data['price']} руб.)")
                        )
                    )
                
                # Миграция
                try:
                    cursor.execute("ALTER TABLE payments ADD COLUMN yoomoney_label TEXT")
                except sqlite3.OperationalError:
                    pass
                
                try:
                    cursor.execute("ALTER TABLE payments ADD COLUMN admin_id INTEGER")
                except sqlite3.OperationalError:
                    pass

                try:
                    cursor.execute("ALTER TABLE payments ADD COLUMN yoomoney_operation_id TEXT")
                except sqlite3.OperationalError:
                    pass

                try:
                    cursor.execute("ALTER TABLE payments ADD COLUMN amount_received REAL")
                except sqlite3.OperationalError:
                    pass
                
                # Уникальный индекс для yoomoney_label
                try:
                    cursor.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_payments_yoomoney_label 
                        ON payments(yoomoney_label) 
                        WHERE yoomoney_label IS NOT NULL
                    """)
                except sqlite3.OperationalError:
                    try:
                        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_yoomoney_label ON payments(yoomoney_label)")
                    except sqlite3.OperationalError:
                        pass
                
                conn.commit()
                logger.info("🔮 Database initialized successfully with achievements support")
                
        except sqlite3.Error as e:
            logger.error(f"⚠️ Error initializing database: {e}")
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)

    async def add_user(
        self,
        user_id: int,
        username: str,
        first_name: str,
        last_name: str,
        referral_id: Optional[int] = None
    ) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
                if cursor.fetchone():
                    return False
                
                if referral_id:
                    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (referral_id,))
                    if not cursor.fetchone():
                        referral_id = None
                
                cursor.execute(
                    """
                    INSERT INTO users 
                    (user_id, username, first_name, last_name, referral_id, requests_left, premium_requests) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, username, first_name, last_name, referral_id, 3, 1)
                )
                
                cursor.execute("INSERT INTO user_stats (user_id) VALUES (?)", (user_id,))
                cursor.execute("INSERT INTO user_levels (user_id) VALUES (?)", (user_id,))
                
                if referral_id:
                    cursor.execute("UPDATE users SET requests_left = requests_left + 1 WHERE user_id = ?", (referral_id,))
                    cursor.execute("UPDATE users SET referrals_count = referrals_count + 1 WHERE user_id = ?", (referral_id,))
                    cursor.execute("UPDATE user_levels SET referrals_count = referrals_count + 1 WHERE user_id = ?", (referral_id,))
                    cursor.execute(
                        "INSERT INTO referral_rewards (referrer_id, referred_id, reward_type, amount) VALUES (?, ?, ?, ?)",
                        (referral_id, user_id, 'free_request', 1)
                    )
                    
                    cursor.execute("SELECT referrals_count FROM users WHERE user_id = ?", (referral_id,))
                    ref_count = cursor.fetchone()[0] or 0
                    if ref_count == 1:
                        cursor.execute(
                            "INSERT INTO user_achievements (user_id, achievement_name, achievement_emoji, description) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, achievement_name) DO NOTHING",
                            (referral_id, "Наставник", "🤝", "Пригласил первого друга")
                        )
                
                cursor.execute(
                    "INSERT INTO user_achievements (user_id, achievement_name, achievement_emoji, description) VALUES (?, ?, ?, ?)",
                    (user_id, "Новичок", "🌱", "Сделал первый шаг в мир Таро")
                )
                
                cursor.execute(
                    "INSERT INTO user_activity (user_id, activity_type, details) VALUES (?, ?, ?)",
                    (user_id, "registration", f"Регистрация через реферала {referral_id if referral_id else 'нет'}")
                )
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"⚠️ Error adding user: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"⚠️ Error getting user {user_id}: {e}")
            return None
    
    async def get_user_with_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user_data = cursor.fetchone()
                if not user_data: return None
                result = dict(user_data)
                
                cursor.execute("SELECT * FROM user_stats WHERE user_id = ?", (user_id,))
                stats_data = cursor.fetchone()
                if stats_data: result.update(dict(stats_data))
                
                cursor.execute("SELECT * FROM user_levels WHERE user_id = ?", (user_id,))
                level_data = cursor.fetchone()
                if level_data: result.update(dict(level_data))
                
                return result
        except sqlite3.Error as e:
            logger.error(f"⚠️ Error getting user with stats {user_id}: {e}")
            return None
    
    async def update_user_requests(self, user_id: int, free_requests: int = 0, premium_requests: int = 0) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if free_requests != 0:
                    cursor.execute("UPDATE users SET requests_left = requests_left + ? WHERE user_id = ?", (free_requests, user_id))
                if premium_requests != 0:
                    cursor.execute("UPDATE users SET premium_requests = premium_requests + ? WHERE user_id = ?", (premium_requests, user_id))
                cursor.execute("UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"⚠️ Error updating requests for user {user_id}: {e}")
            return False
    
    async def use_request(self, user_id: int, use_premium: bool = False) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT requests_left, premium_requests FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                if not result: return False
                free, premium = result
                
                actual_use_premium = use_premium
                log_type = "free"
                
                if not use_premium and free <= 0 and premium > 0:
                    actual_use_premium = True
                
                if actual_use_premium:
                    if premium <= 0: return False
                    cursor.execute("UPDATE users SET premium_requests = premium_requests - 1 WHERE user_id = ?", (user_id,))
                    log_type = "premium"
                else:
                    if free <= 0: return False
                    cursor.execute("UPDATE users SET requests_left = requests_left - 1 WHERE user_id = ?", (user_id,))
                
                cursor.execute("UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
                try:
                    cursor.execute("INSERT INTO user_activity (user_id, activity_type, details) VALUES (?, ?, ?)", (user_id, f"{log_type}_reading", f"Used {log_type} request"))
                except: pass
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"⚠️ Error using request for user {user_id}: {e}")
            return False

    async def add_history(self, user_id: int, question: str, cards: str, response: str, reading_type: str = "classic", is_premium: bool = False) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO history (user_id, question, cards, response, reading_type, is_premium) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, question, cards, response, reading_type, is_premium)
                )
                
                card_count = len(cards.split(',')) if cards else 0
                word_count = len(response.split())
                
                cursor.execute(
                    """
                    UPDATE user_stats 
                    SET total_readings = total_readings + 1, total_cards = total_cards + ?, total_words = total_words + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (card_count, word_count, user_id)
                )
                
                cursor.execute(
                    """
                    UPDATE user_levels 
                    SET total_readings = total_readings + 1, experience = experience + ?, premium_readings = premium_readings + ?
                    WHERE user_id = ?
                    """,
                    (10 if is_premium else 5, 1 if is_premium else 0, user_id)
                )
                
                # Check achievements logic here (implied)
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"⚠️ Error adding history for user {user_id}: {e}")
            return False

    async def get_history(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (user_id, limit, offset)
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"⚠️ Error getting history for user {user_id}: {e}")
            return []

    async def get_total_history_count(self, user_id: int) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM history WHERE user_id = ?", (user_id,))
                return cursor.fetchone()[0] or 0
        except sqlite3.Error as e:
            logger.error(f"⚠️ Error getting history count for {user_id}: {e}")
            return 0
            
    async def increment_forbidden_attempts(self, user_id: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET forbidden_attempts = forbidden_attempts + 1 WHERE user_id = ?", (user_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error incrementing forbidden attempts: {e}")
            return False

    async def create_payment(self, user_id: int, amount: int, requests: int, yoomoney_label: str, status: str = "pending") -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO payments (user_id, amount, requests, status, yoomoney_label) VALUES (?, ?, ?, ?, ?)",
                    (user_id, amount, requests, status, yoomoney_label)
                )
                payment_id = cursor.lastrowid
                conn.commit()
                return payment_id
        except sqlite3.Error as e:
            logger.error(f"Error creating payment: {e}")
            return 0

    async def get_pending_payments(self) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM payments WHERE status = 'pending'")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting pending payments: {e}")
            return []

    async def confirm_payment(self, payment_id: int, status: str = "confirmed", requests: Optional[int] = None) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Получаем информацию о платеже
                cursor.execute("SELECT user_id, requests, status FROM payments WHERE id = ?", (payment_id,))
                payment = cursor.fetchone()
                
                if not payment:
                    return False
                
                user_id, payment_requests, current_status = payment
                
                if current_status == 'confirmed':
                    return True
                
                actual_requests = requests if requests is not None else payment_requests
                
                # Обновляем статус платежа
                cursor.execute("UPDATE payments SET status = ?, requests = ? WHERE id = ?", (status, actual_requests, payment_id))
                
                # Начисляем запросы пользователю
                if status == "confirmed":
                    cursor.execute(
                        "UPDATE users SET premium_requests = premium_requests + ? WHERE user_id = ?",
                        (actual_requests, user_id)
                    )
                    cursor.execute(
                         "INSERT INTO user_activity (user_id, activity_type, details) VALUES (?, ?, ?)",
                        (user_id, "payment_confirmed", f"Payment {payment_id} confirmed, +{actual_requests} requests")
                    )
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error confirming payment {payment_id}: {e}")
            return False

    async def get_all_users(self) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
            
    async def get_active_users(self, days: int = 7) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE last_activity >= datetime('now', ?)", (f'-{days} days',))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    async def add_free_requests_to_all(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Только тем у кого < 3
                cursor.execute(
                    "UPDATE users SET requests_left = requests_left + 1 WHERE requests_left < 3"
                )
                affected = cursor.rowcount
                conn.commit()
                return affected, affected
        except sqlite3.Error:
            return 0, 0

    async def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
         try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                stats = {}
                cursor.execute("SELECT COUNT(*) FROM history WHERE user_id = ?", (user_id,))
                stats["total_readings"] = cursor.fetchone()[0] or 0
                cursor.execute("SELECT COUNT(*) FROM history WHERE user_id = ? AND is_premium = TRUE", (user_id,))
                stats["premium_readings"] = cursor.fetchone()[0] or 0
                stats["level"] = await self.get_user_level(user_id)
                stats["achievements"] = await self.get_user_achievements(user_id)
                stats["achievements_count"] = len(stats["achievements"])
                return stats
         except:
             return {}

    async def get_user_level(self, user_id: int) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM history WHERE user_id = ?", (user_id,))
                history_count = cursor.fetchone()[0] or 0
                return min(history_count // 5 + 1, 10)
        except:
            return 1
            
    async def get_user_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM user_achievements WHERE user_id = ?", (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []
            
    async def get_all_rates(self) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM rates")
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []

    async def get_user_payments(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM payments WHERE user_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?", (user_id, limit, offset))
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []

    async def cleanup_old_pending(self, days=7):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM payments WHERE status = 'pending' AND timestamp < datetime('now', ?)", (f'-{days} days',))
                count = cursor.rowcount
                conn.commit()
                return count
        except:
            return 0
            
    async def ban_user(self, user_id: int, is_banned: bool, ban_expires: str = None) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET is_banned = ?, ban_expires = ? WHERE user_id = ?", (is_banned, ban_expires, user_id))
                conn.commit()
                return True
        except:
            return False

db = Database()
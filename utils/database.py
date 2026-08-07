import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class Database:
    def __init__(self):
        self.db_path = 'data/bot.db'
        os.makedirs('data', exist_ok=True)
        
    async def initialize(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    is_premium BOOLEAN DEFAULT FALSE,
                    premium_expiry DATETIME,
                    total_streams INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_active DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Premium codes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS premium_codes (
                    code TEXT PRIMARY KEY,
                    duration_days INTEGER DEFAULT 30,
                    is_used BOOLEAN DEFAULT FALSE,
                    used_by INTEGER,
                    used_at DATETIME,
                    created_by INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Streams history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS streams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    song_title TEXT,
                    song_url TEXT,
                    duration INTEGER,
                    quality TEXT,
                    streamed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Playlists table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    songs TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Custom stickers
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_stickers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    sticker_id TEXT,
                    sticker_name TEXT,
                    category TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY,
                    default_quality TEXT DEFAULT '192',
                    autoplay BOOLEAN DEFAULT TRUE,
                    show_lyrics BOOLEAN DEFAULT FALSE,
                    language TEXT DEFAULT 'en',
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            
    async def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Add or update user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_active)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name))
            conn.commit()
    
    async def is_premium(self, user_id: int) -> bool:
        """Check if user is premium"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT is_premium, premium_expiry FROM users WHERE user_id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result and result[0]:
                if result[1]:
                    expiry = datetime.fromisoformat(result[1])
                    if expiry > datetime.now():
                        return True
                    else:
                        # Premium expired
                        cursor.execute(
                            'UPDATE users SET is_premium = FALSE WHERE user_id = ?',
                            (user_id,)
                        )
                        conn.commit()
            return False
    
    async def set_premium(self, user_id: int, days: int = 30):
        """Activate premium for user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            expiry = datetime.now() + timedelta(days=days)
            cursor.execute('''
                UPDATE users 
                SET is_premium = TRUE, premium_expiry = ?
                WHERE user_id = ?
            ''', (expiry.isoformat(), user_id))
            conn.commit()
    
    async def get_premium_expiry(self, user_id: int) -> str:
        """Get premium expiry date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT premium_expiry FROM users WHERE user_id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result and result[0] else "N/A"
    
    async def redeem_premium_code(self, user_id: int, code: str) -> bool:
        """Redeem a premium code"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT is_used, duration_days FROM premium_codes WHERE code = ?',
                (code,)
            )
            result = cursor.fetchone()
            
            if result and not result[0]:
                # Code is valid and unused
                days = result[1]
                cursor.execute('''
                    UPDATE premium_codes 
                    SET is_used = TRUE, used_by = ?, used_at = CURRENT_TIMESTAMP
                    WHERE code = ?
                ''', (user_id, code))
                
                await self.set_premium(user_id, days)
                conn.commit()
                return True
            return False
    
    async def create_premium_code(self, code: str, days: int, creator_id: int) -> bool:
        """Create new premium code"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO premium_codes (code, duration_days, created_by)
                    VALUES (?, ?, ?)
                ''', (code, days, creator_id))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    async def log_stream(self, user_id: int, song_title: str, song_url: str = None, 
                        duration: int = 0, quality: str = "192"):
        """Log a stream"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO streams (user_id, song_title, song_url, duration, quality)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, song_title, song_url, duration, quality))
            
            cursor.execute('''
                UPDATE users 
                SET total_streams = total_streams + 1, last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute(
                'SELECT total_streams, is_premium, created_at FROM users WHERE user_id = ?',
                (user_id,)
            )
            user_data = cursor.fetchone()
            
            if not user_data:
                return {}
            
            # Top songs
            cursor.execute('''
                SELECT song_title, COUNT(*) as play_count
                FROM streams
                WHERE user_id = ?
                GROUP BY song_title
                ORDER BY play_count DESC
                LIMIT 5
            ''', (user_id,))
            top_songs = cursor.fetchall()
            
            # Total listening time
            cursor.execute(
                'SELECT SUM(duration) FROM streams WHERE user_id = ?',
                (user_id,)
            )
            total_duration = cursor.fetchone()[0] or 0
            
            stats = {
                'total_streams': user_data[0],
                'is_premium': user_data[1],
                'created_at': user_data[2],
                'top_songs': "\n".join([f"{i+1}. {song[0]} ({song[1]}x)" 
                                      for i, song in enumerate(top_songs)]),
                'total_duration': f"{total_duration // 60} minutes"
            }
            
            return stats
    
    async def get_total_users(self) -> int:
        """Get total users count"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            return cursor.fetchone()[0]
    
    async def get_premium_users_count(self) -> int:
        """Get premium users count"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM users WHERE is_premium = TRUE AND premium_expiry > ?',
                (datetime.now().isoformat(),)
            )
            return cursor.fetchone()[0]

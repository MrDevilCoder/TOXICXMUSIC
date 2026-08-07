#!/usr/bin/env python3
"""
Database handler for Music Bot
Fixed for async operations
"""

import aiosqlite
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

class Database:
    """Async database handler"""
    
    def __init__(self, db_path: str = "data/bot.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_premium BOOLEAN DEFAULT FALSE,
                    premium_expiry DATETIME,
                    total_streams INTEGER DEFAULT 0,
                    total_time INTEGER DEFAULT 0,
                    language TEXT DEFAULT 'en',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_active DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Premium codes
            await db.execute('''
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
            await db.execute('''
                CREATE TABLE IF NOT EXISTS streams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    song_title TEXT,
                    song_url TEXT,
                    duration INTEGER,
                    quality TEXT DEFAULT '192',
                    streamed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Settings
            await db.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY,
                    default_quality TEXT DEFAULT '192',
                    autoplay BOOLEAN DEFAULT TRUE,
                    show_lyrics BOOLEAN DEFAULT FALSE,
                    effects_enabled BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            await db.commit()
    
    async def add_user(self, user_id: int, username: str = None, 
                      first_name: str = None, last_name: str = None):
        """Add or update user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, last_active)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name, last_name))
            await db.commit()
    
    async def is_premium(self, user_id: int) -> bool:
        """Check if user is premium"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT is_premium, premium_expiry FROM users WHERE user_id = ?',
                (user_id,)
            )
            result = await cursor.fetchone()
            
            if result and result[0]:
                if result[1]:
                    expiry = datetime.fromisoformat(result[1])
                    if expiry > datetime.now():
                        return True
                    else:
                        # Premium expired
                        await db.execute(
                            'UPDATE users SET is_premium = FALSE WHERE user_id = ?',
                            (user_id,)
                        )
                        await db.commit()
            return False
    
    async def set_premium(self, user_id: int, days: int = 30):
        """Set user as premium"""
        async with aiosqlite.connect(self.db_path) as db:
            expiry = datetime.now() + timedelta(days=days)
            await db.execute('''
                UPDATE users 
                SET is_premium = TRUE, premium_expiry = ?
                WHERE user_id = ?
            ''', (expiry.isoformat(), user_id))
            await db.commit()
    
    async def log_stream(self, user_id: int, song_title: str, 
                        song_url: str = None, duration: int = 0,
                        quality: str = '192'):
        """Log a stream"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO streams (user_id, song_title, song_url, duration, quality)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, song_title, song_url, duration, quality))
            
            await db.execute('''
                UPDATE users 
                SET total_streams = total_streams + 1,
                    total_time = total_time + ?,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (duration, user_id))
            await db.commit()
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT * FROM users WHERE user_id = ?',
                (user_id,)
            )
            user = await cursor.fetchone()
            
            if not user:
                return {}
            
            cursor = await db.execute('''
                SELECT song_title, COUNT(*) as count
                FROM streams
                WHERE user_id = ?
                GROUP BY song_title
                ORDER BY count DESC
                LIMIT 5
            ''', (user_id,))
            top_songs = await cursor.fetchall()
            
            return {
                'user_id': user[0],
                'username': user[1],
                'is_premium': user[3],
                'total_streams': user[5],
                'total_time': user[6],
                'top_songs': top_songs
            }

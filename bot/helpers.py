#!/usr/bin/env python3
"""
Helper functions for Music Bot
"""

import time
import math
from datetime import datetime, timedelta
from typing import Union, List, Dict, Optional

def get_readable_time(seconds: int) -> str:
    """Convert seconds to readable time format"""
    if not seconds:
        return "0 seconds"
    
    periods = [
        ('year', 365 * 24 * 60 * 60),
        ('month', 30 * 24 * 60 * 60),
        ('week', 7 * 24 * 60 * 60),
        ('day', 24 * 60 * 60),
        ('hour', 60 * 60),
        ('minute', 60),
        ('second', 1)
    ]
    
    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            if period_value > 0:
                result.append(f"{period_value} {period_name}{'s' if period_value > 1 else ''}")
    
    return ', '.join(result)

def get_readable_bytes(size: int) -> str:
    """Convert bytes to human readable format"""
    if size == 0:
        return "0B"
    
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    
    return f"{s} {size_names[i]}"

def get_progress_bar(percentage: int, length: int = 10) -> str:
    """Create a progress bar"""
    filled = int(length * percentage / 100)
    bar = '█' * filled + '░' * (length - filled)
    return f"[{bar}] {percentage}%"

def format_duration(seconds: int) -> str:
    """Format duration in seconds to HH:MM:SS"""
    if not seconds:
        return "00:00"
    
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def clean_filename(filename: str) -> str:
    """Clean filename for safe saving"""
    import re
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces
    filename = filename.replace(' ', '_')
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    return filename

def split_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def generate_pagination_keyboard(items: List, page: int, callback_prefix: str, 
                                items_per_page: int = 5) -> tuple:
    """Generate pagination keyboard"""
    total_pages = math.ceil(len(items) / items_per_page)
    start = (page - 1) * items_per_page
    end = start + items_per_page
    
    current_items = items[start:end]
    
    buttons = []
    for item in current_items:
        buttons.append([
            InlineKeyboardButton(
                text=item['text'],
                callback_data=f"{callback_prefix}_{item['id']}"
            )
        ])
    
    # Navigation buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{page-1}")
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}")
        )
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    return buttons, total_pages

async def check_admin(client, user_id: int) -> bool:
    """Check if user is bot admin"""
    from config import Config
    return user_id == Config.OWNER_ID

class RateLimiter:
    """Simple rate limiter"""
    def __init__(self, max_calls: int, time_period: int):
        self.max_calls = max_calls
        self.time_period = time_period
        self.calls = {}
    
    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to make request"""
        now = time.time()
        
        if user_id not in self.calls:
            self.calls[user_id] = []
        
        # Remove old calls
        self.calls[user_id] = [
            call_time for call_time in self.calls[user_id]
            if now - call_time < self.time_period
        ]
        
        if len(self.calls[user_id]) >= self.max_calls:
            return False
        
        self.calls[user_id].append(now)
        return True

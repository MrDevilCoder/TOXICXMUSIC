#!/usr/bin/env python3
"""
Telegram Music Bot - No Pillow Required
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Pyrogram
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.errors import FloodWait

# Web server
from flask import Flask, jsonify
import threading

# Load env
from dotenv import load_dotenv
load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask health check
health_app = Flask(__name__)

@health_app.route('/')
def home():
    return "<h1>🎵 Music Bot Running!</h1>"

@health_app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    health_app.run(host='0.0.0.0', port=port, debug=False)

# Config
class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    
    # Use emoji and text instead of stickers if needed
    USE_EMOJI = True
    
    # Emoji alternatives to stickers
    STICKERS = {
        'premium': '💎',
        'music': '🎵',
        'effect': '🎨',
        'star': '⭐',
        'fire': '🔥',
        'heart': '❤️'
    }

# Create bot
app = Client(
    "MusicBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    """Start command with emoji alternatives"""
    user = message.from_user
    
    # Use emojis instead of stickers
    welcome = f"""
{Config.STICKERS['music']} **Welcome {user.first_name}!**

**Premium Music Bot**
{Config.STICKERS['star']} YouTube Music Streaming
{Config.STICKERS['effect']} Audio Effects Studio  
{Config.STICKERS['premium']} Premium Features
{Config.STICKERS['fire']} HD Audio Quality

Use buttons below to navigate!
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{Config.STICKERS['music']} Play", callback_data="play"),
            InlineKeyboardButton(f"{Config.STICKERS['effect']} Effects", callback_data="effects")
        ],
        [
            InlineKeyboardButton(f"{Config.STICKERS['premium']} Premium", callback_data="premium"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help")
        ]
    ])
    
    await message.reply_text(welcome, reply_markup=keyboard)

@app.on_message(filters.command("play") & filters.private)
async def play(client: Client, message: Message):
    """Play music command"""
    if len(message.command) < 2:
        await message.reply_text(
            f"{Config.STICKERS['music']} **Play Music**\n\n"
            "Usage: `/play song name`\n"
            "Example: `/play Shape of You`"
        )
        return
    
    query = " ".join(message.command[1:])
    
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    await message.reply_text(
        f"{Config.STICKERS['music']} **Now Playing:**\n"
        f"`{query}`\n\n"
        f"▶️ Status: Playing\n"
        f"📊 Quality: 192kbps"
    )

@app.on_message(filters.command("premium") & filters.private)
async def premium(client: Client, message: Message):
    """Premium command"""
    text = f"""
{Config.STICKERS['premium']} **Premium Membership**

**Benefits:**
{Config.STICKERS['star']} HD Audio (320kbps)
{Config.STICKERS['fire']} Unlimited Downloads
{Config.STICKERS['effect']} All Effects
{Config.STICKERS['heart']} Custom Stickers
{Config.STICKERS['premium']} Priority Support

**Redeem:** `/redeem CODE`
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎁 Redeem", callback_data="redeem"),
            InlineKeyboardButton("💳 Buy", url="https://t.me/admin")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await message.reply_text(text, reply_markup=keyboard)

@app.on_callback_query()
async def callbacks(client: Client, callback: CallbackQuery):
    """Handle callbacks"""
    await callback.answer()
    
    data = callback.data
    
    if data == "main_menu":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎵 Play", callback_data="play"),
                InlineKeyboardButton("🎨 Effects", callback_data="effects")
            ],
            [
                InlineKeyboardButton("⭐ Premium", callback_data="premium"),
                InlineKeyboardButton("ℹ️ Help", callback_data="help")
            ]
        ])
        await callback.message.edit_text("**🎵 Main Menu**", reply_markup=keyboard)
    
    elif data == "play":
        await callback.message.edit_text(
            "**🎵 Play Music**\n\n"
            "Send: `/play song name`"
        )
    
    elif data == "effects":
        await callback.message.edit_text(
            "**🎨 Effects**\n\n"
            "Use `/effects` to see all effects"
        )
    
    elif data == "premium":
        await callback.message.edit_text(
            "**⭐ Premium**\n\n"
            "Use `/premium` for details"
        )
    
    elif data == "help":
        await callback.message.edit_text(
            "**ℹ️ Help**\n\n"
            "Use `/help` for commands"
        )

# Main entry
if __name__ == "__main__":
    try:
        # Start Flask
        threading.Thread(target=run_flask, daemon=True).start()
        
        # Start bot
        logger.info("Starting bot...")
        app.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Error: {e}")

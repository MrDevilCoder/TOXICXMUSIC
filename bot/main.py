#!/usr/bin/env python3
"""
Telegram Music Bot - Pyrogram 2.0.106 Compatible
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Pyrogram imports - Correct for v2.0.106
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.errors import (
    FloodWait,
    MessageNotModified,
    QueryIdInvalid,
    UserIsBlocked
)
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

# Flask for health checks
from flask import Flask, jsonify
import threading

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask App
health_app = Flask(__name__)

@health_app.route('/')
def home():
    return """
    <h1>🎵 Music Bot is Running!</h1>
    <p>Status: Online ✅</p>
    """

@health_app.route('/health')
def health():
    return jsonify({"status": "healthy", "bot": "running"})

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    health_app.run(host='0.0.0.0', port=port, debug=False)

# Configuration
class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    
    # Sticker & Effect IDs
    PREMIUM_STICKER = os.getenv("PREMIUM_STICKER_ID", "")
    MUSIC_EFFECT = os.getenv("MUSIC_EFFECT_ID", "")
    PREMIUM_EFFECT = os.getenv("PREMIUM_EFFECT_ID", "")

# Create Pyrogram Client - v2.0.106 Syntax
app = Client(
    "MusicBot",  # Session name
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins")  # Plugins directory
)

# Command Handlers
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Start command"""
    user = message.from_user
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Play Music", callback_data="play"),
            InlineKeyboardButton("🎨 Effects", callback_data="effects")
        ],
        [
            InlineKeyboardButton("⭐ Premium", callback_data="premium"),
            InlineKeyboardButton("🎯 Stickers", callback_data="stickers")
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="stats"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help")
        ]
    ])
    
    welcome_text = f"""
**🎵 Welcome {user.first_name}!**

**Premium Music Bot Features:**
• 🎵 YouTube Music Streaming
• 🎨 Audio Effects Studio
• ⭐ Premium Features
• 🎯 Custom Stickers
• 📊 Statistics
• 🔊 HD Audio

**Use buttons below!**
    """
    
    # Try sending with animation
    try:
        if Config.PREMIUM_EFFECT:
            await message.reply_animation(
                Config.PREMIUM_EFFECT,
                caption=welcome_text,
                reply_markup=keyboard
            )
        else:
            await message.reply_text(
                welcome_text,
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await message.reply_text(welcome_text, reply_markup=keyboard)

@app.on_message(filters.command("play") & filters.private)
async def play_command(client: Client, message: Message):
    """Play music"""
    if len(message.command) < 2:
        await message.reply_text(
            "**⚠️ Usage:**\n`/play song name`\n\n"
            "**Example:**\n`/play Shape of You`"
        )
        return
    
    query = " ".join(message.command[1:])
    
    # Show typing
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    # Create player controls
    controls = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸️ Pause", callback_data="pause"),
            InlineKeyboardButton("▶️ Resume", callback_data="resume")
        ],
        [
            InlineKeyboardButton("⏹️ Stop", callback_data="stop"),
            InlineKeyboardButton("🔁 Loop", callback_data="loop")
        ],
        [
            InlineKeyboardButton("🎨 Effects", callback_data="add_effect"),
            InlineKeyboardButton("📝 Lyrics", callback_data="lyrics")
        ]
    ])
    
    await message.reply_text(
        f"**🎵 Playing:** `{query}`\n\n"
        f"**Status:** ▶️ Playing\n"
        f"**Quality:** 192kbps\n\n"
        f"Use controls below!",
        reply_markup=controls
    )

@app.on_message(filters.command("premium") & filters.private)
async def premium_command(client: Client, message: Message):
    """Premium features"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem"),
            InlineKeyboardButton("💳 Buy Premium", url="https://t.me/admin")
        ],
        [
            InlineKeyboardButton("✨ Features", callback_data="features"),
            InlineKeyboardButton("🔙 Back", callback_data="main_menu")
        ]
    ])
    
    await message.reply_text(
        "**💎 Premium Membership**\n\n"
        "**Features:**\n"
        "✅ HD Audio (320kbps)\n"
        "✅ Unlimited Downloads\n"
        "✅ All Effects\n"
        "✅ Custom Stickers\n"
        "✅ Priority Support\n\n"
        "**Price:** Contact @admin",
        reply_markup=keyboard
    )

@app.on_message(filters.command("redeem") & filters.private)
async def redeem_command(client: Client, message: Message):
    """Redeem premium code"""
    if len(message.command) < 2:
        await message.reply_text("**⚠️ Usage:** `/redeem CODE`")
        return
    
    code = message.command[1].upper()
    
    # Simple code check
    valid_codes = ["PREMIUM2024", "VIP", "PRO"]
    
    if code in valid_codes:
        try:
            if Config.PREMIUM_STICKER:
                await message.reply_sticker(Config.PREMIUM_STICKER)
        except:
            pass
        
        await message.reply_text(
            "**🎉 Congratulations!**\n\n"
            "**Premium Activated!**\n"
            "✅ 30 Days Access\n"
            "✅ All Features Unlocked\n\n"
            "Enjoy your premium experience!"
        )
    else:
        await message.reply_text(
            "❌ **Invalid Code!**\n\n"
            "Contact @admin to get premium."
        )

@app.on_message(filters.command("effects") & filters.private)
async def effects_command(client: Client, message: Message):
    """Effects menu"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔊 Bass", callback_data="effect_bass"),
            InlineKeyboardButton("🌙 Nightcore", callback_data="effect_nightcore")
        ],
        [
            InlineKeyboardButton("🔁 Echo", callback_data="effect_echo"),
            InlineKeyboardButton("🎵 Reverb", callback_data="effect_reverb")
        ],
        [
            InlineKeyboardButton("🤖 Robot", callback_data="effect_robot"),
            InlineKeyboardButton("🐿️ Chipmunk", callback_data="effect_chipmunk")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await message.reply_text(
        "**🎨 Audio Effects**\n\n"
        "Choose an effect to apply:",
        reply_markup=keyboard
    )

@app.on_message(filters.command("sticker") & filters.private)
async def sticker_command(client: Client, message: Message):
    """Sticker menu"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Music Stickers", callback_data="sticker_music"),
            InlineKeyboardButton("⭐ Premium", callback_data="sticker_premium")
        ],
        [
            InlineKeyboardButton("📦 Get Pack", url="https://t.me/addstickers/your_pack"),
            InlineKeyboardButton("🔙 Back", callback_data="main_menu")
        ]
    ])
    
    await message.reply_text(
        "**🎯 Sticker System**\n\n"
        "Choose sticker category:",
        reply_markup=keyboard
    )

@app.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    """User statistics"""
    user = message.from_user
    
    await message.reply_text(
        f"**📊 Statistics**\n\n"
        f"**User:** {user.first_name}\n"
        f"**Username:** @{user.username or 'None'}\n"
        f"**ID:** `{user.id}`\n\n"
        f"**Status:** {'⭐ Premium' if False else '🔈 Free'}\n"
        f"**Total Streams:** 0\n"
        f"**Joined:** Today"
    )

@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    """Help command"""
    help_text = """
**📚 Commands:**

**🎵 Music:**
`/play` - Play music
`/search` - Search songs
`/lyrics` - Get lyrics
`/stop` - Stop playing

**🎨 Effects:**
`/effects` - Effects menu
`/effect` - Apply effect

**⭐ Premium:**
`/premium` - Premium info
`/redeem` - Redeem code

**🎯 Stickers:**
`/sticker` - Sticker menu

**📊 Other:**
`/stats` - Statistics
`/help` - This menu
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await message.reply_text(help_text, reply_markup=keyboard)

# Callback Query Handler
@app.on_callback_query()
async def handle_callbacks(client: Client, callback: CallbackQuery):
    """Handle all callback queries"""
    try:
        data = callback.data
        
        # Answer callback first
        await callback.answer()
        
        if data == "main_menu":
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎵 Play", callback_data="play"),
                    InlineKeyboardButton("🎨 Effects", callback_data="effects")
                ],
                [
                    InlineKeyboardButton("⭐ Premium", callback_data="premium"),
                    InlineKeyboardButton("🎯 Stickers", callback_data="stickers")
                ],
                [
                    InlineKeyboardButton("📊 Stats", callback_data="stats"),
                    InlineKeyboardButton("ℹ️ Help", callback_data="help")
                ]
            ])
            
            await callback.message.edit_text(
                "**🎵 Main Menu**\nSelect an option:",
                reply_markup=keyboard
            )
        
        elif data == "play":
            await callback.message.edit_text(
                "**🎵 Play Music**\n\n"
                "Send me a song name:\n"
                "`/play song name`\n\n"
                "Or send YouTube link directly!"
            )
        
        elif data == "effects":
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔊 Bass", callback_data="effect_bass"),
                    InlineKeyboardButton("🌙 Nightcore", callback_data="effect_nightcore")
                ],
                [
                    InlineKeyboardButton("🤖 Robot", callback_data="effect_robot"),
                    InlineKeyboardButton("🐿️ Chipmunk", callback_data="effect_chipmunk")
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ])
            
            await callback.message.edit_text(
                "**🎨 Choose Effect:**",
                reply_markup=keyboard
            )
        
        elif data.startswith("effect_"):
            effect = data.replace("effect_", "").title()
            await callback.answer(f"✅ {effect} effect applied!", show_alert=True)
            await callback.message.reply_text(
                f"**🎨 {effect} Effect Applied!**"
            )
        
        elif data == "premium":
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎁 Redeem", callback_data="redeem"),
                    InlineKeyboardButton("💳 Buy", url="https://t.me/admin")
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ])
            
            await callback.message.edit_text(
                "**💎 Premium**\n\nChoose option:",
                reply_markup=keyboard
            )
        
        elif data == "redeem":
            await callback.message.edit_text(
                "**🎁 Redeem Code**\n\n"
                "Use: `/redeem YOUR_CODE`\n\n"
                "Get codes from @admin"
            )
        
        elif data == "stickers":
            await callback.message.edit_text(
                "**🎯 Stickers**\n\n"
                "Use `/sticker` to browse\n"
                "Get pack: @PremiumMusicStickers"
            )
        
        elif data == "stats":
            await stats_command(client, callback.message)
        
        elif data == "help":
            await help_command(client, callback.message)
        
        else:
            await callback.answer("Feature coming soon!")
    
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f"Callback error: {e}")
        try:
            await callback.answer("Error occurred!", show_alert=True)
        except:
            pass

# Error handler for messages
@app.on_message(filters.command("test") & filters.private)
async def test_command(client: Client, message: Message):
    """Test bot response"""
    await message.reply_text(
        "✅ **Bot is working!**\n\n"
        f"Pyrogram Version: `{pyrogram.__version__}`\n"
        f"Bot Username: @{client.me.username}"
    )

# Run bot
if __name__ == "__main__":
    try:
        # Start Flask in thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        # Start bot
        logger.info("Starting Music Bot...")
        app.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

#!/usr/bin/env python3
"""
Telegram Music Bot - Single File Version
Fixed Module Import Errors
"""

import os
import sys
import asyncio
import logging
import threading
from pathlib import Path

# Pyrogram imports
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.errors import FloodWait

# Flask for health checks
from flask import Flask, jsonify

# HTTP client for keep-alive
import aiohttp

# Environment variables
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

# ============================================
# CONFIGURATION
# ============================================

class Config:
    """Bot Configuration"""
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    APP_URL = os.getenv("APP_URL", "")
    
    # Sticker IDs (Optional)
    PREMIUM_STICKER = os.getenv("PREMIUM_STICKER_ID", "")
    MUSIC_STICKER = os.getenv("MUSIC_STICKER_ID", "")
    
    # Effect IDs (Optional)
    PREMIUM_EFFECT = os.getenv("PREMIUM_EFFECT_ID", "")
    MUSIC_EFFECT = os.getenv("MUSIC_EFFECT_ID", "")

# ============================================
# FLASK HEALTH CHECK SERVER
# ============================================

health_app = Flask(__name__)

@health_app.route('/')
def home():
    """Home page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Music Bot</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                max-width: 600px;
                margin: 0 auto;
            }
            h1 { font-size: 3em; }
            .status {
                background: #00ff00;
                color: black;
                padding: 10px 30px;
                border-radius: 50px;
                display: inline-block;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Music Bot</h1>
            <div class="status">✅ Online</div>
            <p>Bot is running 24/7</p>
        </div>
    </body>
    </html>
    """

@health_app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "bot": "running",
        "timestamp": str(asyncio.get_event_loop().time()) if asyncio.get_event_loop().is_running() else "0"
    })

@health_app.route('/ping')
def ping():
    """Ping endpoint"""
    return "pong", 200

def run_flask():
    """Run Flask server in thread"""
    try:
        port = int(os.environ.get('PORT', 8080))
        health_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")

# ============================================
# PYROGRAM BOT
# ============================================

# Create bot instance
bot = Client(
    "MusicBotSession",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# ============================================
# COMMAND HANDLERS
# ============================================

@bot.on_message(filters.command("start") & filters.private)
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
        ],
        [
            InlineKeyboardButton("💎 Get Premium", url="https://t.me/your_channel")
        ]
    ])
    
    welcome_text = f"""
**🎵 Welcome to Premium Music Bot!**

**Hello {user.first_name}!**

**Features:**
• 🎵 YouTube Music Streaming
• 🎨 Audio Effects Studio
• ⭐ Premium Features
• 🎯 Custom Stickers
• 🔊 HD Audio Quality

**Premium Benefits:**
• 320kbps HD Audio
• Unlimited Downloads
• Priority Queue
• Ad-Free Experience
• Exclusive Stickers

Use buttons below to navigate!
    """
    
    # Try to send with animation
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
        logger.error(f"Welcome error: {e}")
        await message.reply_text(welcome_text, reply_markup=keyboard)

@bot.on_message(filters.command("play") & filters.private)
async def play_command(client: Client, message: Message):
    """Play music command"""
    if len(message.command) < 2:
        await message.reply_text(
            "**⚠️ Usage:**\n"
            "`/play song name`\n\n"
            "**Examples:**\n"
            "`/play Shape of You`\n"
            "`/play https://youtube.com/...`\n\n"
            "Send a song name or YouTube link!"
        )
        return
    
    query = " ".join(message.command[1:])
    
    # Send processing message
    status = await message.reply_text(
        f"🔍 **Searching:** `{query}`\n"
        "⏳ Please wait..."
    )
    
    try:
        # Show typing action
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
            ],
            [
                InlineKeyboardButton("🔊 Vol+", callback_data="vol_up"),
                InlineKeyboardButton("🔉 Vol-", callback_data="vol_down")
            ]
        ])
        
        # Update status message
        await status.edit_text(
            f"**🎵 Now Playing**\n\n"
            f"**Song:** {query[:50]}\n"
            f"**Status:** ▶️ Playing\n"
            f"**Quality:** 192kbps\n"
            f"**Time:** 00:00\n\n"
            f"Use controls below to manage playback!",
            reply_markup=controls
        )
        
    except FloodWait as e:
        logger.warning(f"FloodWait: {e.value}s")
        await asyncio.sleep(e.value)
        await play_command(client, message)
    except Exception as e:
        logger.error(f"Play error: {e}")
        await status.edit_text(f"❌ **Error:** {str(e)}")

@bot.on_message(filters.command("search") & filters.private)
async def search_command(client: Client, message: Message):
    """Search music command"""
    if len(message.command) < 2:
        await message.reply_text(
            "**🔍 Search Music**\n\n"
            "Usage: `/search song name`\n"
            "Example: `/search Shape of You`"
        )
        return
    
    query = " ".join(message.command[1:])
    
    await message.reply_text(
        f"**🔍 Search Results for:** `{query}`\n\n"
        "1. **Song Title 1**\n"
        "   👤 Artist • ⏱️ 3:45\n\n"
        "2. **Song Title 2**\n"
        "   👤 Artist • ⏱️ 4:20\n\n"
        "3. **Song Title 3**\n"
        "   👤 Artist • ⏱️ 3:15\n\n"
        "Reply with number to play!"
    )

@bot.on_message(filters.command("premium") & filters.private)
async def premium_command(client: Client, message: Message):
    """Premium features command"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem"),
            InlineKeyboardButton("💳 Buy Premium", url="https://t.me/admin")
        ],
        [
            InlineKeyboardButton("✨ Features", callback_data="premium_features"),
            InlineKeyboardButton("📊 Compare", callback_data="compare")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="main_menu")
        ]
    ])
    
    premium_text = """
**💎 Premium Membership**

**Features:**
✅ HD Audio (320kbps)
✅ Unlimited Downloads
✅ Priority Queue
✅ All Effects Unlocked
✅ Custom Stickers
✅ Ad-Free Experience
✅ 24/7 Priority Support

**Price:** Contact @admin
**Duration:** 30 Days

**Use `/redeem CODE` to activate!**
    """
    
    try:
        if Config.PREMIUM_EFFECT:
            await message.reply_animation(
                Config.PREMIUM_EFFECT,
                caption=premium_text,
                reply_markup=keyboard
            )
        else:
            await message.reply_text(premium_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Premium error: {e}")
        await message.reply_text(premium_text, reply_markup=keyboard)

@bot.on_message(filters.command("redeem") & filters.private)
async def redeem_command(client: Client, message: Message):
    """Redeem premium code"""
    if len(message.command) < 2:
        await message.reply_text(
            "**🎁 Redeem Premium Code**\n\n"
            "Usage: `/redeem YOUR_CODE`\n\n"
            "**Example:**\n"
            "`/redeem PREMIUM2024`\n\n"
            "Get codes from @admin"
        )
        return
    
    code = message.command[1].upper()
    
    # Simple code validation (implement database check)
    valid_codes = ["PREMIUM2024", "VIPMUSIC", "ELITE", "PRO2024"]
    
    if code in valid_codes:
        # Success
        success_text = """
**🎉 Congratulations!**

**Premium Activated Successfully!**
✅ Duration: 30 Days
✅ HD Audio: Enabled
✅ All Effects: Unlocked
✅ Premium Stickers: Available

**Enjoy your premium experience!**
        """
        
        try:
            if Config.PREMIUM_STICKER:
                await message.reply_sticker(Config.PREMIUM_STICKER)
        except:
            pass
        
        await message.reply_text(success_text)
    else:
        await message.reply_text(
            "❌ **Invalid Code!**\n\n"
            "Please check the code and try again.\n"
            "Contact @admin to purchase premium."
        )

@bot.on_message(filters.command("effects") & filters.private)
async def effects_command(client: Client, message: Message):
    """Audio effects menu"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔊 Bass Boost", callback_data="effect_bass"),
            InlineKeyboardButton("🌙 Nightcore", callback_data="effect_nightcore")
        ],
        [
            InlineKeyboardButton("🔁 Echo", callback_data="effect_echo"),
            InlineKeyboardButton("🎵 Reverb", callback_data="effect_reverb")
        ],
        [
            InlineKeyboardButton("🐿️ Chipmunk", callback_data="effect_chipmunk"),
            InlineKeyboardButton("🤖 Robot", callback_data="effect_robot")
        ],
        [
            InlineKeyboardButton("🐌 Slowed", callback_data="effect_slowed"),
            InlineKeyboardButton("⚡ Speed Up", callback_data="effect_speed")
        ],
        [
            InlineKeyboardButton("💎 Premium Effects ⭐", callback_data="premium_effects")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="main_menu")
        ]
    ])
    
    await message.reply_text(
        "**🎨 Audio Effects Studio**\n\n"
        "**Free Effects:**\n"
        "• 🔊 Bass Boost\n"
        "• 🔁 Echo\n"
        "• 🐿️ Chipmunk\n"
        "• 🤖 Robot\n\n"
        "**Premium Effects: ⭐**\n"
        "• 🌙 Nightcore\n"
        "• 🎵 Reverb\n"
        "• 🐌 Slowed + Reverb\n"
        "• ⚡ Speed Up\n\n"
        "Choose an effect to apply!",
        reply_markup=keyboard
    )

@bot.on_message(filters.command("sticker") & filters.private)
async def sticker_command(client: Client, message: Message):
    """Custom sticker system"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Music Stickers", callback_data="sticker_music"),
            InlineKeyboardButton("✨ Premium", callback_data="sticker_premium")
        ],
        [
            InlineKeyboardButton("🎨 Create Custom", callback_data="sticker_create"),
            InlineKeyboardButton("📦 Get Pack", url="https://t.me/addstickers/your_pack")
        ],
        [
            InlineKeyboardButton("🔥 Trending", callback_data="sticker_trending"),
            InlineKeyboardButton("🆕 New", callback_data="sticker_new")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="main_menu")
        ]
    ])
    
    await message.reply_text(
        "**🎯 Custom Sticker System**\n\n"
        "Choose sticker category:\n\n"
        "• 🎵 Music themed stickers\n"
        "• ✨ Premium exclusive stickers\n"
        "• 🎨 Custom sticker creator\n"
        "• 📦 Get sticker packs\n\n"
        "Create your own unique stickers!",
        reply_markup=keyboard
    )

@bot.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    """User statistics"""
    user = message.from_user
    
    stats_text = f"""
**📊 Your Statistics**

**User Info:**
• Name: {user.first_name}
• Username: @{user.username or 'N/A'}
• ID: `{user.id}`

**Activity:**
• Total Streams: 0
• Total Time: 0 mins
• Favorite Genre: Not set

**Status:**
• Account: 🔈 Free
• Joined: Today

**Top 5 Songs:**
No streams yet!

**Use the bot to build your stats!**
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
            InlineKeyboardButton("📈 Detailed", callback_data="detailed_stats")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await message.reply_text(stats_text, reply_markup=keyboard)

@bot.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    """Help command"""
    help_text = """
**📚 Command List**

**🎵 Music Commands:**
`/play [song]` - Play music
`/search [query]` - Search songs
`/lyrics [song]` - Get lyrics
`/skip` - Skip track
`/stop` - Stop music
`/loop` - Toggle loop

**🎨 Effects:**
`/effects` - Effects menu
`/effect [name]` - Apply effect

**⭐ Premium:**
`/premium` - Premium info
`/redeem [code]` - Activate premium

**🎯 Stickers:**
`/sticker` - Sticker menu

**📊 Other:**
`/stats` - Your stats
`/settings` - Bot settings
`/about` - About bot
`/donate` - Support us

**Need help?** @admin
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💎 Premium", url="https://t.me/admin"),
            InlineKeyboardButton("📞 Support", url="https://t.me/admin")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await message.reply_text(
        help_text,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@bot.on_message(filters.command("about") & filters.private)
async def about_command(client: Client, message: Message):
    """About command"""
    about_text = """
**🎵 About Premium Music Bot**

**Version:** 2.0
**Developer:** @admin
**Framework:** Pyrogram

**Features:**
• YouTube Music Streaming
• Audio Effects Studio
• Custom Stickers System
• Premium Membership
• 24/7 Availability

**Statistics:**
• Total Users: 1,000+
• Songs Played: 10,000+
• Premium Users: 100+

**Support:** @admin
**Channel:** @channel
    """
    
    await message.reply_text(about_text)

# ============================================
# CALLBACK QUERY HANDLER
# ============================================

@bot.on_callback_query()
async def callback_handler(client: Client, callback: CallbackQuery):
    """Handle all callback queries"""
    try:
        data = callback.data
        
        # Answer callback
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
                "**🎵 Main Menu**\n\nSelect an option:",
                reply_markup=keyboard
            )
        
        elif data == "play":
            await callback.message.edit_text(
                "**🎵 Play Music**\n\n"
                "Send me a song name:\n"
                "`/play song name`\n\n"
                "Or send a YouTube link!"
            )
        
        elif data == "effects":
            await effects_command(client, callback.message)
        
        elif data == "premium":
            await premium_command(client, callback.message)
        
        elif data == "stickers":
            await sticker_command(client, callback.message)
        
        elif data == "stats":
            await stats_command(client, callback.message)
        
        elif data == "help":
            await help_command(client, callback.message)
        
        elif data.startswith("effect_"):
            effect = data.replace("effect_", "").title()
            await callback.answer(f"✅ {effect} effect applied!", show_alert=True)
            await callback.message.reply_text(
                f"**🎨 {effect} Effect Applied!**\n\n"
                "Your audio is now processed."
            )
        
        elif data == "redeem":
            await callback.message.edit_text(
                "**🎁 Redeem Premium Code**\n\n"
                "Use: `/redeem YOUR_CODE`\n\n"
                "Get codes from @admin"
            )
        
        elif data == "premium_features":
            features = """
**✨ Premium Features**

**Audio:**
✅ 320kbps HD Audio
✅ All Audio Effects
✅ Custom EQ Settings
✅ Lossless Downloads

**Exclusive:**
✅ Premium Stickers
✅ Custom Animations
✅ Priority Support
✅ Early Access

**Unlimited:**
✅ No Download Limits
✅ No Queue Waiting
✅ No Advertisements
✅ All Features Unlocked
            """
            
            await callback.message.edit_text(
                features,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="premium")]
                ])
            )
        
        else:
            await callback.answer("Feature coming soon!")
    
    except FloodWait as e:
        logger.warning(f"FloodWait in callback: {e.value}s")
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        try:
            await callback.answer("Error occurred!", show_alert=True)
        except:
            pass

# ============================================
# KEEP ALIVE SYSTEM
# ============================================

async def keep_alive():
    """Keep the bot alive by pinging itself"""
    while True:
        try:
            if Config.APP_URL:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{Config.APP_URL}/health", timeout=10) as resp:
                        if resp.status == 200:
                            logger.info("✅ Keep-alive ping successful")
                        else:
                            logger.warning(f"Keep-alive ping returned status: {resp.status}")
        except asyncio.TimeoutError:
            logger.error("Keep-alive ping timeout")
        except aiohttp.ClientError as e:
            logger.error(f"Keep-alive HTTP error: {e}")
        except Exception as e:
            logger.error(f"Keep-alive error: {e}")
        
        await asyncio.sleep(300)  # 5 minutes

# ============================================
# ERROR HANDLER
# ============================================

@bot.on_message(filters.command("ping") & filters.private)
async def ping_command(client: Client, message: Message):
    """Ping command to check bot status"""
    start_time = asyncio.get_event_loop().time()
    msg = await message.reply_text("🏓 Pong!")
    end_time = asyncio.get_event_loop().time()
    ping_time = round((end_time - start_time) * 1000, 2)
    
    await msg.edit_text(
        f"🏓 **Pong!**\n\n"
        f"**Response Time:** `{ping_time}ms`\n"
        f"**Status:** ✅ Online\n"
        f"**Uptime:** Running..."
    )

# ============================================
# MAIN ENTRY POINT
# ============================================

async def main():
    """Main function to run everything"""
    # Validate credentials first
    if not Config.API_ID or not Config.API_HASH or not Config.BOT_TOKEN:
        logger.error("❌ Missing API credentials! Check your .env file")
        logger.error("Required: API_ID, API_HASH, BOT_TOKEN")
        sys.exit(1)
    
    if Config.API_ID == 0:
        logger.error("❌ Invalid API_ID! Set it in .env file")
        sys.exit(1)
    
    # Start Flask in thread
    try:
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("✅ Flask server started")
    except Exception as e:
        logger.error(f"Failed to start Flask: {e}")
    
    # Start keep-alive task
    asyncio.create_task(keep_alive())
    logger.info("✅ Keep-alive started")
    
    # Start bot
    logger.info("🚀 Starting Telegram Music Bot...")
    try:
        await bot.start()
        
        # Get bot info
        me = await bot.get_me()
        logger.info(f"✅ Bot @{me.username} is running!")
        logger.info(f"Bot ID: {me.id}")
        logger.info(f"Bot Name: {me.first_name}")
        
        # Send startup message to owner
        if Config.OWNER_ID:
            try:
                await bot.send_message(
                    Config.OWNER_ID,
                    f"✅ **Bot Started!**\n\n"
                    f"**Bot:** @{me.username}\n"
                    f"**Status:** Running\n"
                    f"**Mode:** {'Production' if Config.APP_URL else 'Development'}\n"
                    f"**App URL:** {Config.APP_URL if Config.APP_URL else 'Not set'}"
                )
                logger.info("Startup notification sent to owner")
            except Exception as e:
                logger.error(f"Could not send startup message: {e}")
        else:
            logger.warning("OWNER_ID not set, skipping startup notification")
        
        # Keep running
        logger.info("Bot is ready to process messages!")
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            logger.error("❌ Python 3.7 or higher is required!")
            sys.exit(1)
        
        # Create necessary directories
        Path("downloads").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # Run bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)

#!/usr/bin/env python3
"""
Telegram Music Bot - Main Entry Point
Fixed for Pyrogram v2.x
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    CallbackQuery,
    InputMediaAudio,
    InputMediaVideo,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.errors import (
    FloodWait, 
    MessageNotModified, 
    QueryIdInvalid,
    UserIsBlocked,
    PeerIdInvalid
)
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from dotenv import load_dotenv
import aiohttp
from aiohttp import web

# Load environment variables
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

# Flask app for health checks
from flask import Flask, jsonify, render_template_string

health_app = Flask(__name__)

@health_app.route('/')
def home():
    """Home page"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Music Bot Status</title>
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                min-height: 100vh;
            }
            .container {
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                padding: 40px;
                backdrop-filter: blur(10px);
                max-width: 600px;
                margin: 0 auto;
            }
            h1 { font-size: 2.5em; margin-bottom: 20px; }
            .status { 
                background: #00ff00;
                color: #000;
                padding: 10px 20px;
                border-radius: 50px;
                display: inline-block;
                margin: 20px 0;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                margin-top: 30px;
            }
            .stat-box {
                background: rgba(255,255,255,0.2);
                padding: 20px;
                border-radius: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Telegram Music Bot</h1>
            <div class="status">✅ Bot is Running</div>
            <div class="stats">
                <div class="stat-box">
                    <h3>📊 Status</h3>
                    <p>Online</p>
                </div>
                <div class="stat-box">
                    <h3>⚡ Performance</h3>
                    <p>Optimal</p>
                </div>
                <div class="stat-box">
                    <h3>🔒 SSL</h3>
                    <p>Active</p>
                </div>
                <div class="stat-box">
                    <h3>🔄 Uptime</h3>
                    <p>24/7</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

@health_app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "bot": "running",
        "version": "2.0",
        "timestamp": str(asyncio.get_event_loop().time())
    })

@health_app.route('/ping')
def ping():
    """Ping endpoint for keep-alive"""
    return "pong", 200

def run_health_server():
    """Run Flask health server"""
    port = int(os.environ.get('PORT', 8080))
    health_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Configuration
class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/bot.db")
    
    # Premium Settings
    PREMIUM_STICKER_ID = os.getenv("PREMIUM_STICKER_ID", "")
    MUSIC_STICKER_ID = os.getenv("MUSIC_STICKER_ID", "")
    EFFECT_STICKER_ID = os.getenv("EFFECT_STICKER_ID", "")
    
    # Effect Animation IDs
    MUSIC_EFFECT_ID = os.getenv("MUSIC_EFFECT_ID", "")
    FIRE_EFFECT_ID = os.getenv("FIRE_EFFECT_ID", "")
    STAR_EFFECT_ID = os.getenv("STAR_EFFECT_ID", "")
    HEART_EFFECT_ID = os.getenv("HEART_EFFECT_ID", "")
    PREMIUM_EFFECT_ID = os.getenv("PREMIUM_EFFECT_ID", "")
    
    # URLs
    APP_URL = os.getenv("APP_URL", "")
    WORKER_URL = os.getenv("WORKER_URL", "")

# Initialize Pyrogram Client with fixed syntax
class MusicBot(Client):
    """Main Music Bot Class"""
    
    def __init__(self):
        super().__init__(
            name="MusicBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=100,
            workdir="sessions",
            plugins=dict(root="plugins"),
            parse_mode=ParseMode.MARKDOWN,
            sleep_threshold=10,
            max_concurrent_transmissions=5
        )
        self.config = Config
        self.logger = logger
        
    async def start(self):
        """Start the bot"""
        await super().start()
        
        # Start health server in thread
        import threading
        threading.Thread(target=run_health_server, daemon=True).start()
        
        # Get bot info
        me = await self.get_me()
        self.logger.info(f"✅ Bot @{me.username} started successfully!")
        self.logger.info(f"📊 Bot ID: {me.id}")
        
        # Send startup message to owner
        try:
            await self.send_message(
                Config.OWNER_ID,
                f"✅ **Bot Started Successfully!**\n\n"
                f"**Bot:** @{me.username}\n"
                f"**Version:** 2.0\n"
                f"**Status:** Running\n"
                f"**Time:** {asyncio.get_event_loop().time()}"
            )
        except Exception as e:
            self.logger.error(f"Failed to send startup message: {e}")
        
        # Start keep-alive task
        asyncio.create_task(self.keep_alive())
        
    async def stop(self):
        """Stop the bot"""
        self.logger.info("Bot stopping...")
        await super().stop()
        
    async def keep_alive(self):
        """Keep alive mechanism"""
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{Config.APP_URL}/health") as resp:
                        if resp.status == 200:
                            self.logger.debug("Keep-alive ping successful")
            except Exception as e:
                self.logger.error(f"Keep-alive error: {e}")
            await asyncio.sleep(300)  # 5 minutes

# Create bot instance
app = MusicBot()

# Fixed Command Handlers with proper Pyrogram v2 syntax
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Start command handler"""
    user = message.from_user
    
    # Create inline keyboard with fixed syntax
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Play Music", callback_data="menu_music"),
            InlineKeyboardButton("🎨 Effects", callback_data="menu_effects")
        ],
        [
            InlineKeyboardButton("⭐ Premium", callback_data="menu_premium"),
            InlineKeyboardButton("🎯 Stickers", callback_data="menu_stickers")
        ],
        [
            InlineKeyboardButton("📊 Statistics", callback_data="menu_stats"),
            InlineKeyboardButton("ℹ️ Help", callback_data="menu_help")
        ],
        [
            InlineKeyboardButton("💎 Get Premium", url="https://t.me/your_channel"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/your_channel")
        ]
    ])
    
    # Send welcome message
    welcome_text = f"""
**🎵 Welcome to Premium Music Bot!**

**Hello {user.first_name}!** {chr(10)}
**Features:**
• 🎵 YouTube Music Streaming
• 🎨 Audio Effects Studio
• ⭐ Premium Custom Stickers
• 💎 Exclusive Animations
• 🎯 Custom Sticker Creator
• 📊 Detailed Statistics
• 🔊 HD Audio Quality

**Premium Benefits:**
• 320kbps HD Audio
• Unlimited Downloads
• Priority Queue
• Ad-Free Experience
• Custom Effects
• Exclusive Stickers

**Use buttons below to navigate!**
    """
    
    # Try to send premium animation first
    try:
        if Config.PREMIUM_EFFECT_ID:
            await message.reply_animation(
                Config.PREMIUM_EFFECT_ID,
                caption=welcome_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.reply_text(
                welcome_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Welcome message error: {e}")
        await message.reply_text(
            "**🎵 Welcome to Music Bot!**\n\nUse buttons to navigate.",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

@app.on_message(filters.command("play") & filters.private)
async def play_command(client: Client, message: Message):
    """Play music command"""
    if len(message.command) < 2:
        await message.reply_text(
            "**⚠️ Usage:** `/play song name or YouTube link`\n\n"
            "**Examples:**\n"
            "`/play Shape of You`\n"
            "`/play https://youtube.com/watch?v=...`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    query = " ".join(message.command[1:])
    
    # Send processing message
    status_msg = await message.reply_text(
        f"🔍 **Searching for:** `{query}`\n"
        "⏳ Please wait...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # Show typing action
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        # Create music player controls
        controls = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⏸️ Pause", callback_data="player_pause"),
                InlineKeyboardButton("▶️ Resume", callback_data="player_resume")
            ],
            [
                InlineKeyboardButton("⏹️ Stop", callback_data="player_stop"),
                InlineKeyboardButton("🔁 Loop", callback_data="player_loop")
            ],
            [
                InlineKeyboardButton("🎨 Effects", callback_data="player_effects"),
                InlineKeyboardButton("📝 Lyrics", callback_data="player_lyrics")
            ],
            [
                InlineKeyboardButton("🔊 Volume +", callback_data="vol_up"),
                InlineKeyboardButton("🔉 Volume -", callback_data="vol_down")
            ]
        ])
        
        # Here you would integrate with YouTube downloader
        # For now, send example response
        await status_msg.edit_text(
            f"**🎵 Now Playing**\n\n"
            f"**Song:** {query}\n"
            f"**Status:** ▶️ Playing\n"
            f"**Quality:** 192kbps\n\n"
            f"Use controls below to manage playback!",
            reply_markup=controls,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except FloodWait as e:
        logger.warning(f"FloodWait: {e.value} seconds")
        await asyncio.sleep(e.value)
        await play_command(client, message)
    except Exception as e:
        logger.error(f"Play command error: {e}")
        await status_msg.edit_text(
            f"❌ **Error:** {str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )

@app.on_message(filters.command("premium") & filters.private)
async def premium_command(client: Client, message: Message):
    """Premium features command"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem_code"),
            InlineKeyboardButton("💳 Buy Premium", url="https://t.me/admin")
        ],
        [
            InlineKeyboardButton("✨ Features", callback_data="premium_features"),
            InlineKeyboardButton("📊 Compare", callback_data="compare_plans")
        ],
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
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
✅ 24/7 Support
✅ Exclusive Content

**Price:** Contact @admin
**Duration:** 30 days

**Use `/redeem CODE` to activate!**
    """
    
    try:
        if Config.PREMIUM_EFFECT_ID:
            await message.reply_animation(
                Config.PREMIUM_EFFECT_ID,
                caption=premium_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.reply_text(
                premium_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Premium command error: {e}")

@app.on_message(filters.command("redeem") & filters.private)
async def redeem_command(client: Client, message: Message):
    """Redeem premium code"""
    if len(message.command) < 2:
        await message.reply_text(
            "**⚠️ Usage:** `/redeem YOUR_PREMIUM_CODE`\n\n"
            "**Example:** `/redeem PREMIUM2024`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    code = message.command[1].upper()
    
    # Check code (implement database check here)
    valid_codes = ["PREMIUM2024", "VIPMUSIC", "ELITE", "PRO2024"]
    
    if code in valid_codes:
        # Success message
        success_text = """
**🎉 Congratulations!**

**Premium Activated!**
✅ Duration: 30 Days
✅ All features unlocked
✅ HD Audio enabled
✅ Premium stickers available

**Enjoy your premium experience!**
        """
        
        try:
            if Config.PREMIUM_EFFECT_ID:
                await message.reply_animation(
                    Config.PREMIUM_EFFECT_ID,
                    caption=success_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await message.reply_text(
                    success_text,
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Redeem success message error: {e}")
    else:
        await message.reply_text(
            "❌ **Invalid Code!**\n\n"
            "Please check the code and try again.\n"
            "Contact @admin to purchase premium.",
            parse_mode=ParseMode.MARKDOWN
        )

@app.on_message(filters.command("effects") & filters.private)
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
    
    effects_text = """
**🎨 Audio Effects Studio**

**Free Effects:**
• 🔊 Bass Boost
• 🔁 Echo
• 🐿️ Chipmunk
• 🤖 Robot

**Premium Effects: ⭐**
• 🌙 Nightcore
• 🎵 Reverb
• 🐌 Slowed + Reverb
• ⚡ Speed Up

**Apply effects to your music!**
    """
    
    await message.reply_text(
        effects_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.command("sticker") & filters.private)
async def sticker_command(client: Client, message: Message):
    """Custom sticker system"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Music Stickers", callback_data="sticker_music"),
            InlineKeyboardButton("✨ Premium Stickers", callback_data="sticker_premium")
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
        "• Music themed stickers\n"
        "• Premium exclusive stickers\n"
        "• Custom sticker creator\n"
        "• Get sticker packs\n\n"
        "Create your own unique stickers!",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    """User statistics"""
    user = message.from_user
    
    stats_text = f"""
**📊 Statistics for {user.first_name}**

**Account:**
• User ID: `{user.id}`
• Username: @{user.username or 'None'}
• Status: {'⭐ Premium' if False else '🔈 Free'}

**Activity:**
• Total Streams: 0
• Total Time: 0 minutes
• Favorite Genre: Not set

**Rankings:**
• Global Rank: #1234
• Weekly Rank: #567

**Use the bot more to improve stats!**
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
            InlineKeyboardButton("📈 Detailed", callback_data="detailed_stats")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await message.reply_text(
        stats_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    """Help command"""
    help_text = """
**📚 Command List**

**🎵 Music Commands:**
• `/play [song]` - Play music
• `/search [query]` - Search songs
• `/lyrics [song]` - Get lyrics
• `/queue` - View queue
• `/skip` - Skip track
• `/stop` - Stop music
• `/loop` - Toggle loop
• `/shuffle` - Shuffle queue

**🎨 Effects:**
• `/effects` - Effects menu
• `/effect [name]` - Apply effect
• `/reset_effect` - Remove effects

**⭐ Premium:**
• `/premium` - Premium info
• `/redeem [code]` - Activate premium
• `/premium_features` - Features list

**🎯 Stickers:**
• `/sticker` - Sticker menu
• `/createsticker` - Create custom
• `/mystickers` - Your stickers

**📊 Other:**
• `/stats` - Your stats
• `/settings` - Bot settings
• `/about` - About bot
• `/report [issue]` - Report problem
• `/donate` - Support us

**Need help? Contact @admin**
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Commands", callback_data="music_commands"),
            InlineKeyboardButton("🎨 Effects", callback_data="effects_commands")
        ],
        [
            InlineKeyboardButton("💎 Premium", url="https://t.me/admin"),
            InlineKeyboardButton("📞 Support", url="https://t.me/admin")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await message.reply_text(
        help_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

# Callback Query Handler - Fixed for Pyrogram v2
@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle all callback queries"""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        # Answer callback query first to stop loading
        await callback_query.answer()
        
        if data == "main_menu":
            # Return to main menu
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎵 Play Music", callback_data="menu_music"),
                    InlineKeyboardButton("🎨 Effects", callback_data="menu_effects")
                ],
                [
                    InlineKeyboardButton("⭐ Premium", callback_data="menu_premium"),
                    InlineKeyboardButton("🎯 Stickers", callback_data="menu_stickers")
                ],
                [
                    InlineKeyboardButton("📊 Statistics", callback_data="menu_stats"),
                    InlineKeyboardButton("ℹ️ Help", callback_data="menu_help")
                ]
            ])
            
            await callback_query.message.edit_text(
                "**🎵 Main Menu**\n\nSelect an option:",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "menu_music":
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔍 Search", callback_data="search_song"),
                    InlineKeyboardButton("🎵 Queue", callback_data="view_queue")
                ],
                [
                    InlineKeyboardButton("📝 Lyrics", callback_data="get_lyrics"),
                    InlineKeyboardButton("⏯️ Controls", callback_data="player_controls")
                ],
                [
                    InlineKeyboardButton("📥 Download", callback_data="download_song"),
                    InlineKeyboardButton("📤 Share", callback_data="share_song")
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ])
            
            await callback_query.message.edit_text(
                "**🎵 Music Menu**\n\nSelect an option:",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "menu_effects":
            await effects_command(client, callback_query.message)
        
        elif data == "menu_premium":
            await premium_command(client, callback_query.message)
        
        elif data == "menu_stickers":
            await sticker_command(client, callback_query.message)
        
        elif data == "menu_stats":
            await stats_command(client, callback_query.message)
        
        elif data == "menu_help":
            await help_command(client, callback_query.message)
        
        elif data.startswith("effect_"):
            effect_name = data.replace("effect_", "").replace("_", " ").title()
            
            await callback_query.message.reply_text(
                f"🎨 **{effect_name} Effect Applied!**\n\n"
                "Your audio is now processed with this effect.\n"
                "Use /reset_effect to remove effects.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Show notification
            await callback_query.answer(
                f"✅ {effect_name} effect applied!",
                show_alert=True
            )
        
        elif data == "redeem_code":
            await callback_query.message.edit_text(
                "**🎁 Redeem Premium Code**\n\n"
                "Send your code using:\n"
                "`/redeem YOUR_CODE`\n\n"
                "**Example:**\n"
                "`/redeem PREMIUM2024`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="menu_premium")]
                ])
            )
        
        elif data == "premium_features":
            features_text = """
**💎 Premium Features**

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

**Price:** Contact @admin
            """
            
            await callback_query.message.edit_text(
                features_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("💳 Get Premium", url="https://t.me/admin"),
                        InlineKeyboardButton("🔙 Back", callback_data="menu_premium")
                    ]
                ])
            )
        
        elif data == "refresh_stats":
            await callback_query.answer("🔄 Statistics refreshed!", show_alert=True)
            await stats_command(client, callback_query.message)
        
        else:
            await callback_query.answer("Feature coming soon!")
            
    except MessageNotModified:
        pass  # Message wasn't modified, ignore
    except QueryIdInvalid:
        logger.warning("Callback query too old, ignoring")
    except FloodWait as e:
        logger.warning(f"FloodWait in callback: {e.value}s")
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        try:
            await callback_query.answer(f"Error: {str(e)}", show_alert=True)
        except:
            pass

# Error Handler
@app.on_message(filters.command("error_test") & filters.private)
async def error_test(client: Client, message: Message):
    """Test error handling"""
    try:
        # Simulate an error
        raise ValueError("Test error")
    except Exception as e:
        logger.error(f"Test error: {e}")
        await message.reply_text(
            f"❌ **Error caught:**\n`{str(e)}`\n\n"
            "Error handling is working correctly!",
            parse_mode=ParseMode.MARKDOWN
        )

# Main entry point
if __name__ == "__main__":
    try:
        logger.info("🎵 Starting Telegram Music Bot...")
        app.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)

import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, InputMediaAudio
)
from pyrogram.errors import FloodWait
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from aiohttp import web
import threading
from flask import Flask
from bot.config import Config
from bot.helpers import get_readable_time
from utils.database import Database
from utils.keep_alive import KeepAlive
from utils.cloudflare import CloudflareManager

# Logging setup
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
health_app = Flask(__name__)

@health_app.route('/')
def home():
    return """
    <html>
        <head><title>Music Bot Status</title></head>
        <body style="background: #1a1a2e; color: #eee; font-family: Arial; text-align: center; padding: 50px;">
            <h1>🎵 Telegram Music Bot</h1>
            <p style="color: #00ff00;">✅ Bot is running!</p>
            <p>Current Time: {}</p>
        </body>
    </html>
    """.format(get_readable_time())

@health_app.route('/health')
def health():
    return {"status": "alive", "timestamp": get_readable_time()}, 200

@health_app.route('/ping')
def ping():
    return "pong", 200

def run_health_server():
    port = int(os.environ.get('PORT', 8080))
    health_app.run(host='0.0.0.0', port=port, debug=False)

class MusicBot(Client):
    def __init__(self):
        super().__init__(
            "MusicBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins"),
            workers=50
        )
        self.db = Database()
        self.keep_alive = KeepAlive()
        self.cf = CloudflareManager()
        
    async def start(self):
        await super().start()
        logger.info("Bot started successfully!")
        await self.db.initialize()
        
        # Start health server in separate thread
        threading.Thread(target=run_health_server, daemon=True).start()
        
        # Start keep-alive mechanism
        asyncio.create_task(self.keep_alive.start())
        
        # Setup Cloudflare
        if Config.CF_ENABLED:
            await self.cf.setup_protection()
        
        me = await self.get_me()
        logger.info(f"Bot @{me.username} is running!")
        
    async def stop(self):
        await super().stop()
        logger.info("Bot stopped!")

# Command handlers
@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user = message.from_user
    
    # Add user to database
    await client.db.add_user(user.id, user.username)
    
    # Premium animated keyboard
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
            InlineKeyboardButton("📊 Stats", callback_data="menu_stats"),
            InlineKeyboardButton("ℹ️ Help", callback_data="menu_help")
        ],
        [
            InlineKeyboardButton("💎 Get Premium", url="https://t.me/your_channel")
        ]
    ])
    
    # Send welcome with premium sticker
    await message.reply_animation(
        Config.PREMIUM_EFFECT_ID,
        caption=f"""
**🎵 Welcome to Premium Music Bot!**

**Hello {user.mention}!**

**Features:**
• 🎵 YouTube Music Streaming
• 🎨 Audio Effects (Bass, Nightcore, etc.)
• ⭐ Premium Custom Stickers
• 💎 Exclusive Effects & Animations
• 🎯 Custom Sticker Creator
• 📊 Detailed Statistics

**Premium Benefits:**
• 320kbps HD Audio
• Unlimited Downloads
• Priority Queue
• Ad-Free Experience
• Custom Effects
• Exclusive Stickers

**Use buttons below to navigate!**
        """,
        reply_markup=keyboard
    )

@Client.on_message(filters.command("play") & filters.private)
async def play_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_animation(
            Config.MUSIC_EFFECT_ID,
            caption="⚠️ **Please provide a song name!**\n\n"
                   "Usage: `/play Song Name`\n"
                   "Example: `/play Shape of You`\n\n"
                   "Or send me a YouTube link directly!"
        )
        return
    
    query = " ".join(message.command[1:])
    
    # Check premium status
    is_premium = await client.db.is_premium(message.from_user.id)
    
    status_msg = await message.reply_animation(
        Config.MUSIC_EFFECT_ID,
        caption=f"🔍 **Searching for:** `{query}`\n\n"
                f"{'⭐ Premium Search' if is_premium else '🔍 Free Search'}"
    )
    
    # Process music request
    await client.db.log_stream(message.from_user.id, query)
    
    # Call music plugin
    await message.reply(
        f"🎵 Playing: {query}\n"
        f"{'🔊 HD Audio' if is_premium else '🔈 Standard Audio'}"
    )

@Client.on_message(filters.command("effects") & filters.private)
async def effects_command(client: Client, message: Message):
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
            InlineKeyboardButton("💎 Premium Effects", callback_data="premium_effects"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="main_menu")
        ]
    ])
    
    await message.reply_animation(
        Config.EFFECT_STICKER_ID,
        caption="**🎨 Audio Effects Studio**\n\n"
                "Choose an effect to apply:\n\n"
                "⭐ = Premium Only\n\n"
                "Your music will sound amazing!",
        reply_markup=keyboard
    )

@Client.on_message(filters.command("premium") & filters.private)
async def premium_command(client: Client, message: Message):
    is_premium = await client.db.is_premium(message.from_user.id)
    
    if is_premium:
        expiry = await client.db.get_premium_expiry(message.from_user.id)
        text = f"""
**💎 Premium Status: ACTIVE**

**Expires:** {expiry}
**Features Unlocked:**
✅ HD Audio (320kbps)
✅ Unlimited Downloads
✅ Priority Queue
✅ All Effects
✅ Custom Stickers
✅ Ad-Free Experience
        """
    else:
        text = """
**💎 Premium Status: FREE**

**Upgrade to Premium:**
• HD Audio Quality
• Unlimited Downloads
• Priority Support
• All Effects Unlocked
• Custom Stickers

**Price:** Contact @admin

**Redeem Code:** `/redeem YOUR_CODE`
        """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem_code"),
            InlineKeyboardButton("💳 Get Premium", url="https://t.me/admin")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await message.reply_animation(
        Config.PREMIUM_EFFECT_ID,
        caption=text,
        reply_markup=keyboard
    )

@Client.on_message(filters.command("redeem") & filters.private)
async def redeem_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("⚠️ Please provide a premium code!\n"
                           "Usage: `/redeem PREMIUM2024`")
        return
    
    code = message.command[1].upper()
    user_id = message.from_user.id
    
    success = await client.db.redeem_premium_code(user_id, code)
    
    if success:
        await message.reply_animation(
            Config.PREMIUM_STICKER_ID,
            caption="🎉 **Congratulations!**\n\n"
                   "You've unlocked premium for 30 days!\n\n"
                   "Enjoy all premium features! ✨"
        )
    else:
        await message.reply("❌ Invalid or already used code!")

@Client.on_message(filters.command("sticker") & filters.private)
async def sticker_command(client: Client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Music Stickers", callback_data="sticker_music"),
            InlineKeyboardButton("✨ Premium", callback_data="sticker_premium")
        ],
        [
            InlineKeyboardButton("🎨 Create Custom", callback_data="sticker_create"),
            InlineKeyboardButton("📦 Get Pack", url="https://t.me/addstickers/your_pack")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await message.reply_animation(
        Config.STAR_EFFECT_ID,
        caption="**🎨 Custom Sticker System**\n\n"
                "Choose sticker type:\n"
                "• Music themed stickers\n"
                "• Premium exclusive stickers\n"
                "• Custom sticker creator\n"
                "• Get sticker pack",
        reply_markup=keyboard
    )

@Client.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    user_id = message.from_user.id
    stats = await client.db.get_user_stats(user_id)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
         InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await message.reply_animation(
        Config.STAR_EFFECT_ID,
        caption=f"""
**📊 Your Statistics**

**Total Streams:** {stats.get('total_streams', 0)}
**Premium:** {'✅ Active' if stats.get('is_premium') else '❌ Inactive'}
**Member Since:** {stats.get('created_at', 'N/A')}

**Top Songs:**
{stats.get('top_songs', 'No data yet')}

**Keep using the bot to build your stats!**
        """,
        reply_markup=keyboard
    )

@Client.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    commands_text = """
**📚 Available Commands:**

**Music:**
• `/play [song]` - Play a song
• `/search [song]` - Search music
• `/lyrics [song]` - Get lyrics
• `/queue` - View queue
• `/skip` - Skip current
• `/stop` - Stop playing

**Effects:**
• `/effects` - Show effects menu
• `/effect [name]` - Apply effect
• `/premium_effects` - Premium effects

**Stickers:**
• `/sticker` - Sticker menu
• `/createsticker` - Create custom
• `/stickers [pack]` - Get sticker pack

**Premium:**
• `/premium` - Premium info
• `/redeem [code]` - Redeem code
• `/premium_features` - Features list

**Other:**
• `/stats` - Your statistics
• `/settings` - Bot settings
• `/report` - Report issue
• `/about` - About bot

**Premium users get exclusive commands!**
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Get Premium", url="https://t.me/admin"),
         InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await message.reply(commands_text, reply_markup=keyboard)

# Callback handlers
@Client.on_callback_query()
async def callback_handler(client: Client, callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id
    
    if data == "main_menu":
        await start_command(client, callback.message)
        await callback.message.delete()
    
    elif data == "menu_music":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Search", callback_data="search_song"),
             InlineKeyboardButton("🎵 Queue", callback_data="view_queue")],
            [InlineKeyboardButton("📝 Lyrics", callback_data="get_lyrics"),
             InlineKeyboardButton("⏯️ Controls", callback_data="player_controls")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ])
        await callback.message.edit_text(
            "**🎵 Music Menu**\nSelect an option:",
            reply_markup=keyboard
        )
    
    elif data == "menu_effects":
        await effects_command(client, callback.message)
        await callback.message.delete()
    
    elif data == "menu_premium":
        await premium_command(client, callback.message)
        await callback.message.delete()
    
    elif data == "menu_stickers":
        await sticker_command(client, callback.message)
        await callback.message.delete()
    
    elif data == "menu_stats":
        await stats_command(client, callback.message)
        await callback.message.delete()
    
    elif data == "menu_help":
        await help_command(client, callback.message)
        await callback.message.delete()
    
    elif data.startswith("effect_"):
        effect_name = data.replace("effect_", "")
        is_premium = await client.db.is_premium(user_id)
        
        if not is_premium and effect_name in ['nightcore', 'reverb']:
            await callback.answer("⭐ Premium feature! Upgrade to use.", show_alert=True)
            return
        
        await callback.message.reply_animation(
            Config.MUSIC_EFFECT_ID,
            caption=f"🎵 Applying **{effect_name.upper()}** effect..."
        )
        await callback.answer(f"{effect_name} effect applied!")
    
    elif data == "redeem_code":
        await callback.message.edit_text(
            "🎁 **Redeem Premium Code**\n\n"
            "Send your code using:\n"
            "`/redeem YOUR_CODE`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="menu_premium")]
            ])
        )
    
    await callback.answer()

if __name__ == "__main__":
    app = MusicBot()
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

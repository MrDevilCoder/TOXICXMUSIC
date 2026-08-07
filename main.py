import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from config import BOT_TOKEN, OWNER_ID, PREMIUM_STICKER_ID, EFFECT_IDS
from plugins.music import MusicPlugin
from plugins.premium import PremiumPlugin
from plugins.stickers import StickerPlugin
from plugins.effects import EffectsPlugin
import json
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MusicBot:
    def __init__(self):
        self.music_plugin = MusicPlugin()
        self.premium_plugin = PremiumPlugin()
        self.sticker_plugin = StickerPlugin()
        self.effects_plugin = EffectsPlugin()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        # Check if user is premium
        is_premium = self.premium_plugin.check_premium(user_id)
        premium_status = "🌟 Premium User" if is_premium else "👤 Free User"
        
        welcome_text = f"""
🎵 **Welcome to Music Bot** 🎵

{premium_status}

**Commands:**
▶️ /play [song name/url] - Play music
⏸️ /pause - Pause current song
▶️ /resume - Resume playback
⏭️ /skip - Skip current song
🔄 /loop - Toggle loop mode
🔀 /shuffle - Shuffle queue
📊 /queue - Show current queue
🎵 /now - Show current playing
🔊 /volume [1-100] - Adjust volume
⏹️ /stop - Stop music & leave VC

**Premium Commands:**
🌟 /premium - Get premium features
🎨 /effects - Audio effects menu
🎭 /stickers - Premium stickers
💎 /customsticker - Create custom sticker

**Search:**
🔍 Just send song name to search
        """
        
        # Premium sticker for premium users
        if is_premium:
            await update.message.reply_sticker(PREMIUM_STICKER_ID)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=self.get_main_keyboard(is_premium)
        )
    
    def get_main_keyboard(self, is_premium=False):
        """Get main keyboard markup"""
        keyboard = [
            [
                InlineKeyboardButton("▶️ Play", callback_data="menu_play"),
                InlineKeyboardButton("⏯️ Controls", callback_data="menu_controls")
            ],
            [
                InlineKeyboardButton("📊 Queue", callback_data="menu_queue"),
                InlineKeyboardButton("🎵 Now Playing", callback_data="now_playing")
            ]
        ]
        
        if is_premium:
            keyboard.append([
                InlineKeyboardButton("🌟 Premium Features", callback_data="premium_menu")
            ])
        
        keyboard.append([
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
            InlineKeyboardButton("💎 Premium", callback_data="buy_premium")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if data == "menu_play":
            await query.message.reply_text(
                "🎵 Send me the song name or YouTube URL to play!\n\n"
                "Example: /play Believer"
            )
        
        elif data == "menu_controls":
            controls_text = """
🎮 **Music Controls:**

▶️ /play - Start playing
⏸️ /pause - Pause
▶️ /resume - Resume
⏭️ /skip - Skip track
🔄 /loop - Loop mode
🔀 /shuffle - Shuffle
🔊 /volume [1-100]
⏹️ /stop - Stop
            """
            await query.message.reply_text(controls_text, parse_mode='Markdown')
        
        elif data == "premium_menu":
            if self.premium_plugin.check_premium(user_id):
                await self.premium_plugin.show_premium_features(update, context)
            else:
                await query.message.reply_text(
                    "🌟 Premium required!\n"
                    "Use /premium to upgrade."
                )
        
        elif data == "buy_premium":
            await self.premium_plugin.premium_plans(update, context)
        
        elif data.startswith("effect_"):
            effect = data.replace("effect_", "")
            await self.effects_plugin.apply_effect(update, context, effect)
        
        elif data.startswith("sticker_"):
            sticker_type = data.replace("sticker_", "")
            await self.sticker_plugin.send_premium_sticker(update, context, sticker_type)
    
    async def text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (search for songs)"""
        text = update.message.text
        
        if not text.startswith('/'):
            await self.music_plugin.search_and_play(update, context, text)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Error handler"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )

def main():
    """Main function to run the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    bot = MusicBot()
    
    # Command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.start))
    
    # Music commands
    application.add_handler(CommandHandler("play", bot.music_plugin.play))
    application.add_handler(CommandHandler("pause", bot.music_plugin.pause))
    application.add_handler(CommandHandler("resume", bot.music_plugin.resume))
    application.add_handler(CommandHandler("skip", bot.music_plugin.skip))
    application.add_handler(CommandHandler("loop", bot.music_plugin.loop))
    application.add_handler(CommandHandler("shuffle", bot.music_plugin.shuffle))
    application.add_handler(CommandHandler("queue", bot.music_plugin.show_queue))
    application.add_handler(CommandHandler("now", bot.music_plugin.now_playing))
    application.add_handler(CommandHandler("volume", bot.music_plugin.volume))
    application.add_handler(CommandHandler("stop", bot.music_plugin.stop))
    
    # Premium commands
    application.add_handler(CommandHandler("premium", bot.premium_plugin.premium_plans))
    application.add_handler(CommandHandler("customsticker", bot.sticker_plugin.create_custom_sticker))
    application.add_handler(CommandHandler("effects", bot.effects_plugin.effects_menu))
    
    # Button handler
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    
    # Text handler for song search
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        bot.text_handler
    ))
    
    # Error handler
    application.add_error_handler(bot.error_handler)
    
    # Start bot with webhook for Render deployment
    PORT = int(os.environ.get('PORT', 8443))
    APP_URL = os.environ.get('APP_URL', '')
    
    if APP_URL:
        # Webhook mode (for deployment)
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{APP_URL}/{BOT_TOKEN}"
        )
    else:
        # Polling mode (for development)
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

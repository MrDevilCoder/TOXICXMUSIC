from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
from datetime import datetime, timedelta
import uuid

class PremiumPlugin:
    def __init__(self):
        self.premium_users = self.load_premium_users()
    
    def load_premium_users(self):
        """Load premium users from JSON file"""
        try:
            with open('data/premium_users.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_premium_users(self):
        """Save premium users to JSON file"""
        with open('data/premium_users.json', 'w') as f:
            json.dump(self.premium_users, f, indent=2)
    
    def check_premium(self, user_id):
        """Check if user is premium"""
        user_id = str(user_id)
        if user_id in self.premium_users:
            expiry = datetime.fromisoformat(self.premium_users[user_id]['expiry'])
            if expiry > datetime.now():
                return True
        return False
    
    def add_premium(self, user_id, duration_days=30):
        """Add premium to user"""
        user_id = str(user_id)
        expiry = datetime.now() + timedelta(days=duration_days)
        
        self.premium_users[user_id] = {
            'expiry': expiry.isoformat(),
            'purchase_date': datetime.now().isoformat(),
            'id': str(uuid.uuid4())
        }
        
        self.save_premium_users()
    
    async def premium_plans(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium plans"""
        user_id = update.effective_user.id
        
        if self.check_premium(user_id):
            expiry = datetime.fromisoformat(self.premium_users[str(user_id)]['expiry'])
            days_left = (expiry - datetime.now()).days
            
            await update.message.reply_text(
                f"🌟 **You are a Premium User!**\n\n"
                f"⏳ Days remaining: **{days_left}**\n\n"
                f"**Your Premium Features:**\n"
                f"✨ Custom Stickers\n"
                f"🎨 Audio Effects\n"
                f"🎵 Higher Quality Audio\n"
                f"📊 Extended Queue (1000 songs)\n"
                f"⏭️ Skip Vote Bypass\n"
                f"🔊 Volume Boost\n"
                f"🎭 Custom Effects ID\n"
                f"💎 Priority Support\n\n"
                f"Use /effects for audio effects\n"
                f"Use /customsticker for custom stickers",
                parse_mode='Markdown'
            )
        else:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💎 Monthly - $5.99", callback_data="premium_monthly"),
                    InlineKeyboardButton("💎 Yearly - $49.99", callback_data="premium_yearly")
                ],
                [
                    InlineKeyboardButton("🎁 Gift Premium", callback_data="premium_gift")
                ]
            ])
            
            await update.message.reply_text(
                "🌟 **Premium Subscription Plans**\n\n"
                "**Benefits:**\n"
                "✨ Custom Stickers\n"
                "🎨 Audio Effects (Bass, Nightcore, 8D, etc.)\n"
                "🎵 High Quality Audio (320kbps)\n"
                "📊 Extended Queue (1000 songs)\n"
                "⏭️ Skip Vote Bypass\n"
                "🔊 Volume Boost up to 200%\n"
                "🎭 Custom Effects ID\n"
                "💎 Priority Support\n\n"
                "Choose your plan:",
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    
    async def show_premium_features(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium features menu"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎨 Audio Effects", callback_data="effects_menu"),
                InlineKeyboardButton("🎭 Stickers", callback_data="stickers_menu")
            ],
            [
                InlineKeyboardButton("🎵 Custom Effect ID", callback_data="custom_effect"),
                InlineKeyboardButton("⭐ My Premium", callback_data="my_premium")
            ]
        ])
        
        await update.callback_query.message.reply_text(
            "🌟 **Premium Features Menu**\n\n"
            "Select a feature to use:",
            parse_mode='Markdown',
            reply_markup=keyboard
  )

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import STICKER_IDS
import random
from PIL import Image, ImageDraw, ImageFont
import io
import os

class StickerPlugin:
    def __init__(self):
        self.custom_stickers = {}
    
    async def send_premium_sticker(self, update: Update, context: ContextTypes.DEFAULT_TYPE, sticker_type):
        """Send premium sticker based on type"""
        sticker_ids = STICKER_IDS.get(sticker_type, [])
        
        if sticker_ids:
            sticker_id = random.choice(sticker_ids)
            try:
                await update.callback_query.message.reply_sticker(sticker_id)
            except Exception as e:
                await update.callback_query.message.reply_text(
                    f"❌ Error sending sticker: {str(e)}"
                )
        else:
            await update.callback_query.message.reply_text(
                "❌ No stickers available for this category!"
            )
    
    async def stickers_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show stickers menu"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎵 Music", callback_data="sticker_music"),
                InlineKeyboardButton("🌟 Premium", callback_data="sticker_premium")
            ],
            [
                InlineKeyboardButton("🎉 Party", callback_data="sticker_party"),
                InlineKeyboardButton("😌 Chill", callback_data="sticker_chill")
            ],
            [
                InlineKeyboardButton("🎨 Create Custom", callback_data="create_custom_sticker")
            ]
        ])
        
        await update.callback_query.message.reply_text(
            "🎭 **Premium Stickers Menu**\n\n"
            "Choose a category:",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    async def create_custom_sticker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create custom sticker from text or image"""
        if not context.args:
            await update.message.reply_text(
                "🎨 **Create Custom Sticker**\n\n"
                "Usage:\n"
                "/customsticker text [your text] - Create text sticker\n"
                "/customsticker image - Reply to an image to convert it to sticker"
            )
            return
        
        if context.args[0].lower() == 'text':
            text = ' '.join(context.args[1:])
            if text:
                sticker = await self.create_text_sticker(text)
                await update.message.reply_sticker(sticker)
            else:
                await update.message.reply_text("❌ Please provide text for the sticker!")
    
    async def create_text_sticker(self, text):
        """Create a text-based sticker"""
        # Create image with text
        img = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Add gradient background
        for i in range(512):
            color = (41, 128, 185, 200 - i//3)
            draw.line([(0, i), (512, i)], fill=color)
        
        # Add text
        font_size = 60
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Center text
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (512 - text_width) // 2
        y = (512 - text_height) // 2
        
        # Draw text with shadow
        draw.text((x+2, y+2), text, font=font, fill=(0, 0, 0, 100))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return img_byte_arr

  #!/usr/bin/env python3
"""Simple entry point - No module errors!"""

import os
import sys
import asyncio
import logging
from threading import Thread

# ===== IMPORTS =====
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== CONFIG =====
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
PORT = int(os.getenv("PORT", "8080"))

# ===== FLASK =====
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Bot Running!</h1>"

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False)

# ===== BOT =====
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Play", callback_data="play")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])
    
    await message.reply_text(
        f"**Welcome {message.from_user.first_name}!**\n\n"
        "I'm a Music Bot! Use buttons below.",
        reply_markup=keyboard
    )

@bot.on_message(filters.command("play"))
async def play(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage: `/play song name`")
        return
    
    query = " ".join(message.command[1:])
    await message.reply_text(f"🎵 Playing: {query}")

@bot.on_callback_query()
async def callbacks(client, callback):
    await callback.answer()
    
    if callback.data == "play":
        await callback.message.edit_text("Send: `/play song name`")
    elif callback.data == "help":
        await callback.message.edit_text("Commands: /start, /play, /help")

# ===== MAIN =====
async def main():
    Thread(target=run_flask, daemon=True).start()
    logger.info("Flask started")
    
    await bot.start()
    logger.info(f"Bot @{(await bot.get_me()).username} started!")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    if not all([API_ID, API_HASH, BOT_TOKEN]):
        logger.error("Missing API credentials!")
        sys.exit(1)
    
    asyncio.run(main())          

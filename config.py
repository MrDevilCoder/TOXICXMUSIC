import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
OWNER_ID = int(os.getenv('OWNER_ID', '123456789'))

# Premium Configuration
PREMIUM_PRICE_MONTHLY = 5.99
PREMIUM_PRICE_YEARLY = 49.99

# Sticker IDs
PREMIUM_STICKER_ID = 'CAACAgUAAxkBAA...'  # Replace with actual sticker ID
PREMIUM_STICKER_PACK = 'premium_music_stickers'

# Custom Sticker IDs by category
STICKER_IDS = {
    'music': [
        'CAACAgUAAxkBAA...',  # Replace with actual sticker IDs
        'CAACAgUAAxkBAA...',
    ],
    'premium': [
        'CAACAgUAAxkBAA...',
        'CAACAgUAAxkBAA...',
    ],
    'party': [
        'CAACAgUAAxkBAA...',
        'CAACAgUAAxkBAA...',
    ],
    'chill': [
        'CAACAgUAAxkBAA...',
        'CAACAgUAAxkBAA...',
    ]
}

# Effect IDs and configurations
EFFECT_IDS = {
    'bass': 'bass_boost_effect_id',
    'nightcore': 'nightcore_effect_id',
    '8d': '8d_audio_effect_id',
    'vaporwave': 'vaporwave_effect_id',
    'chipmunk': 'chipmunk_effect_id',
    'slow': 'slow_motion_effect_id',
    'reverb': 'reverb_effect_id',
    'echo': 'echo_effect_id'
}

# API Keys
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///music_bot.db')
REDIS_URL = os.getenv('REDIS_URL', '')

# Payment Configuration
PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN', '')

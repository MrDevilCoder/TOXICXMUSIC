import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram API
    API_ID = int(os.getenv("API_ID", "123456"))
    API_HASH = os.getenv("API_HASH", "your_api_hash")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
    
    # Bot Settings
    BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot_username")
    OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/bot.db")
    
    # Premium Settings
    PREMIUM_PRICE = "$5/month"
    PREMIUM_CODES = os.getenv("PREMIUM_CODES", "PREMIUM2024,VIPMUSIC,ELITE").split(",")
    
    # Custom Sticker IDs
    PREMIUM_STICKER_ID = "CAACAgIAAxkBAAEL..."
    MUSIC_STICKER_ID = "CAACAgIAAxkBAAEL..."
    EFFECT_STICKER_ID = "CAACAgIAAxkBAAEL..."
    
    # Effect Animation IDs (Custom animated emoji IDs)
    MUSIC_EFFECT_ID = "CgACAgQAAxkBAAEL..."
    FIRE_EFFECT_ID = "CgACAgQAAxkBAAEL..."
    STAR_EFFECT_ID = "CgACAgQAAxkBAAEL..."
    HEART_EFFECT_ID = "CgACAgQAAxkBAAEL..."
    PREMIUM_EFFECT_ID = "CgACAgQAAxkBAAEL..."
    BASS_EFFECT_ID = "CgACAgQAAxkBAAEL..."
    NIGHTCORE_EFFECT_ID = "CgACAgQAAxkBAAEL..."
    
    # Sticker Sets
    PREMIUM_STICKER_SET = "PremiumMusicStickers"
    MUSIC_STICKER_SET = "MusicBotStickers"
    
    # App URLs
    APP_URL = os.getenv("APP_URL", "https://your-app.onrender.com")
    WORKER_URL = os.getenv("WORKER_URL", "https://your-worker.workers.dev")
    
    # Cloudflare
    CF_ENABLED = os.getenv("CF_ENABLED", "False").lower() == "true"
    CF_API_TOKEN = os.getenv("CF_API_TOKEN", "")
    CF_ZONE_ID = os.getenv("CF_ZONE_ID", "")
    CF_EMAIL = os.getenv("CF_EMAIL", "")
    
    # YouTube API
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
    
    # Download Settings
    MAX_DOWNLOAD_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_FORMATS = ["mp3", "m4a", "ogg"]
    DEFAULT_QUALITY = "192"  # 192kbps
    PREMIUM_QUALITY = "320"  # 320kbps
    
    # Keep Alive Settings
    KEEP_ALIVE_INTERVAL = 600  # 10 minutes
    PING_URLS = [
        "https://your-app.onrender.com/health",
        "https://your-app.up.railway.app/health",
        "https://your-app.koyeb.app/health"
    ]
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE = 30
    MAX_PLAYLIST_SIZE = 50
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "bot.log"

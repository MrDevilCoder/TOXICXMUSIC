import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from utils.youtube import YouTubeDownloader
from bot.config import Config

class MusicPlayer:
    def __init__(self):
        self.downloader = YouTubeDownloader()
        self.active_streams = {}
        
    async def search_and_play(self, message: Message, query: str):
        """Search YouTube and play music"""
        user_id = message.from_user.id
        is_premium = await message._client.db.is_premium(user_id)
        
        # Status message with animation
        status = await message.reply_animation(
            Config.MUSIC_EFFECT_ID,
            caption=f"🔍 **Searching:** `{query}`\n{'⭐ Premium Search' if is_premium else '🔍 Free Search'}"
        )
        
        try:
            # Search YouTube
            video_info = await self.downloader.search(query)
            
            if not video_info:
                await status.edit_caption("❌ **No results found!**\nTry different keywords.")
                return
            
            # Update status
            await status.edit_caption(
                f"🎵 **Found:** {video_info['title'][:50]}\n"
                f"📊 Duration: {video_info['duration']}s\n"
                f"👤 Artist: {video_info.get('uploader', 'Unknown')}\n\n"
                f"⏳ Downloading..."
            )
            
            # Download audio
            audio_path, info = await self.downloader.download_audio(
                video_info['url'],
                quality=Config.PREMIUM_QUALITY if is_premium else Config.DEFAULT_QUALITY
            )
            
            if not audio_path:
                await status.edit_caption("❌ **Download failed!**")
                return
            
            # Create player controls
            controls = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏸️ Pause", callback_data="player_pause"),
                    InlineKeyboardButton("▶️ Resume", callback_data="player_resume"),
                    InlineKeyboardButton("⏹️ Stop", callback_data="player_stop")
                ],
                [
                    InlineKeyboardButton("🔁 Loop", callback_data="player_loop"),
                    InlineKeyboardButton("🔀 Shuffle", callback_data="player_shuffle"),
                    InlineKeyboardButton("📝 Lyrics", callback_data=f"lyrics_{video_info['title']}")
                ],
                [
                    InlineKeyboardButton("🎨 Effects", callback_data="player_effects"),
                    InlineKeyboardButton("📤 Share", callback_data="player_share")
                ]
            ])
            
            # Send the audio file
            await message.reply_audio(
                audio=audio_path,
                title=video_info.get('title', 'Unknown'),
                performer=video_info.get('uploader', 'Unknown'),
                duration=int(video_info.get('duration', 0)),
                caption=f"""
**🎵 Now Playing**

**Title:** {video_info.get('title', 'Unknown')}
**Artist:** {video_info.get('uploader', 'Unknown')}
**Duration:** {video_info.get('duration', 0)}s
**Quality:** {'🔊 HD 320kbps' if is_premium else '🔈 Standard 192kbps'}

{'⭐ **Premium Stream**' if is_premium else '🔈 **Free Stream**'}
                """,
                reply_markup=controls,
                thumb=video_info.get('thumbnail')
            )
            
            # Log stream
            await message._client.db.log_stream(
                user_id,
                video_info['title'],
                video_info['url'],
                int(video_info.get('duration', 0)),
                Config.PREMIUM_QUALITY if is_premium else Config.DEFAULT_QUALITY
            )
            
            # Clean up
            await status.delete()
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
        except Exception as e:
            await status.edit_caption(f"❌ **Error:** `{str(e)}`\n\nPlease try again!")
    
    async def get_lyrics(self, message: Message, song_name: str):
        """Fetch lyrics for a song"""
        try:
            import lyricsgenius
            genius = lyricsgenius.Genius(Config.GENIUS_API_KEY)
            song = genius.search_song(song_name)
            
            if song:
                lyrics = song.lyrics[:4000]  # Telegram message limit
                await message.reply(
                    f"**📝 Lyrics for:** {song_name}\n\n{lyrics}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔍 Full Lyrics", url=song.url)]
                    ])
                )
            else:
                await message.reply("❌ Lyrics not found!")
        except Exception as e:
            await message.reply("❌ Error fetching lyrics!")

# Plugin handlers
@Client.on_message(filters.command("play") & filters.private)
async def play_handler(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("⚠️ Usage: `/play Song Name`")
        return
    
    query = " ".join(message.command[1:])
    player = MusicPlayer()
    await player.search_and_play(message, query)

@Client.on_message(filters.command("search") & filters.private)
async def search_handler(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("⚠️ Usage: `/search Song Name`")
        return
    
    query = " ".join(message.command[1:])
    player = MusicPlayer()
    
    results = await player.downloader.search(query, max_results=5)
    
    if not results:
        await message.reply("❌ No results found!")
        return
    
    text = "**🔍 Search Results:**\n\n"
    for i, result in enumerate(results, 1):
        text += f"{i}. **{result['title'][:50]}**\n"
        text += f"   👤 {result.get('uploader', 'Unknown')}\n"
        text += f"   ⏱️ {result.get('duration', 0)}s\n\n"
    
    text += "Reply with the number to play!"
    await message.reply(text)

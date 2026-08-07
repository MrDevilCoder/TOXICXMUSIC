import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import yt_dlp
import os
from collections import deque
import uuid
from utils.youtube import search_youtube

class MusicQueue:
    def __init__(self):
        self.queues = {}
        self.now_playing = {}
        self.loop_modes = {}  # 0=off, 1=song, 2=queue
    
    def get_queue(self, chat_id):
        if chat_id not in self.queues:
            self.queues[chat_id] = deque()
        return self.queues[chat_id]
    
    def add_to_queue(self, chat_id, song_info):
        queue = self.get_queue(chat_id)
        queue.append(song_info)
        return len(queue)
    
    def get_current_song(self, chat_id):
        return self.now_playing.get(chat_id)
    
    def clear_queue(self, chat_id):
        if chat_id in self.queues:
            self.queues[chat_id].clear()

class MusicPlugin:
    def __init__(self):
        self.queue = MusicQueue()
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
    
    async def play(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play music command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a song name or URL!\n"
                "Example: /play Believer"
            )
            return
        
        query = ' '.join(context.args)
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # Send searching message
        status_msg = await update.message.reply_text(
            f"🔍 Searching for: **{query}**...",
            parse_mode='Markdown'
        )
        
        try:
            # Search for the song
            song_info = await search_youtube(query)
            
            if not song_info:
                await status_msg.edit_text("❌ No results found!")
                return
            
            # Add to queue
            position = self.queue.add_to_queue(chat_id, {
                'info': song_info,
                'requested_by': user_id,
                'id': str(uuid.uuid4())
            })
            
            # Create response keyboard
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏭️ Skip", callback_data="skip"),
                    InlineKeyboardButton("⏸️ Pause", callback_data="pause")
                ],
                [
                    InlineKeyboardButton("🔊 Volume", callback_data="volume_menu"),
                    InlineKeyboardButton("🔄 Loop", callback_data="loop_toggle")
                ]
            ])
            
            # Edit status message
            await status_msg.edit_text(
                f"✅ **Added to Queue** #{position}\n\n"
                f"🎵 **{song_info['title']}**\n"
                f"👤 **Artist:** {song_info.get('artist', 'Unknown')}\n"
                f"⏱️ **Duration:** {song_info.get('duration', 'N/A')}\n"
                f"🔗 [Watch on YouTube]({song_info['url']})",
                parse_mode='Markdown',
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            # If this is the only song, start playing
            if position == 1:
                await self.start_playing(update, context, chat_id)
            
        except Exception as e:
            await status_msg.edit_text(f"❌ Error: {str(e)}")
    
    async def start_playing(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id):
        """Start playing the first song in queue"""
        # This would connect to voice chat and start streaming
        # Implementation depends on your voice chat library (py-tgcalls, etc.)
        pass
    
    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Pause current playback"""
        await update.message.reply_text("⏸️ Playback paused")
    
    async def resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Resume playback"""
        await update.message.reply_text("▶️ Playback resumed")
    
    async def skip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Skip current song"""
        await update.message.reply_text("⏭️ Skipped to next song")
    
    async def loop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle loop mode"""
        chat_id = update.effective_chat.id
        modes = {0: "Off", 1: "Song", 2: "Queue"}
        
        current = self.queue.loop_modes.get(chat_id, 0)
        new_mode = (current + 1) % 3
        self.queue.loop_modes[chat_id] = new_mode
        
        await update.message.reply_text(f"🔄 Loop mode: **{modes[new_mode]}**", parse_mode='Markdown')
    
    async def shuffle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Shuffle the queue"""
        import random
        chat_id = update.effective_chat.id
        queue = self.queue.get_queue(chat_id)
        
        if len(queue) > 1:
            queue_list = list(queue)
            random.shuffle(queue_list)
            self.queue.queues[chat_id] = deque(queue_list)
            await update.message.reply_text("🔀 Queue shuffled!")
        else:
            await update.message.reply_text("📊 Not enough songs in queue to shuffle!")
    
    async def show_queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current queue"""
        chat_id = update.effective_chat.id
        queue = self.queue.get_queue(chat_id)
        
        if not queue:
            await update.message.reply_text("📊 Queue is empty!")
            return
        
        queue_text = "📊 **Current Queue:**\n\n"
        for i, song in enumerate(queue, 1):
            info = song['info']
            queue_text += f"{i}. **{info['title']}**\n"
            queue_text += f"   ⏱️ {info.get('duration', 'N/A')}\n\n"
        
        await update.message.reply_text(queue_text, parse_mode='Markdown')
    
    async def now_playing(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show currently playing song"""
        chat_id = update.effective_chat.id
        current = self.queue.get_current_song(chat_id)
        
        if current:
            await update.message.reply_text(
                f"🎵 **Now Playing:**\n\n"
                f"**{current['info']['title']}**\n"
                f"⏱️ {current['info'].get('duration', 'N/A')}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Nothing is playing right now!")
    
    async def volume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Adjust volume"""
        if not context.args:
            await update.message.reply_text("🔊 Current volume: 100%")
            return
        
        try:
            vol = int(context.args[0])
            if 0 <= vol <= 100:
                await update.message.reply_text(f"🔊 Volume set to: **{vol}%**", parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Volume must be between 0 and 100!")
        except ValueError:
            await update.message.reply_text("❌ Please provide a valid number!")
    
    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop music and leave voice chat"""
        chat_id = update.effective_chat.id
        self.queue.clear_queue(chat_id)
        await update.message.reply_text("⏹️ Stopped playing and cleared queue!")
    
    async def search_and_play(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Handle text search for songs"""
        context.args = [query]
        await self.play(update, context)

# Search function in utils/youtube.py

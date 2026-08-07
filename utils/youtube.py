import yt_dlp
import asyncio
import os
from typing import Optional, Dict, List
from bot.config import Config

class YouTubeDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': Config.DEFAULT_QUALITY,
            }],
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None
        }
        
    async def search(self, query: str, max_results: int = 1) -> Optional[Dict]:
        """Search YouTube and return video info"""
        search_opts = {
            **self.ydl_opts,
            'format': 'best',
            'noplaylist': True,
            'quiet': True
        }
        
        if max_results > 1:
            search_opts['extract_flat'] = True
            
        try:
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                
                if max_results == 1:
                    if 'entries' in info:
                        info = info['entries'][0]
                    return {
                        'title': info.get('title', 'Unknown'),
                        'url': info.get('webpage_url', ''),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', 'Unknown'),
                        'thumbnail': info.get('thumbnail', ''),
                        'view_count': info.get('view_count', 0),
                        'like_count': info.get('like_count', 0)
                    }
                else:
                    results = []
                    if 'entries' in info:
                        for entry in info['entries'][:max_results]:
                            results.append({
                                'title': entry.get('title', 'Unknown'),
                                'url': entry.get('url', ''),
                                'duration': entry.get('duration', 0),
                                'uploader': entry.get('uploader', 'Unknown')
                            })
                    return results
                    
        except Exception as e:
            print(f"Search error: {e}")
            return None
    
    async def download_audio(self, url: str, quality: str = None) -> tuple:
        """Download audio from YouTube"""
        if not quality:
            quality = Config.DEFAULT_QUALITY
            
        download_opts = {
            **self.ydl_opts,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'outtmpl': 'downloads/%(title)s_%(id)s.%(ext)s',
            'restrictfilenames': True,
            'max_filesize': Config.MAX_DOWNLOAD_SIZE,
            'quiet': True
        }
        
        os.makedirs('downloads', exist_ok=True)
        
        try:
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                mp3_filename = filename.rsplit('.', 1)[0] + '.mp3'
                
                if os.path.exists(mp3_filename):
                    return mp3_filename, info
                return None, None
                
        except Exception as e:
            print(f"Download error: {e}")
            return None, None
    
    async def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'description': info.get('description', '')[:200],
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': info.get('webpage_url', '')
                }
        except Exception as e:
            print(f"Info error: {e}")
            return None

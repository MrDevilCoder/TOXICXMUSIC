import aiohttp
from config import YOUTUBE_API_KEY
import re

async def search_youtube(query, max_results=1):
    """Search YouTube for videos"""
    if YOUTUBE_API_KEY:
        return await search_with_api(query, max_results)
    else:
        return await search_without_api(query, max_results)

async def search_with_api(query, max_results=1):
    """Search using YouTube Data API"""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': max_results,
        'key': YOUTUBE_API_KEY
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                results = []
                
                for item in data.get('items', []):
                    video_id = item['id']['videoId']
                    snippet = item['snippet']
                    
                    results.append({
                        'title': snippet['title'],
                        'artist': snippet['channelTitle'],
                        'url': f"https://youtube.com/watch?v={video_id}",
                        'video_id': video_id,
                        'thumbnail': snippet['thumbnails']['high']['url'],
                        'duration': 'Unknown'  # Would need separate API call
                    })
                
                return results[0] if results else None
    return None

async def search_without_api(query, max_results=1):
    """Search without API (web scraping fallback)"""
    search_url = f"https://www.youtube.com/results?search_query={query}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            if response.status == 200:
                html = await response.text()
                
                # Extract video IDs
                video_ids = re.findall(r'watch\?v=(\S{11})', html)
                
                if video_ids:
                    video_id = video_ids[0]
                    # Get title
                    title_match = re.findall(r'"title":{"runs":\[{"text":"([^"]+)"', html)
                    title = title_match[0] if title_match else "Unknown Title"
                    
                    return {
                        'title': title,
                        'artist': 'Unknown',
                        'url': f"https://youtube.com/watch?v={video_id}",
                        'video_id': video_id,
                        'thumbnail': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                        'duration': 'Unknown'
                    }
    return None

def format_duration(seconds):
    """Format duration from seconds to mm:ss"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

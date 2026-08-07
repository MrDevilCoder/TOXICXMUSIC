import aiohttp
import asyncio
import logging
from datetime import datetime
from bot.config import Config

logger = logging.getLogger(__name__)

class KeepAlive:
    def __init__(self):
        self.urls = Config.PING_URLS
        self.interval = Config.KEEP_ALIVE_INTERVAL
        self.running = False
        
    async def ping_url(self, session: aiohttp.ClientSession, url: str):
        """Ping a single URL"""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"✅ Keep-alive ping successful: {url}")
                    return True
                else:
                    logger.warning(f"⚠️ Ping failed ({response.status}): {url}")
                    return False
        except Exception as e:
            logger.error(f"❌ Ping error for {url}: {str(e)}")
            return False
    
    async def ping_all_services(self):
        """Ping all configured services"""
        async with aiohttp.ClientSession() as session:
            tasks = [self.ping_url(session, url) for url in self.urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for r in results if r is True)
            logger.info(f"Keep-alive: {successful}/{len(self.urls)} services responded")
    
    async def start(self):
        """Start the keep-alive mechanism"""
        self.running = True
        logger.info(f"🔄 Keep-alive started (interval: {self.interval}s)")
        
        while self.running:
            try:
                await self.ping_all_services()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Keep-alive error: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    def stop(self):
        """Stop the keep-alive mechanism"""
        self.running = False
        logger.info("Keep-alive stopped")

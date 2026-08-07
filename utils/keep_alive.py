#!/usr/bin/env python3
"""
Keep-alive mechanism for 24/7 operation
"""

import aiohttp
import asyncio
import logging
from typing import List, Optional
import os

logger = logging.getLogger(__name__)

class KeepAlive:
    """Keep services alive with periodic pings"""
    
    def __init__(self, urls: Optional[List[str]] = None):
        self.urls = urls or []
        self.interval = int(os.getenv('KEEP_ALIVE_INTERVAL', 600))  # 10 minutes
        self.running = False
        
    def add_url(self, url: str):
        """Add URL to ping list"""
        if url not in self.urls:
            self.urls.append(url)
    
    async def ping_url(self, session: aiohttp.ClientSession, url: str) -> bool:
        """Ping a single URL"""
        try:
            async with session.get(f"{url}/health", timeout=30) as response:
                if response.status == 200:
                    logger.debug(f"✅ Ping successful: {url}")
                    return True
                else:
                    logger.warning(f"⚠️ Ping failed ({response.status}): {url}")
                    return False
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Timeout pinging: {url}")
            return False
        except aiohttp.ClientError as e:
            logger.error(f"❌ Connection error for {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error pinging {url}: {e}")
            return False
    
    async def ping_all(self):
        """Ping all configured URLs"""
        if not self.urls:
            logger.warning("No URLs configured for keep-alive")
            return
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.ping_url(session, url) for url in self.urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for r in results if r is True)
            logger.info(f"Keep-alive: {successful}/{len(self.urls)} services alive")
    
    async def start(self):
        """Start keep-alive loop"""
        self.running = True
        logger.info(f"🔄 Keep-alive started (interval: {self.interval}s)")
        
        while self.running:
            try:
                await self.ping_all()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Keep-alive error: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        """Stop keep-alive"""
        self.running = False
        logger.info("Keep-alive stopped")

# Self-ping function for single service
async def self_ping():
    """Self-ping function for the current service"""
    app_url = os.getenv('APP_URL')
    if not app_url:
        logger.warning("APP_URL not set for self-ping")
        return
    
    keep_alive = KeepAlive([app_url])
    await keep_alive.start()

import asyncio
import aiohttp
from bot.config import Config
import logging

logger = logging.getLogger(__name__)

class CloudflareManager:
    def __init__(self):
        self.api_token = Config.CF_API_TOKEN
        self.zone_id = Config.CF_ZONE_ID
        self.email = Config.CF_EMAIL
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    async def setup_protection(self):
        """Setup Cloudflare protection"""
        await self.create_firewall_rules()
        await self.enable_bot_management()
        await self.setup_rate_limiting()
        logger.info("Cloudflare protection configured")
    
    async def create_firewall_rules(self):
        """Create firewall rules for bot protection"""
        rules = [
            {
                "description": "Block malicious bots",
                "expression": '(cf.client.bot)',
                "action": "block"
            },
            {
                "description": "Rate limit API endpoints",
                "expression": '(http.request.uri.path eq "/webhook")',
                "action": "managed_challenge"
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for rule in rules:
                try:
                    url = f"{self.base_url}/zones/{self.zone_id}/firewall/rules"
                    async with session.post(url, json=rule, headers=self.headers) as resp:
                        if resp.status == 200:
                            logger.info(f"Firewall rule created: {rule['description']}")
                except Exception as e:
                    logger.error(f"Firewall rule error: {e}")
    
    async def enable_bot_management(self):
        """Enable bot management"""
        try:
            url = f"{self.base_url}/zones/{self.zone_id}/bot_management"
            data = {
                "fight_mode": True,
                "enable_js": True
            }
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=data, headers=self.headers) as resp:
                    if resp.status == 200:
                        logger.info("Bot management enabled")
        except Exception as e:
            logger.error(f"Bot management error: {e}")
    
    async def setup_rate_limiting(self):
        """Setup rate limiting rules"""
        try:
            url = f"{self.base_url}/zones/{self.zone_id}/rate_limits"
            data = {
                "description": "API Rate Limit",
                "match": {
                    "request": {
                        "methods": ["POST"],
                        "url": "*.yourdomain.com/api/*"
                    }
                },
                "period": 60,
                "threshold": 30,
                "action": {
                    "mode": "simulate",
                    "timeout": 60
                }
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=self.headers) as resp:
                    if resp.status == 200:
                        logger.info("Rate limiting configured")
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
    
    async def purge_cache(self):
        """Purge Cloudflare cache"""
        try:
            url = f"{self.base_url}/zones/{self.zone_id}/purge_cache"
            data = {"purge_everything": True}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=self.headers) as resp:
                    if resp.status == 200:
                        logger.info("Cache purged successfully")
                        return True
            return False
        except Exception as e:
            logger.error(f"Cache purge error: {e}")
            return False

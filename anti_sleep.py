import aiohttp
import asyncio
import os
from datetime import datetime

class AntiSleep:
    def __init__(self, app_url):
        self.app_url = app_url
        self.is_running = False
    
    async def ping_server(self):
        """Ping the server to keep it alive"""
        async with aiohttp.ClientSession() as session:
            while self.is_running:
                try:
                    async with session.get(f"{self.app_url}/health") as response:
                        if response.status == 200:
                            print(f"[{datetime.now()}] Ping successful - Status: {response.status}")
                        else:
                            print(f"[{datetime.now()}] Ping failed - Status: {response.status}")
                except Exception as e:
                    print(f"[{datetime.now()}] Ping error: {str(e)}")
                
                # Wait 5 minutes before next ping
                await asyncio.sleep(300)
    
    def start(self):
        """Start anti-sleep mechanism"""
        self.is_running = True
        asyncio.create_task(self.ping_server())
    
    def stop(self):
        """Stop anti-sleep mechanism"""
        self.is_running = False

# External ping service (use cron-job.org or uptimerobot.com)
# Add this URL to external monitoring: https://your-app.onrender.com/health

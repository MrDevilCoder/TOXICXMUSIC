import aiohttp
import asyncio
import os
from datetime import datetime

async def keep_alive():
    """Cron job to keep services alive"""
    urls = [
        os.getenv("APP_URL", "https://your-app.onrender.com"),
        # Add more URLs for multiple deployments
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(f"{url}/health") as response:
                    status = "✅" if response.status == 200 else "❌"
                    print(f"{status} {url}: {response.status}")
            except Exception as e:
                print(f"❌ {url}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(keep_alive())

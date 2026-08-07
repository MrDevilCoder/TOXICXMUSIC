import asyncio
from bot.main import MusicBot
from utils.keep_alive import KeepAlive
import logging

logger = logging.getLogger(__name__)

async def main():
    """Worker process for background tasks"""
    keep_alive = KeepAlive()
    
    # Start keep-alive
    keep_alive_task = asyncio.create_task(keep_alive.start())
    
    # Additional background tasks
    cleanup_task = asyncio.create_task(cleanup_old_files())
    stats_task = asyncio.create_task(update_statistics())
    
    try:
        await asyncio.gather(
            keep_alive_task,
            cleanup_task,
            stats_task
        )
    except KeyboardInterrupt:
        logger.info("Worker stopped")
    except Exception as e:
        logger.error(f"Worker error: {e}")

async def cleanup_old_files():
    """Clean up old download files"""
    import os
    import time
    
    while True:
        try:
            downloads_dir = 'downloads'
            if os.path.exists(downloads_dir):
                current_time = time.time()
                for file in os.listdir(downloads_dir):
                    file_path = os.path.join(downloads_dir, file)
                    # Remove files older than 1 hour
                    if current_time - os.path.getmtime(file_path) > 3600:
                        os.remove(file_path)
                        logger.info(f"Cleaned up: {file}")
            await asyncio.sleep(1800)  # Run every 30 minutes
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            await asyncio.sleep(300)

async def update_statistics():
    """Update bot statistics periodically"""
    while True:
        try:
            # Statistics update logic here
            logger.info("Statistics updated")
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Stats update error: {e}")
            await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())

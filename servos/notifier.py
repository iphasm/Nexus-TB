"""
Nexus Trading Bot - Async Telegram Notifier
Migrated from synchronous requests to async aiohttp.
"""
import os
import aiohttp
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables
load_dotenv()

# Import config constants
try:
    from system_directive import TELEGRAM_API_BASE, HTTP_TIMEOUT
except ImportError:
    # Fallback if system_directive not available
    TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"
    HTTP_TIMEOUT = 10


async def send_telegram_alert(message: str, session: Optional[aiohttp.ClientSession] = None):
    """
    Async function to send a message via Telegram Bot API.
    Requires TELEGRAM_TOKEN and TELEGRAM_CHAT_ID in .env file.
    
    Args:
        message: Message text to send
        session: Optional aiohttp session (creates new if not provided)
    """
    token = os.getenv('TELEGRAM_TOKEN')
    chat_ids_str = os.getenv('TELEGRAM_CHAT_ID', '')
    chat_ids = [id.strip() for id in chat_ids_str.split(',') if id.strip()]
    
    if not token or not chat_ids:
        print("Error: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not found in environment variables.")
        return

    url = TELEGRAM_API_BASE.format(token=token)
    
    # Use provided session or create new one
    should_close = session is None
    if session is None:
        session = aiohttp.ClientSession()
    
    try:
        for chat_id in chat_ids:
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            try:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT)) as response:
                    response.raise_for_status()  # Raise exception for 4xx/5xx errors
            except aiohttp.ClientError as e:
                print(f"Error sending Telegram alert to {chat_id}: {e}")
    finally:
        if should_close and session:
            await session.close()


# Backward compatibility: Sync wrapper (deprecated, use async version)
def send_telegram_alert_sync(message: str):
    """
    DEPRECATED: Synchronous wrapper for backward compatibility.
    Use send_telegram_alert() async version instead.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create task
            asyncio.create_task(send_telegram_alert(message))
        else:
            # If no loop running, run it
            loop.run_until_complete(send_telegram_alert(message))
    except RuntimeError:
        # No event loop, create new one
        asyncio.run(send_telegram_alert(message))



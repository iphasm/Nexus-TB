import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_telegram_alert(message: str):
    """
    Sends a message via Telegram Bot API.
    Requires TELEGRAM_TOKEN and TELEGRAM_CHAT_ID in .env file.
    """
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("Error: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not found in environment variables.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status() # Raise exception for 4xx/5xx errors
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram alert: {e}")
    except Exception as e:
        print(f"Unexpected error in notifier: {e}")

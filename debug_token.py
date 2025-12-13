import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')

print(f"Testing Token: {token[:6]}...{token[-4:]}")

url = f"https://api.telegram.org/bot{token}/getMe"

try:
    print(f"Sending request to {url.replace(token, 'HIDDEN')}...")
    r = requests.get(url, timeout=10)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Request Failed: {e}")

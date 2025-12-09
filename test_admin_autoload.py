import os
import shutil
import json
from utils.trading_manager import SessionManager

TEST_DB = 'data/test_sessions_admin.json'

def cleanup():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_admin_autoload():
    cleanup()
    
    # Simulate Env Vars
    os.environ['TELEGRAM_ADMIN_ID'] = '999888777'
    os.environ['BINANCE_API_KEY'] = 'env_api_key'
    os.environ['BINANCE_SECRET'] = 'env_secret'
    
    print("TEST: Initializing SessionManager with Env Vars...")
    sm = SessionManager(data_file=TEST_DB)
    
    # Check if admin session was auto-created
    admin_session = sm.get_session('999888777')
    
    if admin_session:
        print(f"✅ Admin Session Found: {admin_session.chat_id}")
        print(f"   Key: {admin_session.api_key}")
        
        assert admin_session.api_key == 'env_api_key'
        assert admin_session.api_secret == 'env_secret'
        print("✅ Keys match environment variables.")
    else:
        print("❌ Admin Session NOT found.")
        exit(1)

    cleanup()

if __name__ == "__main__":
    test_admin_autoload()

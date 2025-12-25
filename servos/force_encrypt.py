import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servos.db import load_all_sessions, save_all_sessions
from servos.security import get_cipher
import dotenv

def force_encrypt_all():
    """
    Loads all sessions (decrypting or reading plaintext)
    and immediately saves them back (encrypting everything).
    """
    dotenv.load_dotenv()
    
    if not get_cipher():
        print("❌ ENCRYPTION_KEY not found. Cannot encrypt.")
        return False
        
    print("⏳ Loading all sessions...")
    sessions = load_all_sessions()
    
    if not sessions:
        print("⚠️ No sessions found or DB connection failed.")
        return False
        
    print(f"🔍 Found {len(sessions)} sessions. Re-saving to force encryption...")
    
    # save_all_sessions handles encryption automatically via utils/db.py hooks
    if save_all_sessions(sessions):
        print("✅ Success! All data is now encrypted.")
        return True
    else:
        print("❌ Failed to save sessions.")
        return False

if __name__ == "__main__":
    force_encrypt_all()


import os
import argparse
import sys
from cryptography.fernet import Fernet # type: ignore
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servos.db import get_connection

def decrypt_with_cipher(cipher, text):
    if not text: return text
    if not cipher: return text # Assume plaintext if no old cipher
    try:
        return cipher.decrypt(text.encode('utf-8')).decode('utf-8')
    except:
        return text # Fail open (assume plaintext)

def rotate_database_keys(new_key_str):
    """
    Rotates encryption keys for the entire database.
    1. Reads OLD_KEY from env.
    2. Decrypts all data.
    3. Encrypts with NEW_KEY.
    4. Updates DB.
    """
    load_dotenv()
    old_key_str = os.getenv('ENCRYPTION_KEY')
    
    print(f"Old Key (Env): {'***' + old_key_str[-4:] if old_key_str else 'None (Plaintext Mode)'}")
    print(f"New Key (Arg): {'***' + new_key_str[-4:]}")
    
    old_cipher = Fernet(old_key_str) if old_key_str else None
    try:
        new_cipher = Fernet(new_key_str)
    except Exception as e:
        print(f"❌ Invalid New Key: {e}")
        return

    conn = get_connection()
    if not conn:
        print("❌ Cannot connect to DB.")
        return

    try:
        success_count = 0
        fail_count = 0
        
        with conn.cursor() as cur:
            # 1. Fetch All Sessions
            cur.execute("SELECT chat_id, api_key, api_secret FROM sessions")
            rows = cur.fetchall()
            
            print(f"Processing {len(rows)} sessions...")
            
            for row in rows:
                chat_id = row[0] # tuple index because not using RealDictCursor here for simplicity/speed? 
                # Actually default cursor returns tuples.
                raw_key = row[1]
                raw_secret = row[2]
                
                try:
                    # Decrypt (Old)
                    dec_key = decrypt_with_cipher(old_cipher, raw_key)
                    dec_secret = decrypt_with_cipher(old_cipher, raw_secret)
                    
                    # Encrypt (New)
                    enc_key = new_cipher.encrypt(dec_key.encode('utf-8')).decode('utf-8') if dec_key else ""
                    enc_secret = new_cipher.encrypt(dec_secret.encode('utf-8')).decode('utf-8') if dec_secret else ""
                    
                    # Update
                    # We use a separate cursor or execute immediately? Same cursor is fine for update if we fetched all.
                    # But fetchall loads to memory, so it is fine.
                    cur.execute("""
                        UPDATE sessions 
                        SET api_key = %s, api_secret = %s, updated_at = NOW()
                        WHERE chat_id = %s
                    """, (enc_key, enc_secret, chat_id))
                    
                    success_count += 1
                except Exception as ex:
                    print(f"❌ Error processing {chat_id}: {ex}")
                    fail_count += 1
            
            conn.commit()
            print(f"✅ Rotation Complete. Updated: {success_count}, Failed: {fail_count}")
            print("\n⚠️ IMPORTANT: Now update your .env file with the NEW key:")
            print(f"ENCRYPTION_KEY='{new_key_str}'")
            
    except Exception as e:
        print(f"❌ Runtime Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rotate API Key Encryption")
    parser.add_argument("--new-key", help="The NEW Fernet key to use", required=False)
    parser.add_argument("--generate", action="store_true", help="Generate a new key automatically")
    
    args = parser.parse_args()
    
    new_key = args.new_key
    if args.generate:
        new_key = Fernet.generate_key().decode('utf-8')
        print(f"🔑 Generated New Key: {new_key}")
        
    if not new_key:
        print("Error: Must provide --new-key or --generate")
        sys.exit(1)
        
    rotate_database_keys(new_key)


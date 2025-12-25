import os
from cryptography.fernet import Fernet # type: ignore

# Lazy loading of the key to avoid import errors if env not set immediately
_fernet_instance = None

def get_cipher():
    """Returns a singleton Fernet instance."""
    global _fernet_instance
    if _fernet_instance:
        return _fernet_instance
    
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        return None
        
    try:
        _fernet_instance = Fernet(key)
        return _fernet_instance
    except Exception as e:
        print(f"❌ Encryption Error: Invalid Key format. {e}")
        return None

def encrypt_value(text: str) -> str:
    """
    Encrypts a string value.
    Returns the encrypted string (base64 encoded).
    If no key is configured, returns value as-is (with warning).
    """
    if not text:
        return text
        
    cipher = get_cipher()
    if not cipher:
        # Fallback for when setup isn't complete (Log this!)
        return text
        
    try:
        # Fernet encrypt expects bytes, returns bytes
        encrypted_bytes = cipher.encrypt(text.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"❌ Encryption Failed: {e}")
        return text

def decrypt_value(text: str) -> str:
    """
    Decrypts a string value.
    Returns the decrypted string.
    If decryption fails (e.g. invalid token, wrong key), returns original text.
    This enables 'Lazy Migration' (reading old plain text works).
    """
    if not text:
        return text
        
    cipher = get_cipher()
    if not cipher:
        return text
        
    try:
        # Fernet decrypt expects bytes
        decrypted_bytes = cipher.decrypt(text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception:
        # If decryption fails, assume it's legacy plain text
        # (or the key changed and data is lost, but we return text to be safe)
        return text

def generate_key() -> str:
    """Generates a new valid Fernet key."""
    return Fernet.generate_key().decode('utf-8')


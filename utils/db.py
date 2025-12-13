"""
Database module for PostgreSQL persistence.
Falls back to JSON files if DATABASE_URL is not set.
"""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv('DATABASE_URL')

def get_connection():
    """Get a PostgreSQL connection."""
    if not DATABASE_URL:
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        print(f"❌ DB Connection Error: {e}")
        return None

def init_db():
    """Initialize database tables if they don't exist."""
    conn = get_connection()
    if not conn:
        print("⚠️ DATABASE_URL not set. Using JSON fallback.")
        return False
    
    try:
        with conn.cursor() as cur:
            # Sessions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    chat_id VARCHAR(50) PRIMARY KEY,
                    api_key TEXT,
                    api_secret TEXT,
                    config JSONB DEFAULT '{}'::jsonb,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Bot state table (singleton)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bot_state (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    enabled_strategies JSONB DEFAULT '{}'::jsonb,
                    group_config JSONB DEFAULT '{}'::jsonb,
                    disabled_assets JSONB DEFAULT '[]'::jsonb,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Ensure bot_state has at least one row
            cur.execute("""
                INSERT INTO bot_state (id) VALUES (1)
                ON CONFLICT (id) DO NOTHING
            """)
            
            conn.commit()
            print("✅ Database tables initialized.")
            return True
    except Exception as e:
        print(f"❌ DB Init Error: {e}")
        return False
    finally:
        conn.close()

# --- SESSION FUNCTIONS ---

def load_all_sessions():
    """Load all sessions from PostgreSQL. Returns dict {chat_id: session_data}."""
    conn = get_connection()
    if not conn:
        return None  # Caller should use JSON fallback
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT chat_id, api_key, api_secret, config FROM sessions")
            rows = cur.fetchall()
            
            sessions = {}
            for row in rows:
                sessions[row['chat_id']] = {
                    'api_key': row['api_key'],
                    'api_secret': row['api_secret'],
                    'config': row['config'] or {}
                }
            print(f"📚 Loaded {len(sessions)} sessions from PostgreSQL.")
            return sessions
    except Exception as e:
        print(f"❌ Load Sessions Error: {e}")
        return None
    finally:
        conn.close()

def save_session(chat_id: str, api_key: str, api_secret: str, config: dict):
    """Save or update a single session to PostgreSQL."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sessions (chat_id, api_key, api_secret, config, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (chat_id) 
                DO UPDATE SET 
                    api_key = EXCLUDED.api_key,
                    api_secret = EXCLUDED.api_secret,
                    config = EXCLUDED.config,
                    updated_at = NOW()
            """, (chat_id, api_key, api_secret, json.dumps(config)))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Save Session Error: {e}")
        return False
    finally:
        conn.close()

def save_all_sessions(sessions_dict: dict):
    """Batch save all sessions to PostgreSQL."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            for chat_id, data in sessions_dict.items():
                cur.execute("""
                    INSERT INTO sessions (chat_id, api_key, api_secret, config, updated_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (chat_id) 
                    DO UPDATE SET 
                        api_key = EXCLUDED.api_key,
                        api_secret = EXCLUDED.api_secret,
                        config = EXCLUDED.config,
                        updated_at = NOW()
                """, (
                    chat_id,
                    data.get('api_key'),
                    data.get('api_secret'),
                    json.dumps(data.get('config', {}))
                ))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Batch Save Sessions Error: {e}")
        return False
    finally:
        conn.close()

# --- BOT STATE FUNCTIONS ---

def load_bot_state():
    """Load global bot state from PostgreSQL. Returns dict or None."""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT enabled_strategies, group_config, disabled_assets FROM bot_state WHERE id = 1")
            row = cur.fetchone()
            
            if row:
                print("✅ Bot state loaded from PostgreSQL.")
                return {
                    'enabled_strategies': row['enabled_strategies'] or {},
                    'group_config': row['group_config'] or {},
                    'disabled_assets': row['disabled_assets'] or []
                }
            return None
    except Exception as e:
        print(f"❌ Load Bot State Error: {e}")
        return None
    finally:
        conn.close()

def save_bot_state(enabled_strategies: dict, group_config: dict, disabled_assets: list):
    """Save global bot state to PostgreSQL."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO bot_state (id, enabled_strategies, group_config, disabled_assets, updated_at)
                VALUES (1, %s, %s, %s, NOW())
                ON CONFLICT (id) 
                DO UPDATE SET 
                    enabled_strategies = EXCLUDED.enabled_strategies,
                    group_config = EXCLUDED.group_config,
                    disabled_assets = EXCLUDED.disabled_assets,
                    updated_at = NOW()
            """, (
                json.dumps(enabled_strategies),
                json.dumps(group_config),
                json.dumps(list(disabled_assets) if isinstance(disabled_assets, set) else disabled_assets)
            ))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Save Bot State Error: {e}")
        return False
    finally:
        conn.close()

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
        
    # Security Check
    if not os.getenv('ENCRYPTION_KEY'):
        print("⚠️ WARNING: 'ENCRYPTION_KEY' not found in env. API Keys will be saved in PLAIN TEXT.")
    else:
        print("🔒 Security: Encryption Enabled (Fernet AES-256).")
    
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

            # Users table (Subscription System)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    chat_id VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'user', -- 'admin', 'user'
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Ensure sequence starts at 1000 for aesthetics (if empty)
            cur.execute("SELECT count(*) FROM users")
            if cur.fetchone()[0] == 0:
                 cur.execute("ALTER SEQUENCE users_id_seq RESTART WITH 1000")
            
            # Add timezone column if not exists (migration)
            cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC'
            """)
            
            # Add telegram_id column alias if not exists (for timezone_manager compatibility)
            cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_id BIGINT
            """)
            # Sync chat_id to telegram_id for existing rows
            cur.execute("""
                UPDATE users SET telegram_id = chat_id::BIGINT WHERE telegram_id IS NULL AND chat_id ~ '^[0-9]+$'
            """)
            
            # Add enabled_groups column if not exists (migration for per-user asset preferences)
            cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS enabled_groups JSONB DEFAULT '{"CRYPTO": true, "STOCKS": true, "ETFS": true}'::jsonb
            """)
            
            # Scheduled tasks table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    job_id VARCHAR(100),
                    action VARCHAR(50) NOT NULL,
                    params JSONB DEFAULT '{}'::jsonb,
                    schedule_type VARCHAR(20),
                    schedule_value TEXT,
                    description TEXT,
                    next_run TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
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
from servos.security import encrypt_value, decrypt_value

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
                # Decrypt keys on load (Lazy Migration handled in decrypt_value)
                sessions[row['chat_id']] = {
                    'api_key': decrypt_value(row['api_key']),
                    'api_secret': decrypt_value(row['api_secret']),
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
    
    # Encrypt sensitive data before saving
    enc_key = encrypt_value(api_key)
    enc_secret = encrypt_value(api_secret)
    
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
            """, (chat_id, enc_key, enc_secret, json.dumps(config)))
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
                # Encrypt sensitive data before saving
                raw_key = data.get('api_key')
                raw_secret = data.get('api_secret')
                
                enc_key = encrypt_value(raw_key) if raw_key else ""
                enc_secret = encrypt_value(raw_secret) if raw_secret else ""
                
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
                    enc_key,
                    enc_secret,
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

def save_bot_state(enabled_strategies: dict, group_config: dict, disabled_assets: list, ai_filter: bool = None, premium_signals: bool = None):
    """Save global bot state to PostgreSQL. Special flags are stored within group_config."""
    conn = get_connection()
    if not conn:
        return False
    
    # Embed flags in group_config for persistence
    gc_to_save = dict(group_config)
    if ai_filter is not None:
        gc_to_save['_AI_FILTER'] = ai_filter
    if premium_signals is not None:
        gc_to_save['_PREMIUM_SIGNALS'] = premium_signals
    
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
                json.dumps(gc_to_save),
                json.dumps(list(disabled_assets) if isinstance(disabled_assets, set) else disabled_assets)
            ))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Save Bot State Error: {e}")
        return False
    finally:
        conn.close()

# --- SUBSCRIPTION FUNCTIONS ---

def get_user_role(chat_id: str) -> tuple[bool, str]:
    """
    Check if user exists in DB and valid.
    Returns: (Allowed, Role)
    Roles: 'owner', 'admin', 'user', 'none'
    """
    # 1. Check ENV Owner
    env_owner = os.getenv('TELEGRAM_CHAT_ID', '')
    if str(chat_id) in env_owner.split(','):
        return True, 'owner'
    
    # 2. Check DB
    conn = get_connection()
    if not conn:
        return False, 'none'
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT role, expires_at FROM users WHERE chat_id = %s", (str(chat_id),))
            row = cur.fetchone()
            
            if not row:
                return False, 'none'
            
            role = row['role']
            if role == 'admin':
                return True, 'admin'
            
            # Check expiration for regular users
            if row['expires_at']:
                from datetime import datetime
                if row['expires_at'] < datetime.now():
                    return False, 'expired'
            
            return True, 'user'
            
    except Exception as e:
        print(f"❌ Check Access Error: {e}")
        return False, 'error'
    finally:
        conn.close()

def get_user_name(chat_id: str) -> str:
    """
    Fetch the user's name from the database.
    Fallback to 'Operador' if not found.
    """
    # Hardcoded owner name
    if str(chat_id) == "1265547936":
        return "Fabio"
    
    conn = get_connection()
    if not conn:
        print(f"⚠️ get_user_name: No DB connection for chat_id={chat_id}")
        return "Operador"
        
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM users WHERE chat_id = %s", (str(chat_id),))
            row = cur.fetchone()
            if row and row[0]:
                print(f"✅ get_user_name: Found '{row[0]}' for chat_id={chat_id}")
                return row[0]
            
            # Fallback if owner
            env_owner = os.getenv('TELEGRAM_CHAT_ID', '')
            if str(chat_id) in env_owner.split(','):
                return "Comandante"
            
            print(f"⚠️ get_user_name: No name found for chat_id={chat_id}, defaulting to Operador")
            return "Operador"
    except Exception as e:
        print(f"❌ Get User Name Error: {e}")
        return "Operador"
    finally:
        conn.close()

def add_system_user(name: str, chat_id: str, days: int = None, role: str = 'user'):
    """Add a user/admin to the DB."""
    conn = get_connection()
    if not conn: return False, "DB Error"
    
    try:
        expires_at = None
        if days:
            from datetime import timedelta, datetime
            expires_at = datetime.now() + timedelta(days=days)
            
        with conn.cursor() as cur:
            # ID sequence starts at 1000 automatically via SERIAL/SEQUENCE if configured, 
            # but we defined SERIAL in init so it starts at 1. 
            # We can force start at 1000 in init if we want, or just let it be.
            # Let's just insert.
            cur.execute("""
                INSERT INTO users (chat_id, name, role, expires_at, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (chat_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    expires_at = EXCLUDED.expires_at,
                    created_at = NOW()
                RETURNING id
            """, (str(chat_id), name, role, expires_at))
            new_id = cur.fetchone()[0]
            conn.commit()
            return True, new_id
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def remove_system_user(user_id: int):
    """Remove user by numeric ID."""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return cur.rowcount > 0
    except:
        return False
    finally:
        conn.close()

def get_all_system_users():
    """Get all DB users."""
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name, chat_id, role, expires_at FROM users ORDER BY role, id")
            return cur.fetchall()
    except:
        return []
    finally:
        conn.close()


# --- USER ENABLED GROUPS FUNCTIONS ---

def get_user_enabled_groups(chat_id: str) -> dict:
    """
    Get user's enabled asset groups.
    Returns dict like {"CRYPTO": True, "STOCKS": True, "ETFS": True}.
    """
    default = {"CRYPTO": True, "STOCKS": True, "ETFS": True}
    conn = get_connection()
    if not conn: return default
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT enabled_groups FROM users WHERE chat_id = %s", (str(chat_id),))
            row = cur.fetchone()
            if row and row[0]:
                return row[0] if isinstance(row[0], dict) else json.loads(row[0])
            return default
    except:
        return default
    finally:
        conn.close()


def set_user_enabled_groups(chat_id: str, groups: dict) -> bool:
    """
    Update user's enabled asset groups.
    groups: dict like {"CRYPTO": True, "STOCKS": False, "ETFS": True}
    """
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET enabled_groups = %s WHERE chat_id = %s",
                (json.dumps(groups), str(chat_id))
            )
            conn.commit()
            return cur.rowcount > 0
    except:
        return False
    finally:
        conn.close()


# --- SCHEDULED TASKS FUNCTIONS ---

def save_scheduled_task(user_id: int, task_data: dict) -> int:
    """Save a new scheduled task. Returns task ID or -1 on error."""
    conn = get_connection()
    if not conn:
        return -1
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO scheduled_tasks 
                (user_id, job_id, action, params, schedule_type, schedule_value, description, next_run)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id,
                task_data.get('job_id'),
                task_data.get('action'),
                json.dumps(task_data.get('params', {})),
                task_data.get('schedule_type'),
                task_data.get('schedule_value'),
                task_data.get('description'),
                task_data.get('next_run')
            ))
            task_id = cur.fetchone()[0]
            conn.commit()
            return task_id
    except Exception as e:
        print(f"❌ Save Task Error: {e}")
        return -1
    finally:
        conn.close()


def get_scheduled_tasks(user_id: int) -> list:
    """Get all active scheduled tasks for a user."""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, job_id, action, params, schedule_type, schedule_value, 
                       description, next_run, created_at
                FROM scheduled_tasks 
                WHERE user_id = %s AND is_active = TRUE
                ORDER BY created_at DESC
            """, (user_id,))
            return cur.fetchall()
    except Exception as e:
        print(f"❌ Get Tasks Error: {e}")
        return []
    finally:
        conn.close()


def delete_scheduled_task(task_id: int) -> bool:
    """Delete (deactivate) a scheduled task."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE scheduled_tasks SET is_active = FALSE WHERE id = %s
            """, (task_id,))
            conn.commit()
            return cur.rowcount > 0
    except Exception as e:
        print(f"❌ Delete Task Error: {e}")
        return False
    finally:
        conn.close()


def update_task_next_run(task_id: int, next_run: str) -> bool:
    """Update the next_run timestamp for a task."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE scheduled_tasks SET next_run = %s WHERE id = %s
            """, (next_run, task_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Update Task Error: {e}")
        return False
    finally:
        conn.close()


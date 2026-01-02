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

            # Trade Journal table (Fase 4)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trade_journal (
                    id SERIAL PRIMARY KEY,
                    chat_id VARCHAR(50) NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    side VARCHAR(10) NOT NULL,  -- LONG, SHORT
                    strategy VARCHAR(50),
                    exchange VARCHAR(20) NOT NULL,
                    entry_price DECIMAL(20,8) NOT NULL,
                    exit_price DECIMAL(20,8),
                    quantity DECIMAL(20,8) NOT NULL,
                    leverage INTEGER DEFAULT 1,
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP,
                    pnl DECIMAL(20,8),
                    pnl_pct DECIMAL(10,4),
                    fees DECIMAL(20,8) DEFAULT 0,
                    slippage DECIMAL(20,8) DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'OPEN',  -- OPEN, CLOSED, CANCELLED
                    exit_reason VARCHAR(100),  -- TP, SL, TIME_STOP, MANUAL, etc.
                    metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Performance Metrics table (Fase 4)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id SERIAL PRIMARY KEY,
                    chat_id VARCHAR(50) NOT NULL,
                    symbol VARCHAR(20),
                    strategy VARCHAR(50),
                    exchange VARCHAR(20),
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    win_rate DECIMAL(5,4),
                    avg_win DECIMAL(20,8),
                    avg_loss DECIMAL(20,8),
                    expectancy DECIMAL(10,4),  -- R multiple
                    profit_factor DECIMAL(10,4),
                    max_drawdown DECIMAL(10,4),
                    sharpe_ratio DECIMAL(10,4),
                    total_pnl DECIMAL(20,8),
                    total_fees DECIMAL(20,8),
                    avg_holding_time INTERVAL,
                    mae DECIMAL(10,4),  -- Maximum Adverse Excursion
                    mfe DECIMAL(10,4),  -- Maximum Favorable Excursion
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(chat_id, symbol, strategy, exchange, period_start, period_end)
                )
            """)

            # Strategy Calibration table (Fase 4)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS strategy_calibration (
                    id SERIAL PRIMARY KEY,
                    chat_id VARCHAR(50) NOT NULL,
                    strategy VARCHAR(50) NOT NULL,
                    symbol VARCHAR(20),
                    exchange VARCHAR(20),
                    confidence_threshold DECIMAL(3,2) DEFAULT 0.7,
                    leverage_multiplier DECIMAL(5,2) DEFAULT 1.0,
                    size_multiplier DECIMAL(5,2) DEFAULT 1.0,
                    kelly_fraction DECIMAL(3,2) DEFAULT 0.5,
                    win_rate_estimate DECIMAL(5,4),
                    risk_reward_estimate DECIMAL(5,2),
                    last_updated TIMESTAMP DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT TRUE,
                    UNIQUE(chat_id, strategy, symbol, exchange)
                )
            """)

            # Create indexes for performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_trade_journal_chat_id ON trade_journal(chat_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_trade_journal_status ON trade_journal(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_trade_journal_symbol ON trade_journal(symbol)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_trade_journal_strategy ON trade_journal(strategy)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_performance_metrics_chat_id ON performance_metrics(chat_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_performance_metrics_strategy ON performance_metrics(strategy)")

            conn.commit()
            print("✅ Database tables initialized.")
            return True
    except Exception as e:
        print(f"❌ DB Init Error: {e}")
        return False
    finally:
        conn.close()

# --- TRADE JOURNAL FUNCTIONS (Fase 4) ---

def log_trade_entry(chat_id: str, symbol: str, side: str, strategy: str, exchange: str,
                   entry_price: float, quantity: float, leverage: int = 1, metadata: dict = None):
    """Log a trade entry to the journal."""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO trade_journal
                (chat_id, symbol, side, strategy, exchange, entry_price, quantity, leverage, entry_time, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """, (chat_id, symbol, side, strategy, exchange, entry_price, quantity, leverage,
                  json.dumps(metadata or {})))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Log Trade Entry Error: {e}")
        return False
    finally:
        conn.close()

def log_trade_exit(trade_id: int, exit_price: float, pnl: float, pnl_pct: float,
                  fees: float = 0, slippage: float = 0, exit_reason: str = None):
    """Update a trade with exit information."""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE trade_journal
                SET exit_price = %s, exit_time = NOW(), pnl = %s, pnl_pct = %s,
                    fees = %s, slippage = %s, status = 'CLOSED', exit_reason = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (exit_price, pnl, pnl_pct, fees, slippage, exit_reason, trade_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Log Trade Exit Error: {e}")
        return False
    finally:
        conn.close()

def get_open_trades(chat_id: str) -> list:
    """Get all open trades for a user."""
    conn = get_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM trade_journal
                WHERE chat_id = %s AND status = 'OPEN'
                ORDER BY entry_time DESC
            """, (chat_id,))
            return cur.fetchall()
    except Exception as e:
        print(f"❌ Get Open Trades Error: {e}")
        return []
    finally:
        conn.close()

def calculate_performance_metrics(chat_id: str, symbol: str = None, strategy: str = None,
                                exchange: str = None, days: int = 30) -> dict:
    """Calculate performance metrics for the specified filters."""
    conn = get_connection()
    if not conn:
        return {}

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Build dynamic WHERE clause
            conditions = ["chat_id = %s", "status = 'CLOSED'"]
            params = [chat_id]

            if symbol:
                conditions.append("symbol = %s")
                params.append(symbol)
            if strategy:
                conditions.append("strategy = %s")
                params.append(strategy)
            if exchange:
                conditions.append("exchange = %s")
                params.append(exchange)

            # Add date filter
            conditions.append("exit_time >= NOW() - INTERVAL '%s days'")
            params.append(days)

            where_clause = " AND ".join(conditions)

            # Get closed trades
            cur.execute(f"""
                SELECT * FROM trade_journal
                WHERE {where_clause}
                ORDER BY exit_time DESC
            """, params)

            trades = cur.fetchall()

            if not trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'expectancy': 0.0,
                    'profit_factor': 0.0,
                    'total_pnl': 0.0,
                    'avg_holding_time': 0
                }

            # Calculate metrics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['pnl'] > 0])
            losing_trades = total_trades - winning_trades

            win_rate = winning_trades / total_trades if total_trades > 0 else 0

            # Calculate averages
            winning_pnls = [t['pnl'] for t in trades if t['pnl'] > 0]
            losing_pnls = [t['pnl'] for t in trades if t['pnl'] < 0]

            avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
            avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0

            # Expectancy (R multiple)
            expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
            expectancy_r = expectancy / abs(avg_loss) if avg_loss != 0 else 0

            # Profit Factor
            total_wins = sum(winning_pnls)
            total_losses = abs(sum(losing_pnls))
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

            # Total P&L
            total_pnl = sum(t['pnl'] for t in trades)

            # Average holding time (in hours)
            holding_times = []
            for t in trades:
                if t['exit_time'] and t['entry_time']:
                    delta = t['exit_time'] - t['entry_time']
                    holding_times.append(delta.total_seconds() / 3600)  # Convert to hours

            avg_holding_time = sum(holding_times) / len(holding_times) if holding_times else 0

            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'expectancy': expectancy_r,
                'profit_factor': profit_factor,
                'total_pnl': total_pnl,
                'avg_holding_time': avg_holding_time
            }

    except Exception as e:
        print(f"❌ Calculate Performance Metrics Error: {e}")
        return {}
    finally:
        conn.close()

def get_strategy_calibration(chat_id: str, strategy: str, symbol: str = None, exchange: str = None) -> dict:
    """Get calibration settings for a strategy."""
    conn = get_connection()
    if not conn:
        return {}

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM strategy_calibration
                WHERE chat_id = %s AND strategy = %s
                AND (symbol = %s OR symbol IS NULL)
                AND (exchange = %s OR exchange IS NULL)
                AND is_active = TRUE
                ORDER BY symbol DESC NULLS LAST, exchange DESC NULLS LAST
                LIMIT 1
            """, (chat_id, strategy, symbol, exchange))
            result = cur.fetchone()
            return dict(result) if result else {}
    except Exception as e:
        print(f"❌ Get Strategy Calibration Error: {e}")
        return {}
    finally:
        conn.close()

def update_strategy_calibration(chat_id: str, strategy: str, symbol: str = None, exchange: str = None,
                              calibration_data: dict = None):
    """Update or create strategy calibration settings."""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            # Use upsert
            cur.execute("""
                INSERT INTO strategy_calibration
                (chat_id, strategy, symbol, exchange, confidence_threshold, leverage_multiplier,
                 size_multiplier, kelly_fraction, win_rate_estimate, risk_reward_estimate, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (chat_id, strategy, symbol, exchange)
                DO UPDATE SET
                    confidence_threshold = EXCLUDED.confidence_threshold,
                    leverage_multiplier = EXCLUDED.leverage_multiplier,
                    size_multiplier = EXCLUDED.size_multiplier,
                    kelly_fraction = EXCLUDED.kelly_fraction,
                    win_rate_estimate = EXCLUDED.win_rate_estimate,
                    risk_reward_estimate = EXCLUDED.risk_reward_estimate,
                    last_updated = NOW()
            """, (
                chat_id, strategy, symbol, exchange,
                calibration_data.get('confidence_threshold', 0.7),
                calibration_data.get('leverage_multiplier', 1.0),
                calibration_data.get('size_multiplier', 1.0),
                calibration_data.get('kelly_fraction', 0.5),
                calibration_data.get('win_rate_estimate'),
                calibration_data.get('risk_reward_estimate')
            ))
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Update Strategy Calibration Error: {e}")
        return False
    finally:
        conn.close()

def auto_calibrate_strategy(chat_id: str, strategy: str, symbol: str = None, exchange: str = None):
    """
    Auto-calibrate strategy parameters based on recent performance (Fase 4).
    Adjusts leverage and size multipliers based on expectancy and drawdown.
    """
    # Get recent performance metrics
    metrics = calculate_performance_metrics(chat_id, symbol, strategy, exchange, days=30)

    if not metrics or metrics['total_trades'] < 10:
        return False  # Need minimum sample size

    expectancy = metrics['expectancy']
    win_rate = metrics['win_rate']
    total_pnl = metrics['total_pnl']

    # Calculate adjustments based on performance
    # Positive expectancy -> increase size/leverage
    # Negative expectancy -> decrease size/leverage

    base_multiplier = 1.0

    if expectancy > 0.5:  # Good expectancy
        size_multiplier = min(1.5, base_multiplier + (expectancy * 0.5))
        leverage_multiplier = min(1.3, base_multiplier + (expectancy * 0.3))
    elif expectancy > 0:  # Slightly positive
        size_multiplier = base_multiplier + (expectancy * 0.3)
        leverage_multiplier = base_multiplier + (expectancy * 0.2)
    elif expectancy > -0.2:  # Slightly negative
        size_multiplier = max(0.7, base_multiplier + (expectancy * 0.5))
        leverage_multiplier = max(0.8, base_multiplier + (expectancy * 0.3))
    else:  # Poor performance
        size_multiplier = max(0.5, base_multiplier + (expectancy * 0.7))
        leverage_multiplier = max(0.7, base_multiplier + (expectancy * 0.4))

    # Additional adjustment based on win rate
    if win_rate > 0.6:
        size_multiplier *= 1.1
        leverage_multiplier *= 1.05
    elif win_rate < 0.4:
        size_multiplier *= 0.9
        leverage_multiplier *= 0.95

    # Update calibration
    calibration_data = {
        'confidence_threshold': 0.7,  # Keep default
        'leverage_multiplier': leverage_multiplier,
        'size_multiplier': size_multiplier,
        'kelly_fraction': 0.5,  # Keep conservative
        'win_rate_estimate': win_rate,
        'risk_reward_estimate': 1.5  # Default assumption
    }

    return update_strategy_calibration(chat_id, strategy, symbol, exchange, calibration_data)

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


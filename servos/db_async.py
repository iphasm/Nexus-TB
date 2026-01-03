"""
Asynchronous PostgreSQL Database Module for Nexus
Optimized with connection pooling and async operations.

MIGRATION FROM: servos/db.py (psycopg2 synchronous)
TO: servos/db_async.py (asyncpg asynchronous)
"""

import os
import json
import logging
import asyncpg
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta

from servos.security import encrypt_value, decrypt_value

# Configure logging
logger = logging.getLogger(__name__)

class NexusDB:
    """
    Asynchronous PostgreSQL database handler with connection pooling.
    Optimized for high-throughput trading operations.
    """

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = os.getenv('DATABASE_URL')
        self.encryption_key = os.getenv('ENCRYPTION_KEY')

    async def init_pool(self, min_size: int = 5, max_size: int = 20):
        """Initialize connection pool with optimized settings."""
        if not self.database_url:
            logger.warning("⚠️ DATABASE_URL not set. Using JSON fallback.")
            return False

        if not self.encryption_key:
            logger.warning("⚠️ ENCRYPTION_KEY not found. API Keys will be saved in PLAIN TEXT.")

        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=min_size,
                max_size=max_size,
                command_timeout=30,  # 30 seconds timeout
                ssl='require',
                # Connection validation
                check=asyncpg.pool.check_connection,
                # Prepared statements cache
                statement_cache_size=100,
                # Max cached query plans
                max_cached_statement_lifetime=300,
            )

            # Initialize database schema
            await self._init_schema()

            logger.info(f"✅ PostgreSQL pool initialized (min={min_size}, max={max_size})")
            return True

        except Exception as e:
            logger.error(f"❌ Pool initialization error: {e}")
            return False

    async def close_pool(self):
        """Gracefully close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("🔌 PostgreSQL pool closed")

    async def _init_schema(self):
        """Initialize database schema with optimized tables and indexes."""
        if not self.pool:
            return

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Sessions table with optimized indexes
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        chat_id VARCHAR(50) PRIMARY KEY,
                        api_key TEXT,
                        api_secret TEXT,
                        config JSONB DEFAULT '{}'::jsonb,
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)

                # Bot state table (singleton pattern)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS bot_state (
                        id INTEGER PRIMARY KEY DEFAULT 1,
                        enabled_strategies JSONB DEFAULT '{}'::jsonb,
                        group_config JSONB DEFAULT '{}'::jsonb,
                        disabled_assets TEXT[] DEFAULT ARRAY[]::TEXT[],
                        ai_filter_enabled BOOLEAN DEFAULT true,
                        last_updated TIMESTAMP DEFAULT NOW(),
                        version INTEGER DEFAULT 1
                    )
                """)

                # Users table for subscription system
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        chat_id VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(100),
                        role VARCHAR(20) DEFAULT 'user',
                        expires_at TIMESTAMP,
                        timezone VARCHAR(50) DEFAULT 'UTC',
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)

                # Ensure bot_state has at least one row
                await conn.execute("""
                    INSERT INTO bot_state (id) VALUES (1)
                    ON CONFLICT (id) DO NOTHING
                """)

                # Ensure sequence starts at 1000
                await conn.execute("SELECT setval('users_id_seq', 1000, false)")

                # Add timezone column if not exists (migration)
                await conn.execute("""
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC'
                """)

                # Create optimized indexes (concurrent for production)
                indexes = [
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_updated_at ON sessions(updated_at DESC)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_config_gin ON sessions USING GIN (config)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bot_state_updated_at ON bot_state(last_updated DESC)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_chat_id ON users(chat_id)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role ON users(role)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_expires_at ON users(expires_at) WHERE expires_at IS NOT NULL"
                ]

                for index_sql in indexes:
                    try:
                        await conn.execute(index_sql)
                    except asyncpg.exceptions.UniqueViolationError:
                        # Index already exists, skip
                        pass

                logger.info("📋 Database schema initialized with optimized indexes")

    # --- SESSION FUNCTIONS (ASYNC OPTIMIZED) ---

    async def load_all_sessions(self) -> Optional[Dict[str, Dict]]:
        """Load all sessions asynchronously with optimized query."""
        if not self.pool:
            return None

        try:
            async with self.pool.acquire() as conn:
                # Optimized query with explicit column selection
                rows = await conn.fetch("""
                    SELECT chat_id, api_key, api_secret, config
                    FROM sessions
                    ORDER BY updated_at DESC
                """)

                sessions = {}
                for row in rows:
                    sessions[row['chat_id']] = {
                        'api_key': decrypt_value(row['api_key']) if row['api_key'] else '',
                        'api_secret': decrypt_value(row['api_secret']) if row['api_secret'] else '',
                        'config': row['config'] or {}
                    }

                logger.info(f"📚 Loaded {len(sessions)} sessions from PostgreSQL")
                return sessions

        except Exception as e:
            logger.error(f"❌ Load sessions error: {e}")
            return None

    async def save_session_batch(self, sessions_dict: Dict[str, Dict]) -> bool:
        """Batch save sessions efficiently with transaction."""
        if not self.pool:
            return False

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Prepare encrypted data
                    records = []
                    for chat_id, data in sessions_dict.items():
                        records.append((
                            chat_id,
                            encrypt_value(data.get('api_key', '')),
                            encrypt_value(data.get('api_secret', '')),
                            json.dumps(data.get('config', {}))
                        ))

                    # Batch upsert with prepared statement
                    await conn.executemany("""
                        INSERT INTO sessions (chat_id, api_key, api_secret, config, updated_at)
                        VALUES ($1, $2, $3, $4, NOW())
                        ON CONFLICT (chat_id)
                        DO UPDATE SET
                            api_key = EXCLUDED.api_key,
                            api_secret = EXCLUDED.api_secret,
                            config = EXCLUDED.config,
                            updated_at = NOW()
                    """, records)

                logger.info(f"💾 Batch saved {len(records)} sessions")
                return True

        except Exception as e:
            logger.error(f"❌ Batch save error: {e}")
            return False

    async def save_single_session(self, chat_id: str, api_key: str, api_secret: str, config: dict) -> bool:
        """Save or update a single session."""
        if not self.pool:
            return False

        try:
            async with self.pool.acquire() as conn:
                enc_key = encrypt_value(api_key) if api_key else ""
                enc_secret = encrypt_value(api_secret) if api_secret else ""

                await conn.execute("""
                    INSERT INTO sessions (chat_id, api_key, api_secret, config, updated_at)
                    VALUES ($1, $2, $3, $4, NOW())
                    ON CONFLICT (chat_id)
                    DO UPDATE SET
                        api_key = EXCLUDED.api_key,
                        api_secret = EXCLUDED.api_secret,
                        config = EXCLUDED.config,
                        updated_at = NOW()
                """, chat_id, enc_key, enc_secret, json.dumps(config))

                logger.debug(f"💾 Saved session for chat_id: {chat_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Save session error: {e}")
            return False

    # --- BOT STATE FUNCTIONS (ASYNC OPTIMIZED) ---

    async def load_bot_state(self) -> Optional[Dict]:
        """Load global bot state asynchronously."""
        if not self.pool:
            return None

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT enabled_strategies, group_config, disabled_assets, ai_filter_enabled
                    FROM bot_state WHERE id = 1
                """)

                if row:
                    logger.info("✅ Bot state loaded from PostgreSQL")
                    return {
                        'enabled_strategies': row['enabled_strategies'] or {},
                        'group_config': row['group_config'] or {},
                        'disabled_assets': row['disabled_assets'] or [],
                        'ai_filter_enabled': row['ai_filter_enabled']
                    }
                return None

        except Exception as e:
            logger.error(f"❌ Load bot state error: {e}")
            return None

    async def save_bot_state(self, enabled_strategies: dict, group_config: dict,
                           disabled_assets: list, ai_filter_enabled: bool = None) -> bool:
        """Save global bot state asynchronously."""
        if not self.pool:
            return False

        try:
            async with self.pool.acquire() as conn:
                # Embed AI filter setting in group_config for backward compatibility
                gc_to_save = dict(group_config)
                if ai_filter_enabled is not None:
                    gc_to_save['_AI_FILTER'] = ai_filter_enabled

                await conn.execute("""
                    INSERT INTO bot_state (id, enabled_strategies, group_config, disabled_assets,
                                         ai_filter_enabled, last_updated)
                    VALUES (1, $1, $2, $3, $4, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        enabled_strategies = EXCLUDED.enabled_strategies,
                        group_config = EXCLUDED.group_config,
                        disabled_assets = EXCLUDED.disabled_assets,
                        ai_filter_enabled = EXCLUDED.ai_filter_enabled,
                        last_updated = NOW()
                """, json.dumps(enabled_strategies), json.dumps(gc_to_save),
                     list(disabled_assets) if isinstance(disabled_assets, (list, set)) else disabled_assets,
                     ai_filter_enabled)

                logger.info("💾 Bot state saved")
                return True

        except Exception as e:
            logger.error(f"❌ Save bot state error: {e}")
            return False

    # --- USER FUNCTIONS (ASYNC OPTIMIZED) ---

    async def get_user_role(self, chat_id: str) -> Tuple[bool, str]:
        """Check if user exists and get role asynchronously."""
        # 1. Check ENV Owner
        env_owner = os.getenv('TELEGRAM_CHAT_ID', '')
        if str(chat_id) in env_owner.split(','):
            return True, 'owner'

        # 2. Check DB
        if not self.pool:
            return False, 'none'

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT role, expires_at FROM users WHERE chat_id = $1
                """, str(chat_id))

                if not row:
                    return False, 'none'

                role = row['role']
                if role == 'admin':
                    return True, 'admin'

                # Check expiration for regular users
                if row['expires_at'] and row['expires_at'] < datetime.now():
                    return False, 'expired'

                return True, 'user'

        except Exception as e:
            logger.error(f"❌ Get user role error: {e}")
            return False, 'error'

    async def get_user_name(self, chat_id: str) -> str:
        """Get user name asynchronously."""
        # Special case for owner
        env_owner = os.getenv('TELEGRAM_CHAT_ID', '')
        if str(chat_id) in env_owner.split(','):
            return "Fabio"

        if not self.pool:
            logger.warning(f"⚠️ get_user_name: No DB connection for chat_id={chat_id}")
            return "Operador"

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT name FROM users WHERE chat_id = $1
                """, str(chat_id))

                return row['name'] if row and row['name'] else "Operador"

        except Exception as e:
            logger.error(f"❌ Get user name error: {e}")
            return "Operador"

    # --- UTILITY FUNCTIONS ---

    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        if not self.pool:
            return {"status": "disconnected", "pool": None}

        try:
            async with self.pool.acquire() as conn:
                # Simple query to test connection
                result = await conn.fetchval("SELECT NOW()")
                pool_stats = {
                    "min_size": self.pool._minsize,
                    "max_size": self.pool._maxsize,
                    "size": len(self.pool._holders),
                    "used": len(self.pool._used),
                }

                return {
                    "status": "healthy",
                    "timestamp": result.isoformat(),
                    "pool": pool_stats
                }

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self.pool:
            return {"error": "No pool available"}

        try:
            async with self.pool.acquire() as conn:
                # Count records in main tables
                session_count = await conn.fetchval("SELECT COUNT(*) FROM sessions")
                user_count = await conn.fetchval("SELECT COUNT(*) FROM users")

                # Get last update times
                last_session = await conn.fetchval("SELECT MAX(updated_at) FROM sessions")
                last_bot_state = await conn.fetchval("SELECT last_updated FROM bot_state WHERE id = 1")

                return {
                    "sessions": session_count,
                    "users": user_count,
                    "last_session_update": last_session.isoformat() if last_session else None,
                    "last_bot_state_update": last_bot_state.isoformat() if last_bot_state else None,
                    "pool_size": len(self.pool._holders),
                    "pool_used": len(self.pool._used)
                }

        except Exception as e:
            logger.error(f"❌ Get stats error: {e}")
            return {"error": str(e)}

# Global instance
nexus_db = NexusDB()

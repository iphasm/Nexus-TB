#!/usr/bin/env python3
"""
Database Index Optimization Script
Creates optimized indexes for PostgreSQL performance

Usage:
    python scripts/optimize_db_indexes.py
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseIndexOptimizer:
    """Optimize PostgreSQL indexes for Nexus performance."""

    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.conn = None

    def connect(self):
        """Connect to PostgreSQL database."""
        if not self.database_url:
            logger.error("❌ DATABASE_URL not set")
            return False

        try:
            self.conn = psycopg2.connect(self.database_url, sslmode='require')
            logger.info("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Disconnected from PostgreSQL")

    def get_existing_indexes(self):
        """Get list of existing indexes."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT schemaname, tablename, indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname
                """)
                indexes = cur.fetchall()
                return {f"{idx['tablename']}.{idx['indexname']}": idx for idx in indexes}
        except Exception as e:
            logger.error(f"❌ Error getting indexes: {e}")
            return {}

    def create_index_concurrent(self, index_sql: str, index_name: str):
        """Create index concurrently (safe for production)."""
        try:
            with self.conn.cursor() as cur:
                logger.info(f"🔨 Creating index: {index_name}")
                cur.execute(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} {index_sql}")
                self.conn.commit()
                logger.info(f"✅ Created index: {index_name}")
                return True
        except psycopg2.errors.UniqueViolation:
            logger.info(f"ℹ️ Index already exists: {index_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating index {index_name}: {e}")
            return False

    def optimize_sessions_indexes(self):
        """Create optimized indexes for sessions table."""
        logger.info("📋 Optimizing sessions table indexes...")

        indexes = [
            # Primary key already exists
            ("ON sessions(updated_at DESC)", "idx_sessions_updated_at"),
            ("ON sessions USING GIN (config)", "idx_sessions_config_gin"),
            # Index for chat_id lookups (already PK, but explicit)
            ("ON sessions(chat_id)", "idx_sessions_chat_id"),
        ]

        success_count = 0
        for index_sql, index_name in indexes:
            if self.create_index_concurrent(index_sql, index_name):
                success_count += 1

        logger.info(f"✅ Created {success_count}/{len(indexes)} sessions indexes")

    def optimize_bot_state_indexes(self):
        """Create optimized indexes for bot_state table."""
        logger.info("📋 Optimizing bot_state table indexes...")

        indexes = [
            ("ON bot_state(last_updated DESC)", "idx_bot_state_updated_at"),
        ]

        success_count = 0
        for index_sql, index_name in indexes:
            if self.create_index_concurrent(index_sql, index_name):
                success_count += 1

        logger.info(f"✅ Created {success_count}/{len(indexes)} bot_state indexes")

    def optimize_users_indexes(self):
        """Create optimized indexes for users table."""
        logger.info("📋 Optimizing users table indexes...")

        indexes = [
            ("ON users(chat_id)", "idx_users_chat_id"),
            ("ON users(role)", "idx_users_role"),
            ("ON users(expires_at) WHERE expires_at IS NOT NULL", "idx_users_expires_at"),
            ("ON users(created_at DESC)", "idx_users_created_at"),
        ]

        success_count = 0
        for index_sql, index_name in indexes:
            if self.create_index_concurrent(index_sql, index_name):
                success_count += 1

        logger.info(f"✅ Created {success_count}/{len(indexes)} users indexes")

    def optimize_trades_indexes(self):
        """Create optimized indexes for trades table (future-proofing)."""
        logger.info("📋 Optimizing trades table indexes (future)...")

        # Check if trades table exists
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'trades')")
                exists = cur.fetchone()[0]

                if not exists:
                    logger.info("ℹ️ Trades table doesn't exist yet, skipping")
                    return

                indexes = [
                    ("ON trades(chat_id)", "idx_trades_chat_id"),
                    ("ON trades(symbol)", "idx_trades_symbol"),
                    ("ON trades(status)", "idx_trades_status"),
                    ("ON trades(entry_timestamp DESC)", "idx_trades_entry_timestamp"),
                    ("ON trades(chat_id, status)", "idx_trades_chat_status"),
                    ("ON trades(symbol, entry_timestamp DESC)", "idx_trades_symbol_time"),
                ]

                success_count = 0
                for index_sql, index_name in indexes:
                    if self.create_index_concurrent(index_sql, index_name):
                        success_count += 1

                logger.info(f"✅ Created {success_count}/{len(indexes)} trades indexes")

        except Exception as e:
            logger.error(f"❌ Error optimizing trades indexes: {e}")

    def analyze_tables(self):
        """Run ANALYZE on all tables for query planner optimization."""
        logger.info("📊 Running ANALYZE on all tables...")

        tables = ['sessions', 'bot_state', 'users', 'trades']

        try:
            with self.conn.cursor() as cur:
                for table in tables:
                    try:
                        cur.execute(f"ANALYZE {table}")
                        logger.info(f"✅ Analyzed table: {table}")
                    except psycopg2.errors.UndefinedTable:
                        logger.info(f"ℹ️ Table doesn't exist: {table}")
                        continue
                self.conn.commit()
        except Exception as e:
            logger.error(f"❌ Error analyzing tables: {e}")

    def show_index_stats(self):
        """Show index statistics and recommendations."""
        logger.info("📊 Index Statistics and Recommendations")
        logger.info("=" * 50)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get table sizes
                cur.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY size_bytes DESC
                """)

                tables = cur.fetchall()

                for table in tables:
                    logger.info(f"📏 Table: {table['tablename']} - Size: {table['size']}")

                    # Get indexes for this table
                    cur.execute("""
                        SELECT indexname, pg_size_pretty(pg_relation_size(indexrelid)) as size
                        FROM pg_stat_user_indexes
                        WHERE schemaname = 'public' AND tablename = %s
                        ORDER BY pg_relation_size(indexrelid) DESC
                    """, (table['tablename'],))

                    indexes = cur.fetchall()
                    if indexes:
                        logger.info("   📎 Indexes:")
                        for idx in indexes:
                            logger.info(f"     • {idx['indexname']} ({idx['size']})")
                    else:
                        logger.info("   ⚠️ No indexes found")

                    logger.info("")

        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")

    def run_optimization(self):
        """Run complete index optimization."""
        logger.info("🚀 Starting PostgreSQL Index Optimization")
        logger.info("=" * 50)

        if not self.connect():
            return False

        try:
            # Get existing indexes first
            existing = self.get_existing_indexes()
            logger.info(f"📋 Found {len(existing)} existing indexes")

            # Optimize each table
            self.optimize_sessions_indexes()
            self.optimize_bot_state_indexes()
            self.optimize_users_indexes()
            self.optimize_trades_indexes()

            # Analyze tables
            self.analyze_tables()

            # Show final stats
            self.show_index_stats()

            logger.info("✅ Database optimization completed!")
            return True

        finally:
            self.disconnect()

def main():
    """Main optimization function."""
    optimizer = DatabaseIndexOptimizer()
    success = optimizer.run_optimization()

    if success:
        logger.info("🎉 All optimizations completed successfully!")
        logger.info("💡 Recommendations:")
        logger.info("   • Monitor query performance with pg_stat_statements")
        logger.info("   • Consider partitioning for large trades table")
        logger.info("   • Regular VACUUM ANALYZE maintenance")
    else:
        logger.error("❌ Optimization failed!")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())

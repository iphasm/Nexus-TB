#!/usr/bin/env python3
"""
Database Performance Monitoring Script
Monitor PostgreSQL performance metrics for Nexus

Usage:
    python scripts/monitor_db_performance.py
"""

import os
import time
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabasePerformanceMonitor:
    """Monitor PostgreSQL performance for Nexus trading bot."""

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

    def get_connection_stats(self):
        """Get connection and pool statistics."""
        logger.info("🔗 Connection Statistics")
        logger.info("-" * 30)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Current connections
                cur.execute("""
                    SELECT count(*) as total_connections,
                           count(*) filter (where state = 'active') as active_connections,
                           count(*) filter (where state = 'idle') as idle_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)
                conn_stats = cur.fetchone()

                logger.info(f"Total connections: {conn_stats['total_connections']}")
                logger.info(f"Active connections: {conn_stats['active_connections']}")
                logger.info(f"Idle connections: {conn_stats['idle_connections']}")

                return conn_stats

        except Exception as e:
            logger.error(f"❌ Error getting connection stats: {e}")
            return None

    def get_table_sizes(self):
        """Get table sizes and growth metrics."""
        logger.info("\n📏 Table Sizes")
        logger.info("-" * 30)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                        pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                                     pg_relation_size(schemaname||'.'||tablename)) as index_size,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)

                tables = cur.fetchall()

                for table in tables:
                    logger.info(f"📊 {table['tablename']}")
                    logger.info(f"   Size: {table['total_size']} (Table: {table['table_size']}, Indexes: {table['index_size']})")
                    logger.info(f"   Operations: +{table['inserts']} -{table['deletes']} ~{table['updates']}")

                return tables

        except Exception as e:
            logger.error(f"❌ Error getting table sizes: {e}")
            return None

    def get_index_usage(self):
        """Get index usage statistics."""
        logger.info("\n📎 Index Usage Statistics")
        logger.info("-" * 30)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        pg_size_pretty(pg_relation_size(indexrelid)) as size,
                        idx_scan as scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes
                    WHERE schemaname = 'public'
                    ORDER BY pg_relation_size(indexrelid) DESC
                """)

                indexes = cur.fetchall()

                for idx in indexes:
                    usage_rate = "HIGH" if idx['scans'] > 1000 else "MEDIUM" if idx['scans'] > 100 else "LOW"
                    logger.info(f"📈 {idx['tablename']}.{idx['indexname']}")
                    logger.info(f"   Size: {idx['size']}, Scans: {idx['scans']} ({usage_rate})")
                    logger.info(f"   Efficiency: {idx['tuples_fetched']}/{idx['tuples_read']} tuples")

                return indexes

        except Exception as e:
            logger.error(f"❌ Error getting index usage: {e}")
            return None

    def get_query_performance(self):
        """Get slow query statistics (requires pg_stat_statements)."""
        logger.info("\n🐌 Slow Query Analysis")
        logger.info("-" * 30)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if pg_stat_statements is available
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                    )
                """)
                has_pg_stat = cur.fetchone()['exists']

                if not has_pg_stat:
                    logger.info("⚠️ pg_stat_statements extension not available")
                    logger.info("   Install with: CREATE EXTENSION pg_stat_statements;")
                    return None

                # Get top slow queries
                cur.execute("""
                    SELECT
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements
                    WHERE query LIKE '%sessions%' OR query LIKE '%bot_state%' OR query LIKE '%users%'
                    ORDER BY mean_time DESC
                    LIMIT 10
                """)

                queries = cur.fetchall()

                for i, query in enumerate(queries, 1):
                    logger.info(f"🔍 Query {i}:")
                    logger.info(f"   Calls: {query['calls']}, Mean time: {query['mean_time']:.2f}ms")
                    logger.info(f"   Total time: {query['total_time']:.2f}ms, Rows: {query['rows']}")
                    logger.info(f"   Query: {query['query'][:100]}...")

                return queries

        except Exception as e:
            logger.error(f"❌ Error getting query performance: {e}")
            return None

    def get_cache_hit_ratio(self):
        """Get database cache hit ratio."""
        logger.info("\n💾 Cache Performance")
        logger.info("-" * 30)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        'index' as type,
                        sum(idx_blks_hit) as hits,
                        sum(idx_blks_hit + idx_blks_read) as total,
                        CASE
                            WHEN sum(idx_blks_hit + idx_blks_read) > 0
                            THEN round((sum(idx_blks_hit)::numeric / sum(idx_blks_hit + idx_blks_read)) * 100, 2)
                            ELSE 0
                        END as ratio
                    FROM pg_statio_user_indexes
                    UNION ALL
                    SELECT
                        'table' as type,
                        sum(heap_blks_hit) as hits,
                        sum(heap_blks_hit + heap_blks_read) as total,
                        CASE
                            WHEN sum(heap_blks_hit + heap_blks_read) > 0
                            THEN round((sum(heap_blks_hit)::numeric / sum(heap_blks_hit + heap_blks_read)) * 100, 2)
                            ELSE 0
                        END as ratio
                    FROM pg_statio_user_tables
                """)

                cache_stats = cur.fetchall()

                for stat in cache_stats:
                    logger.info(f"🎯 {stat['type'].title()} cache hit ratio: {stat['ratio']}% ({stat['hits']}/{stat['total']} blocks)")

                return cache_stats

        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {e}")
            return None

    def benchmark_operations(self):
        """Benchmark common operations."""
        logger.info("\n⚡ Operation Benchmarks")
        logger.info("-" * 30)

        benchmarks = {}

        try:
            # Benchmark session load
            start_time = time.time()
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM sessions")
                count = cur.fetchone()[0]
            load_time = time.time() - start_time
            benchmarks['session_count'] = load_time
            logger.info(".4f"
            # Benchmark bot state load
            start_time = time.time()
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM bot_state WHERE id = 1")
                row = cur.fetchone()
            state_time = time.time() - start_time
            benchmarks['bot_state_load'] = state_time
            logger.info(".4f"
            # Benchmark user lookup
            start_time = time.time()
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                user_count = cur.fetchone()[0]
            user_time = time.time() - start_time
            benchmarks['user_count'] = user_time
            logger.info(".4f"
            return benchmarks

        except Exception as e:
            logger.error(f"❌ Benchmark error: {e}")
            return None

    def generate_report(self):
        """Generate complete performance report."""
        logger.info("🚀 Nexus PostgreSQL Performance Report")
        logger.info("=" * 50)
        logger.info(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 50)

        if not self.connect():
            return False

        try:
            # Collect all metrics
            self.get_connection_stats()
            self.get_table_sizes()
            self.get_index_usage()
            self.get_query_performance()
            self.get_cache_hit_ratio()
            benchmarks = self.benchmark_operations()

            # Generate recommendations
            logger.info("\n💡 Performance Recommendations")
            logger.info("-" * 35)

            if benchmarks:
                # Check benchmark thresholds
                if benchmarks.get('session_count', 0) > 1.0:
                    logger.info("⚠️ Session count query is slow (>1s) - consider caching")
                if benchmarks.get('bot_state_load', 0) > 0.5:
                    logger.info("⚠️ Bot state load is slow (>500ms) - review indexes")

            logger.info("✅ Regular maintenance:")
            logger.info("   • Run VACUUM ANALYZE weekly")
            logger.info("   • Monitor pg_stat_statements for slow queries")
            logger.info("   • Consider connection pooling for high load")
            logger.info("   • Archive old trade data if applicable")

            return True

        finally:
            self.disconnect()

def main():
    """Main monitoring function."""
    monitor = DatabasePerformanceMonitor()
    success = monitor.generate_report()

    if success:
        logger.info("\n✅ Performance monitoring completed!")
    else:
        logger.error("\n❌ Performance monitoring failed!")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())

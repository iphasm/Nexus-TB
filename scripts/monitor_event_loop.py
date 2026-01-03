#!/usr/bin/env python3
"""
Event Loop Performance Monitor
Monitor and benchmark event loop blocking

TARGET: Measure impact of async optimizations
USAGE: python scripts/monitor_event_loop.py
"""

import asyncio
import time
import threading
import logging
from typing import Dict, List, Any
import psutil
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EventLoopMonitor:
    """Monitor event loop performance and blocking."""

    def __init__(self):
        self.metrics = {
            'loop_block_time': 0,
            'total_operations': 0,
            'slow_operations': 0,
            'db_operations': [],
            'xai_operations': [],
            'concurrent_tasks': 0
        }
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start background monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("📊 Event loop monitoring started")

    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logger.info("📊 Event loop monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            # Monitor basic system metrics
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)

                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent

                # Log if high usage
                if cpu_percent > 80:
                    logger.warning(f"⚠️ High CPU usage: {cpu_percent}%")
                if memory_percent > 85:
                    logger.warning(f"⚠️ High memory usage: {memory_percent}%")

            except Exception as e:
                logger.error(f"Monitoring error: {e}")

            time.sleep(5)  # Check every 5 seconds

    async def benchmark_db_operations(self) -> Dict[str, float]:
        """Benchmark database operations."""
        logger.info("🧪 Benchmarking database operations...")

        try:
            from servos.db_async import nexus_db

            # Initialize if needed
            if not hasattr(nexus_db, 'pool') or nexus_db.pool is None:
                await nexus_db.init_pool()

            results = {}

            # Test session loading
            start_time = time.time()
            sessions = await nexus_db.load_all_sessions()
            load_time = time.time() - start_time
            results['session_load'] = load_time
            logger.info(".4f"
            # Test bot state loading
            start_time = time.time()
            bot_state = await nexus_db.load_bot_state()
            state_time = time.time() - start_time
            results['bot_state_load'] = state_time
            logger.info(".4f"
            # Test health check
            start_time = time.time()
            health = await nexus_db.health_check()
            health_time = time.time() - start_time
            results['health_check'] = health_time
            logger.info(".4f"
            # Cleanup
            await nexus_db.close_pool()

            return results

        except Exception as e:
            logger.error(f"❌ DB benchmark failed: {e}")
            return {}

    async def benchmark_xai_operations(self) -> Dict[str, float]:
        """Benchmark XAI operations."""
        logger.info("🧪 Benchmarking XAI operations...")

        try:
            from servos.xai_integration import xai_integration

            results = {}

            if not xai_integration.xai_available:
                logger.info("⚠️ XAI not configured - skipping benchmark")
                return {'xai_available': False}

            # Test XAI query (will fail without real key, but measures blocking)
            start_time = time.time()

            try:
                result = await xai_integration.query_xai("Test query for benchmarking")
                success = True
            except Exception as e:
                success = False
                logger.info(f"XAI query failed (expected): {str(e)[:50]}...")

            query_time = time.time() - start_time
            results['xai_query_time'] = query_time
            results['xai_success'] = success

            # Check if it blocked (should be fast even if failed)
            if query_time < 2:  # Should fail quickly, not block
                logger.info("✅ XAI async: No blocking detected"            else:
                logger.warning(".2f"
            return results

        except Exception as e:
            logger.error(f"❌ XAI benchmark failed: {e}")
            return {'error': str(e)}

    async def benchmark_concurrent_operations(self, num_operations: int = 100) -> Dict[str, Any]:
        """Benchmark concurrent operations."""
        logger.info(f"🧪 Benchmarking {num_operations} concurrent operations...")

        async def mock_operation(i: int):
            """Mock async operation."""
            await asyncio.sleep(0.01)  # 10ms operation
            return f"result_{i}"

        start_time = time.time()

        # Create concurrent tasks
        tasks = [asyncio.create_task(mock_operation(i)) for i in range(num_operations)]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        logger.info(".4f"        logger.info(".1f"        logger.info(".4f"
        return {
            'total_time': total_time,
            'avg_time_per_operation': total_time / num_operations,
            'operations_per_second': num_operations / total_time,
            'success_count': len(results)
        }

    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete performance benchmark."""
        logger.info("🚀 Running Full Event Loop Performance Benchmark")
        logger.info("=" * 60)

        results = {
            'timestamp': time.time(),
            'db_benchmark': await self.benchmark_db_operations(),
            'xai_benchmark': await self.benchmark_xai_operations(),
            'concurrent_benchmark': await self.benchmark_concurrent_operations(),
            'system_info': {
                'cpu_count': os.cpu_count(),
                'memory_gb': psutil.virtual_memory().total / (1024**3)
            }
        }

        # Calculate performance score
        score = self._calculate_performance_score(results)
        results['performance_score'] = score

        self._print_benchmark_results(results)

        return results

    def _calculate_performance_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)."""
        score = 100.0

        # DB performance penalties
        db_results = results.get('db_benchmark', {})
        if db_results.get('session_load', 1) > 0.1:  # Should be < 100ms
            score -= 20
        if db_results.get('bot_state_load', 0.1) > 0.05:  # Should be < 50ms
            score -= 10

        # XAI performance penalties
        xai_results = results.get('xai_benchmark', {})
        if xai_results.get('xai_query_time', 0) > 2:  # Should fail quickly
            score -= 15

        # Concurrent performance penalties
        concurrent = results.get('concurrent_benchmark', {})
        ops_per_sec = concurrent.get('operations_per_second', 0)
        if ops_per_sec < 5000:  # Should handle 5000+ ops/sec
            score -= max(0, (5000 - ops_per_sec) / 100)

        return max(0, min(100, score))

    def _print_benchmark_results(self, results: Dict[str, Any]):
        """Print formatted benchmark results."""
        logger.info("\n📊 BENCHMARK RESULTS")
        logger.info("=" * 60)

        score = results.get('performance_score', 0)
        if score >= 90:
            logger.info(f"🎉 PERFORMANCE SCORE: {score:.1f}/100 - EXCELLENT"        elif score >= 70:
            logger.info(f"✅ PERFORMANCE SCORE: {score:.1f}/100 - GOOD"        elif score >= 50:
            logger.info(f"⚠️ PERFORMANCE SCORE: {score:.1f}/100 - FAIR"        else:
            logger.info(f"❌ PERFORMANCE SCORE: {score:.1f}/100 - NEEDS IMPROVEMENT"
        # DB Results
        db = results.get('db_benchmark', {})
        logger.info("
🐘 DATABASE PERFORMANCE:"        for key, value in db.items():
            logger.info("6.4f"
        # XAI Results
        xai = results.get('xai_benchmark', {})
        logger.info("
🧠 XAI PERFORMANCE:"        for key, value in xai.items():
            if isinstance(value, bool):
                logger.info(f"  {key}: {'✅' if value else '❌'}")
            elif isinstance(value, (int, float)):
                logger.info("6.4f"
        # Concurrent Results
        concurrent = results.get('concurrent_benchmark', {})
        logger.info("
⚡ CONCURRENT PERFORMANCE:"        logger.info(".1f"        logger.info(".4f"        logger.info(".1f"
        logger.info("=" * 60)

async def main():
    """Main monitoring function."""
    monitor = EventLoopMonitor()

    try:
        # Start monitoring
        monitor.start_monitoring()

        # Run benchmarks
        results = await monitor.run_full_benchmark()

        # Recommendations
        score = results.get('performance_score', 0)
        logger.info("\n💡 RECOMMENDATIONS:")

        if score < 70:
            logger.info("• Implement Phase 1 async migration immediately")
            logger.info("• Fix XAI blocking issues")
            logger.info("• Optimize database connection pooling")

        if score >= 70 and score < 90:
            logger.info("• Consider Phase 2 optimizations")
            logger.info("• Implement advanced caching")
            logger.info("• Add more monitoring metrics")

        if score >= 90:
            logger.info("• Performance is excellent!")
            logger.info("• Focus on maintaining and monitoring")
            logger.info("• Consider Phase 3 advanced optimizations")

    finally:
        # Stop monitoring
        monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())

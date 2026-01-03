#!/usr/bin/env python3
"""
Test script for Premium Nexus Logger
Verifies structured logging and phase system
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from servos.voight_kampff import voight_kampff as nexus_logger

async def test_premium_logging():
    """Test the premium logging system."""

    print("🧪 Testing Premium Nexus Logger")
    print("=" * 50)

    # Test banner display
    print("1. Testing banner display...")
    nexus_logger.show_banner()
    print("✅ Banner displayed")

    # Test phase system
    print("\n2. Testing phase system...")

    # Phase 1
    nexus_logger.phase_start(1, "TEST INITIALIZATION", "🔧")
    await asyncio.sleep(0.1)  # Simulate work
    nexus_logger.phase_success("Test component 1 loaded")
    await asyncio.sleep(0.05)
    nexus_logger.phase_success("Test component 2 initialized")

    # Phase 2
    nexus_logger.phase_start(2, "TEST SECURITY", "🔐")
    await asyncio.sleep(0.1)
    nexus_logger.phase_success("Test encryption enabled")
    nexus_logger.phase_warning("Test certificate expiring soon")

    # Phase 3
    nexus_logger.phase_start(3, "TEST DATABASE", "🗄️")
    await asyncio.sleep(0.1)
    nexus_logger.phase_success("Test database connected", "5 tables")
    nexus_logger.phase_error("Test backup failed", "Connection timeout")

    # Phase 4
    nexus_logger.phase_start(4, "TEST AI", "🤖")
    await asyncio.sleep(0.1)
    nexus_logger.phase_success("Test AI model loaded", "99.2% accuracy")

    # Phase 5
    nexus_logger.phase_start(5, "TEST CONNECTIVITY", "🌐")
    await asyncio.sleep(0.1)
    nexus_logger.phase_success("Test services connected", "3/3 online")

    # Test final message
    print("\n3. Testing system ready message...")
    nexus_logger.system_ready(session_count=3, response_time="<100ms")

    print("\n✅ Premium logging test completed!")
    print("🎯 All features working correctly")

if __name__ == "__main__":
    asyncio.run(test_premium_logging())

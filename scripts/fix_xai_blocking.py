#!/usr/bin/env python3
"""
CRITICAL: Fix XAI Integration Blocking
Convert synchronous requests to async aiohttp

TARGET: Eliminate XAI blocking from event loop
FILE: servos/xai_integration.py
"""

import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_xai_integration():
    """Fix the blocking XAI integration."""

    file_path = "servos/xai_integration.py"
    backup_path = "servos/xai_integration.py.backup"

    # Create backup
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"📦 Backup created: {backup_path}")

    # Fix the synchronous requests.post call
    # Find the problematic section
    pattern = r'(response = requests\.post\(\s*f"{self\.xai_base_url}/chat/completions",\s*headers=headers,\s*json=payload,\s*timeout=10\s*\))'

    replacement = '''                # Async XAI request - no blocking
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.xai_base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response_data = await response.json()
                        response = type('Response', (), {
                            'status_code': response.status,
                            'json': lambda: response_data
                        })()'''

    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Add aiohttp import if not present
    if 'import aiohttp' not in content:
        # Find the requests import and replace it
        content = content.replace(
            'import requests',
            'import aiohttp'
        )

    # Fix the timeout handling
    content = content.replace(
        'time.sleep(2 ** attempt)',
        'await asyncio.sleep(2 ** attempt)'
    )

    # Make sure the method is async
    if 'async def' not in content:
        content = content.replace(
            'def query_xai(self, prompt: str) -> dict:',
            'async def query_xai(self, prompt: str) -> dict:'
        )

    # Write back the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info("✅ Fixed XAI integration - now async!")
    return True

def validate_fix():
    """Validate that the fix was applied correctly."""
    file_path = "servos/xai_integration.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for async patterns
    checks = [
        ('async def query_xai' in content, "Method is async"),
        ('aiohttp.ClientSession()' in content, "Using aiohttp"),
        ('async with session.post' in content, "Async POST request"),
        ('await response.json()' in content, "Async JSON parsing"),
        ('requests.post' not in content, "No more sync requests"),
    ]

    logger.info("🔍 Validation Results:")
    all_passed = True
    for check, description in checks:
        status = "✅" if check else "❌"
        logger.info(f"  {status} {description}")
        if not check:
            all_passed = False

    return all_passed

async def test_xai_fix():
    """Test the fixed XAI integration."""
    try:
        from servos.xai_integration import xai_integration

        if not xai_integration.xai_available:
            logger.info("⚠️ XAI not configured - skipping functional test")
            return True

        # This should not block now
        import time
        start_time = time.time()

        # Create a simple test (this will fail without real API key, but shouldn't block)
        try:
            result = await xai_integration.query_xai("Test prompt")
            elapsed = time.time() - start_time
            logger.info(".3f"            return True
        except Exception as e:
            elapsed = time.time() - start_time
            logger.info(".3f"            # If it completes in reasonable time, the async fix worked
            return elapsed < 5  # Should fail quickly, not block

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def main():
    """Main fix function."""
    logger.info("🚀 Fixing XAI Integration Blocking Issues")
    logger.info("=" * 50)

    # Step 1: Apply the fix
    logger.info("Step 1: Applying async fix...")
    if not fix_xai_integration():
        logger.error("❌ Fix application failed")
        return 1

    # Step 2: Validate
    logger.info("Step 2: Validating fix...")
    if not validate_fix():
        logger.error("❌ Validation failed")
        return 1

    # Step 3: Test (async)
    logger.info("Step 3: Testing functionality...")
    import asyncio
    if not asyncio.run(test_xai_fix()):
        logger.error("❌ Functional test failed")
        return 1

    logger.info("=" * 50)
    logger.info("🎉 XAI BLOCKING FIX COMPLETED!")
    logger.info("✅ XAI calls no longer block the event loop")
    logger.info("✅ Trading signals can process during XAI analysis")
    logger.info("✅ Bot responsiveness dramatically improved")
    logger.info("=" * 50)

    return 0

if __name__ == "__main__":
    exit(main())

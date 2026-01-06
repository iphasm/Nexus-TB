#!/usr/bin/env python3
"""
Test health checker locally
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append('.')

async def test_health_local():
    """Test if health checker can start locally"""
    print("🩺 Testing Health Checker Locally")
    print("=" * 40)

    try:
        from servos.health_checker import app, mark_service_healthy
        print("✅ Health checker module imported")

        # Mark as healthy
        mark_service_healthy()
        print("✅ Service marked as healthy")

        # Try to start server briefly
        from uvicorn import Config, Server

        port = 8000
        config = Config(
            app=app,
            host="127.0.0.1",  # Localhost for testing
            port=port,
            log_level="info",
            access_log=False
        )
        server = Server(config)

        print(f"🌐 Attempting to start health server on localhost:{port}")

        # Start server in background
        server_task = asyncio.create_task(server.serve())

        # Wait a moment for server to start
        await asyncio.sleep(2)

        # Test the endpoint
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"http://127.0.0.1:{port}/health")
                print(f"✅ Health endpoint responded: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Status: {data.get('status')}")
                    print(f"   Components: {len(data.get('components', {}))}")

                    # Test detailed endpoint
                    response2 = await client.get(f"http://127.0.0.1:{port}/health/detailed")
                    print(f"✅ Detailed endpoint: {response2.status_code}")

                return True
            except Exception as e:
                print(f"❌ Failed to connect to health endpoint: {e}")
                return False
            finally:
                # Stop server
                server.should_exit = True
                await server_task

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_health_local())
    if success:
        print("\n✅ Health checker works locally!")
        print("The issue might be with Railway network configuration or port binding.")
    else:
        print("\n❌ Health checker has issues even locally.")
        sys.exit(1)

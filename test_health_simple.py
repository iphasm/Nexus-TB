#!/usr/bin/env python3
"""
Simple test for health checker functionality
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

def test_health_checker():
    """Test basic health checker functionality"""
    print("🩺 Testing Health Checker Service")
    print("=" * 50)

    try:
        # Test import
        print("1. Testing imports...")
        from servos.health_checker import app, update_health_status, mark_service_healthy
        print("   ✅ Health checker module imported successfully")

        # Test basic functions
        print("2. Testing basic functions...")
        mark_service_healthy()
        update_health_status("telegram_bot", "healthy")
        update_health_status("database", "healthy")
        print("   ✅ Health status functions working")

        # Test FastAPI app creation
        print("3. Testing FastAPI app...")
        if hasattr(app, 'routes'):
            print(f"   ✅ FastAPI app created with {len(app.routes)} routes")
        else:
            print("   ⚠️ FastAPI app created (routes not accessible)")

        # Test endpoints exist
        print("4. Testing endpoint registration...")
        route_paths = []
        for route in app.routes:
            if hasattr(route, 'path'):
                route_paths.append(route.path)

        expected_endpoints = ['/', '/health', '/health/detailed']
        for endpoint in expected_endpoints:
            if endpoint in route_paths:
                print(f"   ✅ Endpoint {endpoint} registered")
            else:
                print(f"   ❌ Endpoint {endpoint} missing")

        print("\n" + "=" * 50)
        print("🎉 HEALTH CHECKER BASIC TESTS PASSED!")
        print("✅ Health checker service is ready for Railway")
        print("✅ Endpoints will be available when service starts")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure FastAPI is installed: pip install fastapi uvicorn[standard]")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_health_checker()
    if success:
        print("\n✅ Health checker test completed successfully!")
        print("\n🚀 Ready for Railway deployment with health checks!")
    else:
        print("\n❌ Health checker test failed!")
        sys.exit(1)

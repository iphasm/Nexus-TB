#!/usr/bin/env python3
"""
Test Client for Railway ML Training Service
Simple script to test the deployed ML service
"""

import os
import time
import requests
from ml_training_client import RailwayMLClient

def test_service():
    """Test the Railway ML service"""
    # Get service URL from environment
    service_url = os.getenv('RAILWAY_ML_URL', 'http://localhost:8000')

    print(f"🧪 Testing Railway ML Service at: {service_url}")
    print("=" * 50)

    client = RailwayMLClient(service_url)

    # Test 1: Health Check
    print("1️⃣ Testing Health Check...")
    health = client.health_check()
    if health['healthy']:
        print("✅ Health check passed")
        print(f"   Service: {health['data'].get('service', 'Unknown')}")
        print(f"   Timestamp: {health['data'].get('timestamp', 'Unknown')}")
    else:
        print("❌ Health check failed")
        print(f"   Error: {health.get('error', 'Unknown')}")
        return False

    # Test 2: Model Info
    print("\n2️⃣ Testing Model Info...")
    model_info = client.get_model_info()
    if model_info['success']:
        info = model_info['model_info']
        print("✅ Model info retrieved")
        print(f"   Model exists: {info.get('model_exists', False)}")
        print(f"   Scaler exists: {info.get('scaler_exists', False)}")
        print(f"   Model size: {info.get('model_size', 0)} bytes")
    else:
        print("❌ Failed to get model info")
        print(f"   Error: {model_info.get('error', 'Unknown')}")

    # Test 3: Training Status (should be idle)
    print("\n3️⃣ Testing Training Status...")
    status = client.get_training_status()
    if status['success']:
        status_data = status['status']
        print("✅ Training status retrieved")
        print(f"   Status: {status_data.get('status', 'unknown')}")
        print(f"   Progress: {status_data.get('progress', 0)}%")
    else:
        print("❌ Failed to get training status")
        print(f"   Error: {status.get('error', 'Unknown')}")

    # Test 4: Start Training (optional - comment out for production)
    print("\n4️⃣ Testing Training Start (SHORT TEST)...")
    test_config = {
        'candles': 1000,  # Very short for testing
        'symbols': 3,     # Few symbols for testing
        'verbose': True
    }

    print("⚠️ Starting short training test...")
    result = client.start_training(test_config)
    if result['success']:
        print("✅ Training started successfully")
        print(f"   Job ID: {result.get('job_id', 'N/A')}")

        # Monitor progress for a bit
        print("📊 Monitoring progress...")
        for i in range(5):  # Check 5 times
            time.sleep(10)  # Wait 10 seconds
            status = client.get_training_status()
            if status['success']:
                status_data = status['status']
                progress = status_data.get('progress', 0)
                current_status = status_data.get('status', 'unknown')
                print(f"   Status: {current_status} ({progress}%)")

                if current_status in ['completed', 'failed']:
                    break
            else:
                print("   Error checking status")
    else:
        print("❌ Failed to start training")
        print(f"   Error: {result.get('error', 'Unknown')}")

    print("\n" + "=" * 50)
    print("🎉 Service testing completed!")
    print("\n💡 Next steps:")
    print("1. If tests passed, the service is ready")
    print("2. Configure RAILWAY_ML_URL in your main bot")
    print("3. Use /ml_train, /ml_status, /ml_logs in Telegram")

    return True

if __name__ == "__main__":
    test_service()

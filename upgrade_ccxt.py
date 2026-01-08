#!/usr/bin/env python3
"""
Script to upgrade CCXT to latest compatible version
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    print("🚀 CCXT Upgrade Script")
    print("=" * 50)
    print("This will upgrade CCXT to version 4.4.0+ for improved conditional orders support")
    print("Compatible with Bybit V5 API and enhanced trailing stops")
    print()

    # Check current Python version
    print(f"🐍 Python version: {sys.version}")

    # Upgrade pip first
    if not run_command("python -m pip install --upgrade pip", "Upgrading pip"):
        print("⚠️ Pip upgrade failed, continuing anyway...")

    # Upgrade CCXT
    if run_command("pip install \"ccxt>=4.4.0,<5.0.0\" --upgrade", "Upgrading CCXT to 4.4.0+"):
        print("\n✅ CCXT upgrade completed successfully!")
    else:
        print("\n❌ CCXT upgrade failed!")
        print("💡 Try manual installation: pip install \"ccxt>=4.4.0,<5.0.0\" --upgrade")
        return False

    # Run compatibility test
    print("\n🧪 Running compatibility tests...")
    test_result = run_command("python check_ccxt_version.py", "Checking CCXT version")
    test_result &= run_command("python test_ccxt_compatibility.py", "Testing conditional orders compatibility")

    if test_result:
        print("\n🎉 All tests passed! CCXT upgrade successful.")
        print("\n📋 Next steps:")
        print("   1. Restart your trading bot")
        print("   2. Test conditional orders with small amounts")
        print("   3. Monitor logs for any issues")
        print("   4. Use /recover_protection if needed")
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
        print("   You may need to troubleshoot compatibility issues.")

    return test_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

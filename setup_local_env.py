#!/usr/bin/env python3
"""
Setup script for local environment variables testing.
Creates a .env file template and shows how to set environment variables.
"""

import os

def create_env_template():
    """Create a .env template file for local development."""

    template = """# Environment Variables Template for Local Development
# Copy this file to .env and fill in your actual API keys

# Railway Environment Variables (for Railway deployment)
RAILWAY_BINANCE_API_KEY=your_binance_api_key_here
RAILWAY_BINANCE_API_SECRET=your_binance_api_secret_here
RAILWAY_BYBIT_API_KEY=your_bybit_api_key_here
RAILWAY_BYBIT_API_SECRET=your_bybit_api_secret_here
RAILWAY_ALPACA_API_KEY=your_alpaca_api_key_here
RAILWAY_ALPACA_API_SECRET=your_alpaca_api_secret_here

# Standard Environment Variables (alternative)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here
BYBIT_API_KEY=your_bybit_api_key_here
BYBIT_API_SECRET=your_bybit_api_secret_here
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_API_SECRET=your_alpaca_api_secret_here

# Telegram Configuration
TELEGRAM_SUPEROWNER_ID=your_telegram_user_id_here

# Other Bot Configuration
LOG_LEVEL=INFO
PROXY_URL=
"""

    with open('.env.template', 'w') as f:
        f.write(template)

    print("✅ Created .env.template file")
    print("📝 Fill in your actual API keys and rename to .env")

def show_setup_instructions():
    """Show instructions for setting up environment variables."""

    print("\n🚀 SETUP INSTRUCTIONS")
    print("=" * 50)

    print("\n📋 FOR LOCAL DEVELOPMENT:")
    print("1. Copy .env.template to .env")
    print("2. Fill in your actual API keys")
    print("3. The bot will automatically load .env file")

    print("\n☁️ FOR RAILWAY DEPLOYMENT:")
    print("1. Go to https://railway.app")
    print("2. Select your project")
    print("3. Go to Variables in the sidebar")
    print("4. Add these variables:")
    print("   - RAILWAY_BINANCE_API_KEY")
    print("   - RAILWAY_BINANCE_API_SECRET")
    print("   - RAILWAY_BYBIT_API_KEY")
    print("   - RAILWAY_BYBIT_API_SECRET")
    print("   - RAILWAY_ALPACA_API_KEY")
    print("   - RAILWAY_ALPACA_API_SECRET")
    print("   - TELEGRAM_SUPEROWNER_ID")

    print("\n🧪 TESTING:")
    print("1. Run: python test_railway_vars.py")
    print("2. Check that variables are detected")
    print("3. Run: /railway_debug in Telegram")
    print("4. Check /exchanges status")

    print("\n⚠️ SECURITY NOTES:")
    print("- Never commit .env file to git")
    print("- Use Railway variables for production")
    print("- Keep API keys secure")

def main():
    """Main setup function."""

    print("🔧 NEXUS BOT ENVIRONMENT SETUP")
    print("=" * 40)

    # Create template
    create_env_template()

    # Show current status
    print("\n📊 CURRENT ENVIRONMENT STATUS:")
    railway_vars = ['RAILWAY_BINANCE_API_KEY', 'RAILWAY_BYBIT_API_KEY', 'RAILWAY_ALPACA_API_KEY']
    standard_vars = ['BINANCE_API_KEY', 'BYBIT_API_KEY', 'ALPACA_API_KEY']

    print("Railway variables:")
    for var in railway_vars:
        exists = bool(os.getenv(var))
        print(f"  {'✅' if exists else '❌'} {var}")

    print("Standard variables:")
    for var in standard_vars:
        exists = bool(os.getenv(var))
        print(f"  {'✅' if exists else '❌'} {var}")

    # Show instructions
    show_setup_instructions()

if __name__ == "__main__":
    main()
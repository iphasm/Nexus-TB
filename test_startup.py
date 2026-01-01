#!/usr/bin/env python3
"""
Test script to verify Railway environment and basic functionality
"""

import os
import sys
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_imports():
    """Test basic Python imports"""
    try:
        import flask
        logger.info(f"✅ Flask {flask.__version__} imported successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Flask import failed: {e}")
        return False

def test_env_vars():
    """Test environment variables"""
    required = ['BINANCE_API_KEY', 'BINANCE_API_SECRET']
    optional = ['ALPHA_VANTAGE_API_KEY', 'PORT']

    logger.info("🔍 Checking environment variables...")

    for var in required:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var} is set (length: {len(value)})")
        else:
            logger.error(f"❌ {var} is missing")

    for var in optional:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var} is set (length: {len(value)})")
        else:
            logger.warning(f"⚠️ {var} is not set")

def test_ml_imports():
    """Test ML-related imports"""
    try:
        # Test basic ML imports
        import numpy as np
        import pandas as pd
        import sklearn
        import xgboost
        import ta

        logger.info("✅ Core ML libraries imported successfully")
        logger.info(f"   - NumPy: {np.__version__}")
        logger.info(f"   - Pandas: {pd.__version__}")
        logger.info(f"   - Scikit-learn: {sklearn.__version__}")
        logger.info(f"   - XGBoost: {xgboost.__version__}")
        logger.info(f"   - TA: {ta.__version__}")

        # Test our custom imports
        from ta_compat import ta as ta_compat
        logger.info("✅ ta_compat imported successfully")

        # Test src imports (this is where it might fail)
        sys.path.append('src')
        from ml.train_cortex import fetch_data, add_indicators
        logger.info("✅ ML training modules imported successfully")

        return True

    except Exception as e:
        logger.error(f"❌ ML import failed: {e}")
        import traceback
        logger.error(f"📋 Traceback:\n{traceback.format_exc()}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 Starting Railway ML Environment Test")
    logger.info(f"🔧 Python version: {sys.version}")
    logger.info(f"📦 Working directory: {os.getcwd()}")

    # Test basic functionality
    if not test_basic_imports():
        logger.error("❌ Basic imports failed - exiting")
        sys.exit(1)

    # Test environment
    test_env_vars()

    # Test ML imports
    if not test_ml_imports():
        logger.error("❌ ML imports failed - exiting")
        sys.exit(1)

    logger.info("🎉 All tests passed! Environment is ready for ML training")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Railway ML Training Service
Cloud-based ML model training for Nexus Trading Bot

This service provides:
- Automated ML model retraining
- Cloud-based training with Railway
- Model storage and retrieval
- Training status monitoring
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import joblib
import pandas as pd
from flask import Flask, request, jsonify

# Add src to path for imports
sys.path.append('src')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

class RailwayMLTrainer:
    """ML Training service for Railway deployment"""

    def __init__(self):
        self.training_status = {
            'status': 'idle',
            'progress': 0,
            'current_symbol': '',
            'symbols_processed': 0,
            'total_symbols': 0,
            'start_time': None,
            'estimated_completion': None,
            'last_error': None
        }

    def update_status(self, **kwargs):
        """Update training status"""
        self.training_status.update(kwargs)
        logger.info(f"Training status updated: {kwargs}")

    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        return self.training_status.copy()

    def validate_environment(self) -> bool:
        """Validate Railway environment and dependencies"""
        try:
            # Check required environment variables
            required_env_vars = [
                'BINANCE_API_KEY', 'BINANCE_API_SECRET'
            ]

            # Optional environment variables
            optional_env_vars = [
                'ALPHA_VANTAGE_API_KEY'  # For Yahoo Finance fallback
            ]

            missing_vars = []
            for var in required_env_vars:
                if not os.getenv(var):
                    missing_vars.append(var)

            if missing_vars:
                self.update_status(
                    status='error',
                    last_error=f"Missing required environment variables: {', '.join(missing_vars)}"
                )
                return False

            # Log optional variables status
            for var in optional_env_vars:
                if os.getenv(var):
                    logger.info(f"✅ Optional variable {var} is configured")
                else:
                    logger.warning(f"⚠️ Optional variable {var} not configured - limited fallback available")

            # Check if we can import training modules
            try:
                from ml.train_cortex import fetch_data, add_indicators
                from ml.add_new_features import add_all_new_features
                logger.info("✅ ML training dependencies available")
            except ImportError as e:
                self.update_status(
                    status='error',
                    last_error=f"Cannot import ML modules: {e}"
                )
                return False

            # Check storage directories
            os.makedirs('nexus_system/memory_archives', exist_ok=True)
            os.makedirs('training_logs', exist_ok=True)

            logger.info("✅ Railway environment validated")
            return True

        except Exception as e:
            self.update_status(status='error', last_error=str(e))
            return False

    def start_training(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start ML model training job"""
        try:
            if self.training_status['status'] == 'running':
                return {
                    'success': False,
                    'error': 'Training already in progress'
                }

            # Validate environment
            if not self.validate_environment():
                return {
                    'success': False,
                    'error': self.training_status.get('last_error', 'Environment validation failed')
                }

            # Reset status
            self.training_status = {
                'status': 'running',
                'progress': 0,
                'current_symbol': '',
                'symbols_processed': 0,
                'total_symbols': config.get('symbols', 50),
                'start_time': datetime.now().isoformat(),
                'estimated_completion': None,
                'last_error': None,
                'config': config
            }

            # Start training in background thread
            from threading import Thread
            training_thread = Thread(target=self._run_training, args=(config,))
            training_thread.daemon = True
            training_thread.start()

            logger.info(f"🚀 ML Training started with config: {config}")

            return {
                'success': True,
                'message': 'ML training started successfully',
                'job_id': f"train_{int(time.time())}"
            }

        except Exception as e:
            logger.error(f"Failed to start training: {e}")
            self.update_status(status='error', last_error=str(e))
            return {
                'success': False,
                'error': str(e)
            }

    def _run_training(self, config: Dict[str, Any]):
        """Run the actual training process"""
        try:
            from ml.train_cortex import main as train_main

            # Prepare command line arguments
            sys.argv = ['train_cortex.py']

            if 'candles' in config:
                sys.argv.extend(['--candles', str(config['candles'])])
            if 'symbols' in config:
                sys.argv.extend(['--symbols', str(config['symbols'])])
            if config.get('verbose', False):
                sys.argv.append('--verbose')

            # Override symbols limit if specified
            if 'max_symbols' in config:
                # This would need to be handled in train_cortex.py
                pass

            self.update_status(progress=10, status='running')

            # Run training
            logger.info("🎯 Starting ML model training...")
            train_main()

            # Training completed successfully
            self.update_status(
                status='completed',
                progress=100,
                estimated_completion=datetime.now().isoformat()
            )

            logger.info("✅ ML Training completed successfully")

        except Exception as e:
            logger.error(f"ML Training failed: {e}")
            self.update_status(
                status='failed',
                last_error=str(e)
            )

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the trained model"""
        model_path = 'nexus_system/memory_archives/ml_model.pkl'
        scaler_path = 'nexus_system/memory_archives/scaler.pkl'

        info = {
            'model_exists': os.path.exists(model_path),
            'scaler_exists': os.path.exists(scaler_path),
            'model_size': 0,
            'scaler_size': 0,
            'last_modified': None
        }

        if info['model_exists']:
            info['model_size'] = os.path.getsize(model_path)
            info['last_modified'] = datetime.fromtimestamp(
                os.path.getmtime(model_path)
            ).isoformat()

        if info['scaler_exists']:
            info['scaler_size'] = os.path.getsize(scaler_path)

        return info

# Global trainer instance
trainer = RailwayMLTrainer()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'railway-ml-trainer'
    })

@app.route('/status', methods=['GET'])
def get_status():
    """Get training status"""
    return jsonify({
        'status': 'success',
        'data': trainer.get_training_status()
    })

@app.route('/train', methods=['POST'])
def start_training():
    """Start ML model training"""
    try:
        config = request.get_json() or {}

        # Default configuration
        default_config = {
            'candles': 15000,  # 15k candles for good training
            'symbols': 50,     # Limit symbols for Railway resources
            'verbose': True,
            'max_symbols': 50
        }

        # Merge with provided config
        config = {**default_config, **config}

        result = trainer.start_training(config)

        return jsonify({
            'status': 'success' if result['success'] else 'error',
            'data': result
        })

    except Exception as e:
        logger.error(f"Training request failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/model', methods=['GET'])
def get_model():
    """Get model information"""
    return jsonify({
        'status': 'success',
        'data': trainer.get_model_info()
    })

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get recent training logs"""
    try:
        # Read last 100 lines from log file if it exists
        log_files = ['training.log', 'training_logs/latest.log']
        logs = []

        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-100:]  # Last 100 lines
                    logs.extend([line.strip() for line in lines])
                break

        return jsonify({
            'status': 'success',
            'data': {
                'logs': logs[-50:],  # Return last 50 lines
                'total_lines': len(logs)
            }
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Railway configuration
    port = int(os.getenv('PORT', 8000))

    logger.info("🚀 Starting Railway ML Training Service")
    logger.info(f"📡 Listening on port {port}")

    app.run(host='0.0.0.0', port=port, debug=False)

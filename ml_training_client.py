#!/usr/bin/env python3
"""
ML Training Client for Railway
Client to interact with Railway ML Training service from the main bot
"""

import os
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RailwayMLClient:
    """Client to interact with Railway ML Training service"""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Railway ML Client

        Args:
            base_url: Railway service URL (from RAILWAY_ML_URL env var)
        """
        self.base_url = base_url or os.getenv('RAILWAY_ML_URL', 'http://localhost:8000')
        self.session = requests.Session()
        self.session.timeout = 30

    def health_check(self) -> Dict[str, Any]:
        """Check if Railway ML service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return {
                'healthy': True,
                'data': response.json()
            }
        except Exception as e:
            logger.error(f"Railway ML health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e)
            }

    def start_training(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start ML model training on Railway

        Args:
            config: Training configuration
                - candles: Number of candles (default: 15000)
                - symbols: Number of symbols to train (default: 50)
                - verbose: Enable verbose logging (default: True)
        """
        if config is None:
            config = {}

        # Default configuration optimized for Railway
        default_config = {
            'candles': 15000,
            'symbols': 50,  # Limit for Railway resources
            'verbose': True
        }

        training_config = {**default_config, **config}

        try:
            logger.info(f"🚀 Starting ML training on Railway with config: {training_config}")
            response = self.session.post(
                f"{self.base_url}/train",
                json=training_config,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()

            result = response.json()
            if result.get('status') == 'success':
                logger.info("✅ ML training started successfully on Railway")
                return {
                    'success': True,
                    'job_id': result.get('data', {}).get('job_id'),
                    'message': result.get('data', {}).get('message')
                }
            else:
                logger.error(f"❌ Failed to start ML training: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error')
                }

        except Exception as e:
            logger.error(f"❌ Error starting ML training: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status from Railway"""
        try:
            response = self.session.get(f"{self.base_url}/status")
            response.raise_for_status()

            result = response.json()
            return {
                'success': True,
                'status': result.get('data', {})
            }

        except Exception as e:
            logger.error(f"❌ Error getting training status: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the trained model"""
        try:
            response = self.session.get(f"{self.base_url}/model")
            response.raise_for_status()

            result = response.json()
            return {
                'success': True,
                'model_info': result.get('data', {})
            }

        except Exception as e:
            logger.error(f"❌ Error getting model info: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_training_logs(self, lines: int = 50) -> Dict[str, Any]:
        """Get recent training logs from Railway"""
        try:
            response = self.session.get(f"{self.base_url}/logs")
            response.raise_for_status()

            result = response.json()
            logs = result.get('data', {}).get('logs', [])

            return {
                'success': True,
                'logs': logs[-lines:] if logs else [],
                'total_lines': len(logs)
            }

        except Exception as e:
            logger.error(f"❌ Error getting training logs: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def format_training_status(self, status_data: Dict[str, Any]) -> str:
        """Format training status for display"""
        if not status_data:
            return "❌ No se pudo obtener el estado del entrenamiento"

        status = status_data.get('status', 'unknown')
        progress = status_data.get('progress', 0)
        current_symbol = status_data.get('current_symbol', '')
        symbols_processed = status_data.get('symbols_processed', 0)
        total_symbols = status_data.get('total_symbols', 0)

        # Status emoji
        status_emoji = {
            'idle': '⏸️',
            'running': '🚀',
            'completed': '✅',
            'failed': '❌',
            'error': '💥'
        }.get(status, '❓')

        message = f"{status_emoji} **Estado del Entrenamiento ML**\n"
        message += f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += f"**Estado:** {status.upper()}\n"
        message += f"**Progreso:** {progress}%\n"

        if status == 'running':
            message += f"**Símbolo actual:** {current_symbol or 'N/A'}\n"
            message += f"**Progreso:** {symbols_processed}/{total_symbols} símbolos\n"

            if status_data.get('start_time'):
                start_time = datetime.fromisoformat(status_data['start_time'].replace('Z', '+00:00'))
                elapsed = datetime.now() - start_time
                message += f"**Tiempo transcurrido:** {elapsed.seconds // 3600}h {(elapsed.seconds % 3600) // 60}m\n"

        if status_data.get('last_error'):
            message += f"\n**Último error:** {status_data['last_error'][:200]}...\n"

        if status == 'completed':
            message += f"\n🎉 **Entrenamiento completado exitosamente!**\n"
            message += f"El nuevo modelo ML está listo para usar.\n"

        return message

# Convenience functions for bot integration
def start_ml_training(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function to start ML training"""
    client = RailwayMLClient()
    return client.start_training(config)

def get_ml_training_status() -> Dict[str, Any]:
    """Convenience function to get training status"""
    client = RailwayMLClient()
    return client.get_training_status()

def format_ml_status(status_data: Dict[str, Any]) -> str:
    """Convenience function to format training status"""
    client = RailwayMLClient()
    return client.format_training_status(status_data)

# Example usage for testing
if __name__ == '__main__':
    # Test the client
    client = RailwayMLClient()

    print("Testing Railway ML Client...")

    # Health check
    health = client.health_check()
    print(f"Health check: {health}")

    # Start training (uncomment to test)
    # result = client.start_training({'candles': 1000, 'symbols': 5})
    # print(f"Training start: {result}")

    print("Client test completed.")

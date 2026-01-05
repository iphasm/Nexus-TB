"""
Model Sync - Downloads ML models from PostgreSQL
Allows Nexus-TB to use models trained by the ML Trainer worker.
"""

import os
import io
import joblib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

import psycopg2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache for loaded model
_cached_model = None
_cached_scaler = None
_cached_version = None


def get_db_connection():
    """Get PostgreSQL connection from DATABASE_URL environment variable."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # Railway uses postgres:// but psycopg2 needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return psycopg2.connect(database_url)


def init_ml_models_table():
    """Create the ml_models table if it doesn't exist."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ml_models (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    model_blob BYTEA NOT NULL,
                    scaler_blob BYTEA NOT NULL,
                    accuracy FLOAT,
                    cv_score FLOAT,
                    feature_names TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB,
                    is_active BOOLEAN DEFAULT TRUE
                );
                
                CREATE INDEX IF NOT EXISTS idx_ml_models_version ON ml_models(version);
                CREATE INDEX IF NOT EXISTS idx_ml_models_created_at ON ml_models(created_at DESC);
            """)
            conn.commit()
            logger.info("✅ ml_models table initialized")
    except Exception as e:
        logger.error(f"❌ Error initializing ml_models table: {e}")
        raise
    finally:
        conn.close()


def get_model_info() -> Optional[Dict]:
    """Get information about the latest model without downloading the blob."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT version, accuracy, cv_score, feature_names, metadata, created_at,
                       LENGTH(model_blob) as model_size,
                       LENGTH(scaler_blob) as scaler_size
                FROM ml_models
                WHERE is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                'version': row[0],
                'accuracy': row[1],
                'cv_score': row[2],
                'feature_names': row[3],
                'metadata': row[4],
                'created_at': row[5].isoformat() if row[5] else None,
                'model_size_kb': row[6] / 1024 if row[6] else 0,
                'scaler_size_kb': row[7] / 1024 if row[7] else 0
            }
    except Exception as e:
        logger.error(f"❌ Error getting model info: {e}")
        return None
    finally:
        conn.close()


def load_model_from_db(force_reload: bool = False) -> Optional[Tuple[Dict, Any, Dict]]:
    """
    Download the latest active model from PostgreSQL.
    Uses caching to avoid repeated downloads.
    
    Args:
        force_reload: If True, bypass cache and download fresh model
    
    Returns:
        Tuple of (model_data, scaler, info) or None if not found
    """
    global _cached_model, _cached_scaler, _cached_version
    
    # Check if we have a cached model and don't need to reload
    if not force_reload and _cached_model is not None:
        logger.info(f"📦 Using cached model: {_cached_version}")
        return _cached_model, _cached_scaler, {'version': _cached_version, 'cached': True}
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT model_blob, scaler_blob, version, accuracy, cv_score, feature_names, metadata, created_at
                FROM ml_models
                WHERE is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            row = cur.fetchone()
            if not row:
                logger.warning("⚠️ No active model found in database")
                return None
            
            model_blob, scaler_blob, version, accuracy, cv_score, feature_names, metadata, created_at = row
            
            # Deserialize
            model_data = joblib.load(io.BytesIO(model_blob))
            scaler = joblib.load(io.BytesIO(scaler_blob))
            
            info = {
                'version': version,
                'accuracy': accuracy,
                'cv_score': cv_score,
                'feature_names': feature_names,
                'metadata': metadata,
                'created_at': created_at.isoformat() if created_at else None,
                'cached': False
            }
            
            # Update cache
            _cached_model = model_data
            _cached_scaler = scaler
            _cached_version = version
            
            logger.info(f"✅ Model loaded from DB: {version} (Accuracy: {accuracy:.3f})")
            
            return model_data, scaler, info
            
    except Exception as e:
        logger.error(f"❌ Error loading model from DB: {e}")
        return None
    finally:
        conn.close()


def check_for_new_model() -> Optional[str]:
    """
    Check if there's a newer model available than the cached one.
    
    Returns:
        New version string if available, None if no update needed
    """
    global _cached_version
    
    try:
        info = get_model_info()
        if not info:
            return None
        
        db_version = info['version']
        
        if _cached_version is None:
            logger.info(f"🆕 No cached model, new model available: {db_version}")
            return db_version
        
        if db_version != _cached_version:
            logger.info(f"🆕 New model available: {db_version} (current: {_cached_version})")
            return db_version
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error checking for new model: {e}")
        return None


def get_cached_model() -> Optional[Tuple[Dict, Any]]:
    """
    Get the cached model without database access.
    
    Returns:
        Tuple of (model_data, scaler) or None if not cached
    """
    global _cached_model, _cached_scaler
    
    if _cached_model is None:
        return None
    
    return _cached_model, _cached_scaler


def clear_cache():
    """Clear the model cache, forcing next load to fetch from DB."""
    global _cached_model, _cached_scaler, _cached_version
    _cached_model = None
    _cached_scaler = None
    _cached_version = None
    logger.info("🗑️ Model cache cleared")


async def model_sync_task(check_interval: int = 3600):
    """
    Background task that periodically checks for new models.
    
    Args:
        check_interval: Seconds between checks (default: 1 hour)
    """
    import asyncio
    
    logger.info(f"🔄 Model sync task started (check every {check_interval}s)")
    
    while True:
        try:
            new_version = check_for_new_model()
            if new_version:
                logger.info(f"📥 Downloading new model: {new_version}")
                load_model_from_db(force_reload=True)
        except Exception as e:
            logger.error(f"❌ Model sync error: {e}")
        
        await asyncio.sleep(check_interval)


def format_model_status() -> str:
    """Format model status for Telegram display."""
    info = get_model_info()
    
    if not info:
        return "❌ **No hay modelo ML activo en la base de datos.**"
    
    cached = "✅ Sí" if _cached_version == info['version'] else "❌ No"
    
    return (
        f"🧠 **Estado del Modelo ML**\n\n"
        f"📦 **Versión:** `{info['version']}`\n"
        f"🎯 **Accuracy:** `{info['accuracy']:.1%}`\n"
        f"📊 **CV Score:** `{info['cv_score']:.1%}`\n"
        f"📅 **Entrenado:** `{info['created_at'][:10] if info['created_at'] else 'N/A'}`\n"
        f"💾 **Tamaño:** `{info['model_size_kb']:.1f} KB`\n"
        f"🔄 **En Caché:** {cached}\n"
    )


if __name__ == "__main__":
    # Test connection
    print("🔧 Testing Model Sync...")
    
    info = get_model_info()
    if info:
        print(f"📊 Current model: {info['version']}")
        print(f"   Accuracy: {info['accuracy']:.3f}")
        print(f"   Created: {info['created_at']}")
    else:
        print("📭 No models found in database")
    
    # Try loading
    result = load_model_from_db()
    if result:
        model_data, scaler, info = result
        print(f"✅ Model loaded successfully!")
        print(f"   Features: {len(model_data.get('feature_names', []))}")
    else:
        print("❌ Failed to load model")

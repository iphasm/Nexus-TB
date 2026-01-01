import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .classifier import MarketClassifier, MarketRegime
from servos.indicators import calculate_ema, calculate_rsi, calculate_atr, calculate_adx
import pandas_ta as ta

# Define paths to model artifacts
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'memory_archives', 'ml_model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '..', 'memory_archives', 'scaler.pkl')

# Confidence threshold - below this, fallback to rule-based
CONFIDENCE_THRESHOLD = 0.70

class MLClassifier:
    """
    Advanced Classifier using Machine Learning (XGBoost) - v3.1
    
    Logic:
    1. Loads pre-trained model from 'nexus_system/memory_archives/ml_model.pkl'.
    2. Loads scaler from 'nexus_system/memory_archives/scaler.pkl'.
    3. Transforms market_data into feature vector and scales it.
    4. Predicts optimal strategy label with confidence threshold.
    5. Falls back to Rule-Based Classifier if model is missing, low confidence, or error.
    """
    
    _model = None
    _label_encoder = None
    _feature_names = None
    _scaler = None
    _model_loaded = False
    
    @classmethod
    def load_model(cls):
        if cls._model_loaded:
            return

        # Load model bundle (model + label_encoder + feature_names)
        if os.path.exists(MODEL_PATH):
            try:
                model_data = joblib.load(MODEL_PATH)
                if isinstance(model_data, dict):
                    cls._model = model_data.get('model')
                    cls._label_encoder = model_data.get('label_encoder')
                    cls._feature_names = model_data.get('feature_names')
                else:
                    # Legacy format (just the model)
                    cls._model = model_data
                    cls._label_encoder = None
                    cls._feature_names = None
                print(f"🧠 ML Classifier: Model loaded from {MODEL_PATH}")
            except Exception as e:
                print(f"⚠️ ML Classifier: Failed to load model: {e}")
                return
        else:
            return
        
        # Load scaler
        if os.path.exists(SCALER_PATH):
            try:
                cls._scaler = joblib.load(SCALER_PATH)
                print(f"🧠 ML Classifier: Scaler loaded from {SCALER_PATH}")
            except Exception as e:
                print(f"⚠️ ML Classifier: Failed to load scaler: {e}")
                cls._scaler = None
        else:
            print(f"⚠️ ML Classifier: Scaler not found at {SCALER_PATH}")
            cls._scaler = None
        
        cls._model_loaded = True

    @staticmethod
    def _extract_features(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Extracts features from the dataframe for the model.
        MUST match the training feature set (v3.2 - 79 features expandidas).
        Uses the same pipeline as training: add_indicators() + add_all_new_features()
        """
        if df is None or df.empty or len(df) < 50:
            return None

        try:
            # Import functions from the organized ML module
            try:
                from src.ml.train_cortex import add_indicators
                from src.ml.add_new_features import add_all_new_features
            except ImportError:
                # Fallback to compatibility imports
                try:
                    from compatibility_imports import fetch_data, add_indicators
                    from compatibility_imports import add_all_new_features
                except ImportError:
                    # Last resort: calculate basic features only
                    print("⚠️  ML features extraction failed - using basic features only")
                    return cls._extract_basic_features(df)

            # Apply the same feature engineering pipeline as training
            df_with_indicators = add_indicators(df.copy())
            df_with_all_features = add_all_new_features(df_with_indicators)

            # Extract the feature columns that match training (X_cols from train_cortex.py)
            X_cols = [
                # Core (original)
                'rsi', 'adx', 'atr_pct', 'trend_str', 'vol_change',
                # v3.0 features
                'macd_hist_norm', 'bb_pct', 'bb_width',
                'roc_5', 'roc_10', 'obv_change',
                'price_position', 'body_pct',
                'above_ema200', 'ema_cross',
                # NEW v3.1 features (reduce ATR dependence)
                'ema20_slope', 'mfi', 'dist_50_high', 'dist_50_low',
                'hour_of_day', 'day_of_week',
                # NEW v3.2 features (further reduce ATR dependence)
                # Momentum features
                'roc_21', 'roc_50', 'williams_r', 'cci', 'ultimate_osc',
                # Volume features
                'volume_roc_5', 'volume_roc_21', 'chaikin_mf', 'force_index', 'ease_movement',
                # Structure features
                'dist_sma20', 'dist_sma50', 'pivot_dist', 'fib_dist',
                # Correlation features
                'morning_volatility', 'afternoon_volatility', 'gap_up', 'gap_down', 'range_change',
                # Sentiment features
                'bull_power', 'bear_power', 'momentum_div', 'vpt', 'intraday_momentum'
            ]

            # Filter to available features (some may not be calculated if data is insufficient)
            available_features = [col for col in X_cols if col in df_with_all_features.columns]

            if len(available_features) < len(X_cols):
                missing = [col for col in X_cols if col not in df_with_all_features.columns]
                print(f"⚠️  Missing features during inference: {len(missing)} features")
                print(f"   Missing: {missing[:5]}..." if len(missing) > 5 else f"   Missing: {missing}")

            if not available_features:
                print("❌ No features available for inference")
                return None

            # Return the feature vector (last row only, as numpy array)
            features_df = df_with_all_features[available_features].iloc[-1:].copy()

            return features_df
            
            return features_df
            
        except Exception as e:
            print(f"⚠️ ML Feature Extraction Error: {e}")
            return None


    @classmethod
    def classify(cls, market_data: Dict[str, Any]) -> Optional[MarketRegime]:
        """
        Predicts regime using ML model. Returns None if:
        - Model missing/fails
        - Confidence below CONFIDENCE_THRESHOLD (0.70)
        - Asset not in training data (bypass for new assets)
        """
        # Ensure model is loaded
        if not cls._model_loaded:
            cls.load_model()

        if not cls._model:
            return None # Trigger fallback

        # 🔄 BYPASS CHECK: If asset is not in training data, skip ML and use rule-based
        # This prevents errors with newly added assets before model retraining
        symbol = market_data.get('symbol', '')
        if hasattr(cls, '_feature_names') and cls._feature_names:
            # If we have feature names but asset wasn't in training, skip ML
            # This is a temporary bypass until model is retrained with all assets
            if symbol and not any(symbol.upper() in str(name).upper() for name in cls._feature_names[:10]):
                print(f"🔄 ML Bypass: {symbol} not in training data, using rule-based classifier")
                return None  # Trigger fallback to rule-based

        features = cls._extract_features(market_data.get('dataframe'))
        if features is None:
            return None
            
        try:
            # Apply scaler if available
            if cls._scaler is not None:
                features_scaled = cls._scaler.transform(features)
            else:
                features_scaled = features.values  # Use raw features if no scaler
            
            # Predict
            prediction = cls._model.predict(features_scaled)[0]
            
            # Get probabilities
            confidence = 0.8 # Default
            if hasattr(cls._model, "predict_proba"):
                probs = cls._model.predict_proba(features_scaled)
                confidence = float(np.max(probs))
            
            # CONFIDENCE THRESHOLD CHECK
            if confidence < CONFIDENCE_THRESHOLD:
                # Low confidence - fallback to rule-based
                return None
            
            # Decode prediction if label encoder is available
            if cls._label_encoder is not None:
                pred_label = cls._label_encoder.inverse_transform([prediction])[0]
            else:
                pred_label = str(prediction)
            
            # Map Prediction Label to Regime/Strategy
            strategy_map = {
                "trend": ("TREND", "TrendFollowing"),
                "scalp": ("VOLATILE", "Scalping"),
                "grid": ("RANGE_TIGHT", "Grid"),
                "mean_rev": ("RANGE_WIDE", "MeanReversion")
            }
            
            # Handle if prediction is int or string
            pred_key = str(pred_label).lower()
            
            # Mapping logic
            if "trend" in pred_key: mapping = strategy_map["trend"]
            elif "scalp" in pred_key: mapping = strategy_map["scalp"]
            elif "grid" in pred_key: mapping = strategy_map["grid"]
            else: mapping = strategy_map["mean_rev"]
            
            return MarketRegime(
                regime=mapping[0],
                suggested_strategy=mapping[1],
                confidence=confidence,
                reason=f"🤖 ML Prediction ({pred_key.upper()}, conf: {confidence:.0%})"
            )
            
        except Exception as e:
            print(f"⚠️ ML Inference Error: {e}")
            return None

    @staticmethod
    def _extract_basic_features(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Fallback feature extraction with basic features only.
        Used when expanded feature extraction fails.
        """
        if df is None or df.empty or len(df) < 50:
            return None

        try:
            last = df.iloc[-1]
            close = last.get('close', 1.0)
            high = last.get('high', close)
            low = last.get('low', close)
            open_price = last.get('open', close)

            # Basic features only (subset of training features)
            features_dict = {
                'rsi': last.get('rsi', 50),
                'adx': last.get('adx', 0),
                'atr_pct': (last.get('atr', 0) / close) * 100 if close > 0 else 0,
                'trend_str': 0,  # Will be calculated if EMAs available
                'vol_change': 0,  # Simplified
                'macd_hist_norm': 0,
                'bb_pct': 0.5,
                'bb_width': 0,
                'roc_5': 0,
                'roc_10': 0,
                'obv_change': 0,
                'price_position': 0.5,
                'body_pct': abs(close - open_price) / (high - low + 1e-10),
                'above_ema200': 0,
                'ema_cross': 0,
                'ema20_slope': 0,
                'mfi': 50,
                'dist_50_high': 0,
                'dist_50_low': 0,
                'hour_of_day': 12,
                'day_of_week': 0
            }

            # Calculate trend_str if EMAs are available
            if 'ema_20' in last and 'ema_50' in last:
                ema_20 = last.get('ema_20', close)
                ema_50 = last.get('ema_50', close)
                features_dict['trend_str'] = (ema_20 - ema_50) / close * 100 if close > 0 else 0

            # Create DataFrame with single row
            features_df = pd.DataFrame([features_dict])
            return features_df

        except Exception as e:
            print(f"❌ Error in basic feature extraction: {e}")
            return None


import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .classifier import MarketClassifier, MarketRegime

# Define paths to model artifacts
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'scaler.pkl')

# Confidence threshold - below this, fallback to rule-based
CONFIDENCE_THRESHOLD = 0.70

class MLClassifier:
    """
    Advanced Classifier using Machine Learning (XGBoost) - v3.1
    
    Logic:
    1. Loads pre-trained model from 'antigravity_quantum/data/ml_model.pkl'.
    2. Loads scaler from 'antigravity_quantum/data/scaler.pkl'.
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
    def _calculate_mfi(df, period=14):
        """Calculate Money Flow Index (volume-weighted RSI alternative)"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        raw_money_flow = typical_price * df['volume']
        
        price_change = typical_price.diff()
        positive_flow = np.where(price_change > 0, raw_money_flow, 0)
        negative_flow = np.where(price_change < 0, raw_money_flow, 0)
        
        positive_sum = pd.Series(positive_flow).rolling(period).sum()
        negative_sum = pd.Series(negative_flow).rolling(period).sum()
        
        mfr = positive_sum / (negative_sum + 1e-10)
        mfi = 100 - (100 / (1 + mfr))
        
        return mfi.iloc[-1] if len(mfi) > 0 else 50

    @staticmethod
    def _extract_features(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Extracts features from the dataframe for the model.
        MUST match the training feature set (v3.1 - 21 features).
        Returns DataFrame with named columns to avoid sklearn warning.
        """
        if df is None or df.empty or len(df) < 50:
            return None
            
        try:
            last = df.iloc[-1]
            close = last.get('close', 1.0)
            high = last.get('high', close)
            low = last.get('low', close)
            open_price = last.get('open', close)
            
            # === CORE FEATURES ===
            rsi = last.get('rsi', 50)
            adx = last.get('adx', 0)
            atr = last.get('atr', 0)
            atr_pct = (atr / close) * 100 if close > 0 else 0
            
            # Trend Strength
            ema_20 = last.get('ema_20', close)
            ema_50 = last.get('ema_50', close)
            trend_str = (ema_20 - ema_50) / close * 100 if close > 0 else 0
            
            # Volume Change (rolling calculation)
            vol = df['volume'].iloc[-5:].mean() if 'volume' in df.columns else 0
            vol_20 = df['volume'].iloc[-20:].mean() if 'volume' in df.columns else 1
            vol_change = (vol - vol_20) / (vol_20 + 1e-10)
            
            # === v3.0 FEATURES ===
            
            # MACD Histogram Normalized
            ema_12 = df['close'].ewm(span=12, adjust=False).mean().iloc[-1]
            ema_26 = df['close'].ewm(span=26, adjust=False).mean().iloc[-1]
            macd = ema_12 - ema_26
            macd_signal = df['close'].ewm(span=12, adjust=False).mean().ewm(span=9, adjust=False).mean().iloc[-1] - \
                         df['close'].ewm(span=26, adjust=False).mean().ewm(span=9, adjust=False).mean().iloc[-1]
            macd_hist_norm = (macd - macd_signal) / close * 100 if close > 0 else 0
            
            # Bollinger Bands
            bb_middle = df['close'].rolling(20).mean().iloc[-1]
            bb_std = df['close'].rolling(20).std().iloc[-1]
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            bb_width = (bb_std * 2) / (bb_middle + 1e-10) * 100
            bb_pct = (close - bb_lower) / (bb_upper - bb_lower + 1e-10)
            
            # Rate of Change
            close_5 = df['close'].iloc[-6] if len(df) > 5 else close
            close_10 = df['close'].iloc[-11] if len(df) > 10 else close
            roc_5 = (close - close_5) / close_5 * 100 if close_5 > 0 else 0
            roc_10 = (close - close_10) / close_10 * 100 if close_10 > 0 else 0
            
            # OBV Change
            obv_change = vol_change  # Simplified approximation
            
            # Price Position (20 period)
            high_20 = df['high'].iloc[-20:].max() if 'high' in df.columns else high
            low_20 = df['low'].iloc[-20:].min() if 'low' in df.columns else low
            price_position = (close - low_20) / (high_20 - low_20 + 1e-10)
            
            # Candle Body Percentage
            body_pct = abs(close - open_price) / (high - low + 1e-10)
            
            # Trend Direction
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1] if len(df) >= 200 else ema_50
            ema_9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
            above_ema200 = 1 if close > ema_200 else 0
            ema_cross = 1 if ema_9 > ema_20 else 0
            
            # === NEW v3.1 FEATURES ===
            
            # EMA20 Slope (momentum direction)
            ema_20_series = df['close'].ewm(span=20, adjust=False).mean()
            ema20_current = ema_20_series.iloc[-1]
            ema20_5back = ema_20_series.iloc[-6] if len(ema_20_series) > 5 else ema20_current
            ema20_slope = (ema20_current - ema20_5back) / close * 100 if close > 0 else 0
            
            # MFI (Money Flow Index)
            mfi = MLClassifier._calculate_mfi(df, period=14)
            
            # Distance to 50-period High/Low
            high_50 = df['high'].iloc[-50:].max() if len(df) >= 50 and 'high' in df.columns else high
            low_50 = df['low'].iloc[-50:].min() if len(df) >= 50 and 'low' in df.columns else low
            dist_50_high = (close - high_50) / close * 100 if close > 0 else 0
            dist_50_low = (close - low_50) / close * 100 if close > 0 else 0
            
            # Time-based features
            if 'timestamp' in df.columns:
                try:
                    ts = df['timestamp'].iloc[-1]
                    if hasattr(ts, 'hour'):
                        hour_of_day = ts.hour
                        day_of_week = ts.dayofweek
                    else:
                        hour_of_day = 12
                        day_of_week = 2
                except:
                    hour_of_day = 12
                    day_of_week = 2
            else:
                hour_of_day = 12
                day_of_week = 2
            
            # Feature names MUST match training order (21 features for v3.1)
            feature_names = [
                'rsi', 'adx', 'atr_pct', 'trend_str', 'vol_change',
                'macd_hist_norm', 'bb_pct', 'bb_width',
                'roc_5', 'roc_10', 'obv_change',
                'price_position', 'body_pct',
                'above_ema200', 'ema_cross',
                'ema20_slope', 'mfi', 'dist_50_high', 'dist_50_low',
                'hour_of_day', 'day_of_week'
            ]
            
            feature_values = [
                rsi, adx, atr_pct, trend_str, vol_change,
                macd_hist_norm, bb_pct, bb_width,
                roc_5, roc_10, obv_change,
                price_position, body_pct,
                above_ema200, ema_cross,
                ema20_slope, mfi, dist_50_high, dist_50_low,
                hour_of_day, day_of_week
            ]
            
            # Return as DataFrame with named columns (fixes sklearn warning)
            features_df = pd.DataFrame([feature_values], columns=feature_names)
            
            # Replace NaNs and Infs
            features_df = features_df.replace([np.inf, -np.inf], 0).fillna(0)
            
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
        """
        # Ensure model is loaded
        if not cls._model_loaded:
            cls.load_model()
            
        if not cls._model:
            return None # Trigger fallback
            
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

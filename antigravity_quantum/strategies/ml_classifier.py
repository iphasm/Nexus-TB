import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .classifier import MarketClassifier, MarketRegime

# Define path to the model
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_model.pkl')

class MLClassifier:
    """
    Advanced Classifier using Machine Learning (Random Forest / XGBoost).
    
    Logic:
    1. Loads pre-trained model from 'antigravity_quantum/data/ml_model.pkl'.
    2. Transforms market_data into feature vector.
    3. Predicts optimal strategy label.
    4. Falls back to Rule-Based Classifier if model is missing or low confidence.
    """
    
    _model = None
    _model_loaded = False
    
    @classmethod
    def load_model(cls):
        if cls._model_loaded:
            return

        if os.path.exists(MODEL_PATH):
            try:
                cls._model = joblib.load(MODEL_PATH)
                cls._model_loaded = True
                print(f"🧠 ML Classifier: Model loaded from {MODEL_PATH}")
            except Exception as e:
                print(f"⚠️ ML Classifier: Failed to load model: {e}")
        else:
            # Silent fail - Factory handles fallback
            pass

    @staticmethod
    def _extract_features(df: pd.DataFrame) -> Optional[np.ndarray]:
        """
        Extracts features from the dataframe for the model.
        MUST match the training feature set (v3.0 - 15 features).
        """
        if df is None or df.empty or len(df) < 26:
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
            
            # === NEW v3.0 FEATURES ===
            
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
            
            # Price Position
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
            
            # Feature Vector - MUST MATCH TRAINING ORDER
            features = np.array([[
                rsi, adx, atr_pct, trend_str, vol_change,
                macd_hist_norm, bb_pct, bb_width,
                roc_5, roc_10, obv_change,
                price_position, body_pct,
                above_ema200, ema_cross
            ]])
            
            # Replace NaNs and Infs
            features = np.nan_to_num(features, nan=0, posinf=0, neginf=0)
            
            return features
            
        except Exception as e:
            print(f"⚠️ ML Feature Extraction Error: {e}")
            return None


    @classmethod
    def classify(cls, market_data: Dict[str, Any]) -> Optional[MarketRegime]:
        """
        Predicts regime using ML model. Returns None if model missing/fails.
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
            # Predict
            prediction = cls._model.predict(features)[0]
            # Probabilities (if model supports it)
            confidence = 0.8 # Default
            if hasattr(cls._model, "predict_proba"):
                probs = cls._model.predict_proba(features)
                confidence = float(np.max(probs))
            
            # Map Prediction Label to Regime/Strategy
            # Labels: 0=mean_rev, 1=trend, 2=scalp, 3=grid
            # This mapping depends on how the model was trained.
            # Assuming string labels for simplicity:
            
            strategy_map = {
                "trend": ("TREND", "TrendFollowing"),
                "scalp": ("VOLATILE", "Scalping"),
                "grid": ("RANGE_TIGHT", "Grid"),
                "mean_rev": ("RANGE_WIDE", "MeanReversion")
            }
            
            # Handle if prediction is int or string
            pred_key = str(prediction).lower()
            
            # Mapping logic (example)
            if "trend" in pred_key: mapping = strategy_map["trend"]
            elif "scalp" in pred_key: mapping = strategy_map["scalp"]
            elif "grid" in pred_key: mapping = strategy_map["grid"]
            else: mapping = strategy_map["mean_rev"]
            
            return MarketRegime(
                regime=mapping[0],
                suggested_strategy=mapping[1],
                confidence=confidence,
                reason=f"🤖 ML Prediction ({pred_key.upper()})"
            )
            
        except Exception as e:
            print(f"⚠️ ML Inference Error: {e}")
            return None

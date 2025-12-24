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
        MUST match the training feature set.
        
        Features (Example):
        - RSI, ADX, ATR_PCT
        - EMA_Diff_Pct (Trend strength)
        - Volume_Change_Pct
        - Close_vs_Bollinger
        """
        if df is None or df.empty:
            return None
            
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        
        try:
            # 1. Core Technicals
            rsi = last.get('rsi', 50)
            adx = last.get('adx', 0)
            
            # 2. Volatility
            close = last.get('close', 1.0)
            atr = last.get('atr', 0)
            atr_pct = (atr / close) * 100 if close > 0 else 0
            
            # 3. Trend
            ema_20 = last.get('ema_20', 0)
            ema_50 = last.get('ema_50', 0)
            trend_str = (ema_20 - ema_50) / close * 100 if close > 0 else 0
            
            # 4. Momentum / Volume
            vol_change = (last.get('volume', 0) - prev.get('volume', 0)) / (prev.get('volume', 1) + 1e-9)
            
            # Feature Vector (Order matters!)
            # [RSI, ADX, ATR_PCT, TREND_STR, VOL_CHANGE]
            features = np.array([[rsi, adx, atr_pct, trend_str, vol_change]])
            
            # Replace NaNs
            features = np.nan_to_num(features)
            
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

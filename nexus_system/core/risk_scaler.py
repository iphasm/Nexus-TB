"""
Risk Scaler - Sistema de Escalado Dinámico de Riesgo
Ajusta parámetros de trading basado en confianza de señal + régimen de mercado.
"""
from typing import Dict, Any, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import numpy as np


class MarketRegime(Enum):
    TREND = "TREND"
    RANGE = "RANGE"
    VOLATILE = "VOLATILE"
    UNCERTAIN = "UNCERTAIN"


class ConfidenceLevel(Enum):
    VERY_LOW = "VERY_LOW"      # < 0.3
    LOW = "LOW"               # 0.3 - 0.5
    MEDIUM = "MEDIUM"         # 0.5 - 0.7
    HIGH = "HIGH"             # 0.7 - 0.85
    VERY_HIGH = "VERY_HIGH"   # > 0.85


@dataclass
class RiskMultipliers:
    """Multiplicadores de riesgo calculados dinámicamente"""
    leverage_multiplier: float = 1.0
    size_multiplier: float = 1.0
    stop_loss_multiplier: float = 1.0  # Más amplio = menos restrictivo
    take_profit_multiplier: float = 1.0  # Más amplio = más conservador
    max_holding_multiplier: float = 1.0  # Más alto = permite holds más largos


class RiskScaler:
    """
    Escala dinámicamente el riesgo basado en:
    1. Confianza de la señal (confidence score)
    2. Régimen de mercado actual (market regime)
    3. Combinación estratégica de ambos factores
    """

    def __init__(self):
        # Tabla de scaling base por régimen
        self.regime_base_scaling = {
            MarketRegime.TREND: {
                'leverage': 1.2,      # Aumentar leverage en trends
                'size': 1.3,          # Aumentar size en trends
                'sl': 1.5,           # SL más amplio para dar espacio
                'tp': 0.8,           # TP más agresivo
                'holding': 1.5       # Permitir holds más largos
            },
            MarketRegime.RANGE: {
                'leverage': 0.8,      # Reducir leverage en ranges
                'size': 0.9,          # Reducir size en ranges
                'sl': 0.8,           # SL más ajustado
                'tp': 1.2,           # TP más conservador
                'holding': 0.8       # Holds más cortos
            },
            MarketRegime.VOLATILE: {
                'leverage': 0.6,      # Mucho más conservador
                'size': 0.5,          # Size muy reducido
                'sl': 0.6,           # SL muy ajustado
                'tp': 1.5,           # TP muy conservador
                'holding': 0.5       # Holds muy cortos
            },
            MarketRegime.UNCERTAIN: {
                'leverage': 0.7,      # Conservador por defecto
                'size': 0.7,          # Size reducido
                'sl': 0.9,           # SL ligeramente ajustado
                'tp': 1.1,           # TP conservador
                'holding': 0.9       # Holds normales
            }
        }

        # Ajustes adicionales por nivel de confianza
        self.confidence_adjustments = {
            ConfidenceLevel.VERY_LOW: {
                'leverage': 0.5, 'size': 0.4, 'sl': 0.7, 'tp': 1.3, 'holding': 0.6
            },
            ConfidenceLevel.LOW: {
                'leverage': 0.7, 'size': 0.6, 'sl': 0.8, 'tp': 1.2, 'holding': 0.8
            },
            ConfidenceLevel.MEDIUM: {
                'leverage': 1.0, 'size': 1.0, 'sl': 1.0, 'tp': 1.0, 'holding': 1.0
            },
            ConfidenceLevel.HIGH: {
                'leverage': 1.2, 'size': 1.2, 'sl': 1.1, 'tp': 0.9, 'holding': 1.2
            },
            ConfidenceLevel.VERY_HIGH: {
                'leverage': 1.4, 'size': 1.4, 'sl': 1.2, 'tp': 0.8, 'holding': 1.4
            }
        }

        # Ajustes especiales por estrategia + régimen
        self.strategy_regime_overrides = {
            'Scalping': {
                MarketRegime.VOLATILE: {'leverage': 1.5, 'size': 1.2, 'holding': 0.3},  # Scalping brilla en volatilidad
                MarketRegime.TREND: {'leverage': 0.8, 'size': 0.8},  # Menos efectivo en trends largos
            },
            'Grid': {
                MarketRegime.RANGE: {'leverage': 1.3, 'size': 1.4, 'holding': 2.0},  # Grid perfecto para ranges
                MarketRegime.TREND: {'leverage': 0.6, 'size': 0.6},  # Menos efectivo en trends
            },
            'MeanReversion': {
                MarketRegime.RANGE: {'leverage': 1.2, 'size': 1.3, 'holding': 1.5},  # Excelente en ranges
                MarketRegime.VOLATILE: {'leverage': 0.7, 'size': 0.7},  # Cuidado con volatility
            },
            'TrendFollowing': {
                MarketRegime.TREND: {'leverage': 1.5, 'size': 1.6, 'holding': 2.5},  # Perfecto para trends
                MarketRegime.RANGE: {'leverage': 0.5, 'size': 0.5},  # Terrible en ranges
            }
        }

    def classify_confidence(self, confidence: float) -> ConfidenceLevel:
        """Clasifica el nivel de confianza en categorías"""
        if confidence < 0.3:
            return ConfidenceLevel.VERY_LOW
        elif confidence < 0.5:
            return ConfidenceLevel.LOW
        elif confidence < 0.7:
            return ConfidenceLevel.MEDIUM
        elif confidence < 0.85:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH

    def detect_market_regime(self, market_data: Dict[str, Any]) -> MarketRegime:
        """
        Detecta el régimen de mercado usando MarketClassifier
        """
        try:
            from nexus_system.cortex.classifier import MarketClassifier

            regime_data = MarketClassifier.classify(market_data)
            if regime_data and 'regime' in regime_data:
                regime_str = regime_data['regime'].split('_')[0]  # Remove _TIGHT/_WIDE suffix
                return MarketRegime(regime_str)
            else:
                return MarketRegime.UNCERTAIN
        except Exception as e:
            print(f"⚠️ Regime detection error: {e}")
            return MarketRegime.UNCERTAIN

    def calculate_risk_multipliers(self,
                                 confidence: float,
                                 strategy: str,
                                 market_data: Optional[Dict[str, Any]] = None) -> RiskMultipliers:
        """
        Calcula multiplicadores de riesgo basados en confianza + régimen + estrategia
        """

        # 1. Clasificar confianza
        confidence_level = self.classify_confidence(confidence)

        # 2. Detectar régimen de mercado
        regime = MarketRegime.UNCERTAIN
        if market_data:
            regime = self.detect_market_regime(market_data)

        # 3. Obtener scaling base del régimen
        regime_scaling = self.regime_base_scaling[regime]

        # 4. Aplicar ajustes por confianza
        confidence_adj = self.confidence_adjustments[confidence_level]

        # 5. Aplicar overrides específicos de estrategia + régimen
        strategy_override = {}
        if strategy in self.strategy_regime_overrides:
            if regime in self.strategy_regime_overrides[strategy]:
                strategy_override = self.strategy_regime_overrides[strategy][regime]

        # 6. Combinar todos los factores
        final_multipliers = RiskMultipliers()

        for attr in ['leverage', 'size', 'sl', 'tp', 'holding']:
            # Base del régimen
            base = regime_scaling[attr]

            # Ajuste por confianza
            confidence_mult = confidence_adj[attr]

            # Override de estrategia (si existe)
            strategy_mult = strategy_override.get(attr, 1.0)

            # Combinación final (con clamping para evitar extremos)
            final_value = base * confidence_mult * strategy_mult
            final_value = np.clip(final_value, 0.3, 3.0)  # Limitar entre 0.3x y 3.0x

            setattr(final_multipliers, f"{attr}_multiplier", final_value)

        return final_multipliers

    def get_scaling_explanation(self,
                               confidence: float,
                               strategy: str,
                               market_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Proporciona explicación detallada del scaling aplicado
        """
        confidence_level = self.classify_confidence(confidence)
        regime = self.detect_market_regime(market_data) if market_data else MarketRegime.UNCERTAIN
        multipliers = self.calculate_risk_multipliers(confidence, strategy, market_data)

        explanation = (
            f"🎯 Risk Scaling: Confianza {confidence_level.value} ({confidence:.1%}) + "
            f"Régimen {regime.value}\n"
            f"   Leverage: {multipliers.leverage_multiplier:.1f}x | "
            f"Size: {multipliers.size_multiplier:.1f}x | "
            f"SL: {multipliers.stop_loss_multiplier:.1f}x | "
            f"TP: {multipliers.take_profit_multiplier:.1f}x"
        )

        # Añadir nota especial si hay overrides
        if strategy in self.strategy_regime_overrides and regime in self.strategy_regime_overrides[strategy]:
            explanation += f"\n   📌 Override {strategy} aplicado en régimen {regime.value}"

        return explanation

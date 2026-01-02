"""
Risk Policy Engine - Fase 2: Centralización de Lógica de Riesgo
Unifica aprobación de trades, límites de exposición y ajustes dinámicos de tamaño.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TradeAction(Enum):
    OPEN_LONG = "OPEN_LONG"
    OPEN_SHORT = "OPEN_SHORT"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"
    EXIT_ALL = "EXIT_ALL"


@dataclass
class StrategyIntent:
    """Representa la intención de una estrategia de trading"""
    symbol: str
    action: str  # OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT, EXIT_ALL
    strategy_key: str  # TREND, GRID, MEAN_REVERSION, SCALPING, SENTINEL
    confidence: float
    price: float
    atr: float | None
    metadata: Dict[str, Any]


@dataclass
class Position:
    """Posición actual en la cartera"""
    symbol: str
    side: str  # LONG, SHORT
    quantity: float
    entry_price: float
    exchange: str
    unrealized_pnl: float = 0.0
    notional_value: float = 0.0


@dataclass
class PortfolioState:
    """Estado completo de la cartera para evaluación de riesgo"""
    positions: List[Position]
    exposure_notional_by_exchange: Dict[str, float]
    exposure_by_cluster: Dict[str, float]  # cluster = subgroup (MAJOR_CAPS, MEME_COINS, etc.)
    net_direction_exposure: Dict[str, float]  # long_notional, short_notional
    drawdown: float
    corr_matrix: Dict[Tuple[str, str], float]   # sobre returns
    corr_to_bench: Dict[str, float]         # corr con BTC/ETH, opcional


@dataclass
class RiskDecision:
    """Decisión de riesgo con ajustes dinámicos"""
    allow: bool
    reason: str
    target_exchange: str
    leverage: int
    size_pct: float
    sl_price: float | None
    tp_price: float | None
    adjustments: Dict[str, Any]  # Para ajustes adicionales (multipliers, etc.)


@dataclass
class ExecutionPlan:
    """Plan completo de ejecución"""
    exchange: str
    symbol: str
    leverage: int
    entry_qty: float
    entry_order: Dict[str, Any]
    sl_order: Dict[str, Any] | None
    tp_order: Dict[str, Any] | None


class RiskPolicy:
    """
    Motor Central de Política de Riesgo

    Responsabilidades:
    - Evaluar intención vs estado de cartera
    - Aplicar límites por símbolo/cluster/exchange/dirección
    - Ajustar tamaño dinámicamente basado en correlación/drawdown/volatilidad
    - Proporcionar decisiones de riesgo unificadas
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cluster_caps = config.get('cluster_caps', {
            'MAJOR_CAPS': 0.40,    # BTC, ETH, etc.
            'L1_L2': 0.25,         # SOL, AVAX, etc.
            'MEME_COINS': 0.10,    # PEPE, DOGE, etc.
            'DEFI': 0.15,          # UNI, AAVE, etc.
            'OTHERS': 0.10
        })

        # Límites dinámicos basados en drawdown
        self.drawdown_multipliers = {
            0.05: 1.0,    # 5% DD: normal
            0.10: 0.8,    # 10% DD: 80% size
            0.15: 0.5,    # 15% DD: 50% size
            0.20: 0.2     # 20% DD: 20% size
        }

    def evaluate(self, intent: StrategyIntent, portfolio: PortfolioState) -> RiskDecision:
        """
        Evalúa intención de trade vs estado de cartera.
        Retorna decisión con ajustes dinámicos de tamaño.
        """
        # 0) Hard stops globales
        if self.config.get('mode', 'PILOT') != 'PILOT':
            return self._deny("Modo no PILOT")

        # 1) Exchange routing (según preferencias y disponibilidad)
        target_exchange = self._route_symbol(intent.symbol)

        # 2) Validaciones básicas
        if intent.price <= 0 or intent.confidence < self.config.get('min_confidence', 0.0):
            return self._deny("Confianza/precio inválidos")

        # 3) Cluster exposure budgets
        cluster = self._get_subgroup(intent.symbol)
        current_cluster_exposure = portfolio.exposure_by_cluster.get(cluster, 0.0)
        if current_cluster_exposure >= self.cluster_caps.get(cluster, 0.10):
            return self._deny(f"Cluster cap excedido ({cluster}: {current_cluster_exposure:.1%})")

        # 4) Symbol exposure limits (máximo 10% por símbolo individual)
        symbol_limit = self.config.get('max_symbol_exposure', 0.10)
        current_symbol_exposure = sum(p.notional_value for p in portfolio.positions if p.symbol == intent.symbol)
        if current_symbol_exposure >= symbol_limit:
            return self._deny(f"Símbolo expuesto al límite ({intent.symbol}: {current_symbol_exposure:.1%})")

        # 5) Net direction limits (prevenir bias direccional extremo)
        net_long = portfolio.net_direction_exposure.get('long', 0.0)
        net_short = portfolio.net_direction_exposure.get('short', 0.0)
        total_exposure = net_long + net_short

        if total_exposure > 0:
            direction_bias = abs(net_long - net_short) / total_exposure
            max_bias = self.config.get('max_direction_bias', 0.7)  # Máximo 70% bias
            if direction_bias > max_bias:
                return self._deny(f"Bias direccional extremo ({direction_bias:.1%})")

        # 6) Correlation guard (si está habilitado)
        if self.config.get('correlation_guard_enabled', True):
            ok, msg = self._check_correlation(intent.symbol, portfolio)
            if not ok:
                return self._deny(msg)

        # 7) Calcular parámetros base con ajustes dinámicos
        base_leverage = min(self.config.get('leverage', 5), self.config.get('max_leverage_allowed', 5))
        base_size_pct = min(self.config.get('max_capital_pct', 0.10), self.config.get('max_capital_pct_allowed', 0.10))

        # Aplicar ajustes dinámicos
        adjusted_size_pct = self._apply_dynamic_adjustments(base_size_pct, intent, portfolio)

        # 8) SL/TP calculation (usando ATR si disponible)
        sl_price, tp_price = self._compute_sl_tp(intent, self.config)

        return RiskDecision(
            allow=True,
            reason="Aprobado",
            target_exchange=target_exchange,
            leverage=base_leverage,
            size_pct=adjusted_size_pct,
            sl_price=sl_price,
            tp_price=tp_price,
            adjustments={}
        )

    def _deny(self, reason: str) -> RiskDecision:
        """Helper para decisiones de denegación"""
        return RiskDecision(
            allow=False,
            reason=reason,
            target_exchange="",
            leverage=1,
            size_pct=0.0,
            sl_price=None,
            tp_price=None,
            adjustments={}
        )

    def _route_symbol(self, symbol: str) -> str:
        """Determina exchange destino basado en reglas de routing"""
        # Usar lógica de session si está disponible, sino fallback
        try:
            # Intentar acceder a session para usar su lógica de routing
            # Por ahora, simplificado - expandir después
            is_crypto = 'USDT' in symbol or 'BTC' in symbol
            if is_crypto:
                # Preferencias por defecto: BINANCE para crypto
                crypto_pref = self.config.get('crypto_exchange', 'BINANCE')
                return crypto_pref if crypto_pref in ['BINANCE', 'BYBIT'] else 'BINANCE'
            else:
                return 'ALPACA'
        except:
            # Fallback seguro
            is_crypto = 'USDT' in symbol or 'BTC' in symbol
            return 'BINANCE' if is_crypto else 'ALPACA'

    def _get_subgroup(self, symbol: str) -> str:
        """Clasifica símbolo en subgrupos para control de exposición"""
        major_caps = {'BTCUSDT', 'ETHUSDT', 'BNBUSDT'}
        l1_l2 = {'SOLUSDT', 'AVAXUSDT', 'MATICUSDT', 'FTMUSDT', 'NEARUSDT'}
        meme_coins = {'PEPEUSDT', 'DOGEUSDT', 'SHIBUSDT', 'WIFUSDT'}
        defi = {'UNIUSDT', 'AAVEUSDT', 'SUSHIUSDT', 'COMPUSDT'}

        if symbol in major_caps:
            return 'MAJOR_CAPS'
        elif symbol in l1_l2:
            return 'L1_L2'
        elif symbol in meme_coins:
            return 'MEME_COINS'
        elif symbol in defi:
            return 'DEFI'
        else:
            return 'OTHERS'

    def _check_correlation(self, symbol: str, portfolio: PortfolioState) -> Tuple[bool, str]:
        """Verifica correlación con posiciones existentes"""
        # Usar correlation guard existente
        # Por ahora, implementación simplificada
        return True, ""

    def _apply_dynamic_adjustments(self, base_size_pct: float, intent: StrategyIntent, portfolio: PortfolioState) -> float:
        """Aplica ajustes dinámicos basados en condiciones de mercado/cartera"""
        adjusted = base_size_pct

        # 1) Drawdown adjustment
        for dd_threshold, multiplier in self.drawdown_multipliers.items():
            if portfolio.drawdown >= dd_threshold:
                adjusted *= multiplier
                break

        # 2) Volatility adjustment (si ATR disponible)
        if intent.atr and intent.price > 0:
            atr_pct = (intent.atr / intent.price) * 100
            if atr_pct > 3.0:  # Alta volatilidad
                adjusted *= 0.7
            elif atr_pct > 5.0:  # Volatilidad extrema
                adjusted *= 0.5

        # 3) Correlation adjustment (si símbolo altamente correlacionado)
        corr_to_bench = portfolio.corr_to_bench.get(intent.symbol, 0.0)
        if abs(corr_to_bench) > 0.8:  # Alta correlación con benchmark
            adjusted *= 0.8

        return min(adjusted, base_size_pct)  # Nunca aumentar sobre base

    def _compute_sl_tp(self, intent: StrategyIntent, config: Dict[str, Any]) -> Tuple[float | None, float | None]:
        """Calcula precios de SL/TP usando ATR o porcentajes"""
        if not intent.price > 0:
            return None, None

        # Usar ATR si disponible
        if intent.atr and intent.atr > 0:
            mult = config.get('atr_multiplier', 2.0)
            sl_dist = mult * intent.atr
            tp_dist = mult * config.get('tp_ratio', 2.0) * intent.atr

            if intent.action == "OPEN_LONG":
                sl_price = intent.price - sl_dist
                tp_price = intent.price + tp_dist
            elif intent.action == "OPEN_SHORT":
                sl_price = intent.price + sl_dist
                tp_price = intent.price - tp_dist
            else:
                return None, None
        else:
            # Fallback a porcentajes
            stop_pct = config.get('stop_loss_pct', 0.02)
            tp_ratio = config.get('tp_ratio', 1.5)

            if intent.action == "OPEN_LONG":
                sl_price = intent.price * (1 - stop_pct)
                tp_price = intent.price * (1 + (stop_pct * tp_ratio))
            elif intent.action == "OPEN_SHORT":
                sl_price = intent.price * (1 + stop_pct)
                tp_price = intent.price * (1 - (stop_pct * tp_ratio))
            else:
                return None, None

        return sl_price, tp_price


async def build_portfolio_state(session, shadow_wallet) -> PortfolioState:
    """
    Construye estado completo de la cartera desde ShadowWallet y Bridge
    """
    positions = []
    exposure_notional_by_exchange = {'BINANCE': 0.0, 'BYBIT': 0.0, 'ALPACA': 0.0}
    exposure_by_cluster = {}
    net_direction_exposure = {'long': 0.0, 'short': 0.0}

    try:
        # Obtener posiciones activas del bridge
        if session.bridge:
            bridge_positions = await session.bridge.get_positions()
            for pos_data in bridge_positions:
                symbol = pos_data.get('symbol', '')
                qty = float(pos_data.get('quantity', 0) or pos_data.get('amt', 0))
                entry_price = float(pos_data.get('entry', 0) or pos_data.get('avgPrice', 0))
                exchange = pos_data.get('exchange', 'BINANCE')  # Default assumption

                if abs(qty) > 0.001:  # Ignorar posiciones dust
                    side = 'LONG' if qty > 0 else 'SHORT'
                    notional_value = abs(qty) * entry_price

                    pos = Position(
                        symbol=symbol,
                        side=side,
                        quantity=abs(qty),
                        entry_price=entry_price,
                        exchange=exchange,
                        notional_value=notional_value
                    )
                    positions.append(pos)

                    # Actualizar exposiciones
                    exposure_notional_by_exchange[exchange] = exposure_notional_by_exchange.get(exchange, 0.0) + notional_value

                    cluster = _get_subgroup(symbol)
                    exposure_by_cluster[cluster] = exposure_by_cluster.get(cluster, 0.0) + notional_value

                    # Exposición direccional
                    if side == 'LONG':
                        net_direction_exposure['long'] += notional_value
                    else:
                        net_direction_exposure['short'] += notional_value
    except Exception as e:
        print(f"⚠️ Error building portfolio state: {e}")
        # Fallback: usar datos de ShadowWallet si bridge falla
        pass

    # Calcular drawdown (simplificado - implementar con historical P&L)
    # Por ahora, usar un valor conservador basado en configuración
    drawdown = 0.0  # TODO: implementar cálculo real con historial de P&L

    return PortfolioState(
        positions=positions,
        exposure_notional_by_exchange=exposure_notional_by_exchange,
        exposure_by_cluster=exposure_by_cluster,
        net_direction_exposure=net_direction_exposure,
        drawdown=drawdown,
        corr_matrix={},  # TODO: implementar cálculo de correlaciones
        corr_to_bench={}  # TODO: implementar correlación con benchmark
    )


def _get_subgroup(symbol: str) -> str:
    """Clasifica símbolo en subgrupos para control de exposición"""
    major_caps = {'BTCUSDT', 'ETHUSDT', 'BNBUSDT'}
    l1_l2 = {'SOLUSDT', 'AVAXUSDT', 'MATICUSDT', 'FTMUSDT', 'NEARUSDT'}
    meme_coins = {'PEPEUSDT', 'DOGEUSDT', 'SHIBUSDT', 'WIFUSDT', '1000PEPEUSDT'}
    defi = {'UNIUSDT', 'AAVEUSDT', 'SUSHIUSDT', 'COMPUSDT'}

    if any(cap in symbol for cap in major_caps):
        return 'MAJOR_CAPS'
    elif any(l1 in symbol for l1 in l1_l2):
        return 'L1_L2'
    elif any(meme in symbol for meme in meme_coins):
        return 'MEME_COINS'
    elif any(defi_token in symbol for defi_token in defi):
        return 'DEFI'
    else:
        return 'OTHERS'

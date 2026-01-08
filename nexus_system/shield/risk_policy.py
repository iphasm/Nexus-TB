"""
Risk Policy Engine - Fase 2: Centralización de Lógica de Riesgo
Unifica aprobación de trades, límites de exposición y ajustes dinámicos de tamaño.
"""
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from nexus_system.core.risk_scaler import RiskMultipliers


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
    - Aplicar risk-scaling dinámico por confianza + régimen de mercado
    - Proporcionar decisiones de riesgo unificadas
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cluster_caps = config.get('cluster_caps', {
            'MAJOR_CAPS': 0.40,    # BTC, ETH, etc.
            'L1_L2': 0.25,         # SOL, AVAX, etc.
            'MEME_COINS': 0.10,    # PEPE, DOGE, etc.
            'DEFI': 0.15,          # UNI, AAVE, etc.
            'AI_TECH': 0.10,       # WLD, INJ - NUEVO
            'OTHERS': 0.10
        })

        # NUEVO: Caps específicos para tokens muy volátiles
        self.symbol_specific_caps = config.get('symbol_specific_caps', {
            'PONKEUSDT': 0.02,     # Max 2% en tokens muy nuevos
            'WIFUSDT': 0.03,
            '1000PEPEUSDT': 0.03,
            'XAIUSDT': 0.02,
            'PENDLEUSDT': 0.03,
            'FLOWUSDT': 0.03
        })

        # NUEVO: Grupos con alta correlación conocida (para correlation guard)
        self.high_corr_groups = {
            'L1_ALTS': {'SOLUSDT', 'AVAXUSDT', 'NEARUSDT', 'ALGOUSDT'},
            'ETH_ECOSYSTEM': {'ARBUSDT', 'MATICUSDT', 'LDOUSDT', 'OPUSDT'},
            'MEMES': {'DOGEUSDT', 'SHIBUSDT', 'WIFUSDT', '1000PEPEUSDT', 'PONKEUSDT'},
            'LEGACY_L1': {'LTCUSDT', 'BCHUSDT', 'ETCUSDT'}
        }

        # Límites dinámicos basados en drawdown
        self.drawdown_multipliers = {
            0.05: 1.0,    # 5% DD: normal
            0.10: 0.8,    # 10% DD: 80% size
            0.15: 0.5,    # 15% DD: 50% size
            0.20: 0.2     # 20% DD: 20% size
        }

        # Risk Scaler para ajuste dinámico
        from nexus_system.core.risk_scaler import RiskScaler, RiskMultipliers
        self.risk_scaler = RiskScaler()

    def evaluate(self, intent: StrategyIntent, portfolio: PortfolioState, market_data: Optional[Dict[str, Any]] = None) -> RiskDecision:
        """
        Evalúa intención de trade vs estado de cartera.
        Aplica risk-scaling dinámico por confianza + régimen.
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

        # 4b) NUEVO: Symbol-specific caps para tokens volátiles
        specific_cap = self.symbol_specific_caps.get(intent.symbol)
        if specific_cap and current_symbol_exposure >= specific_cap:
            return self._deny(f"Cap específico alcanzado ({intent.symbol}: {specific_cap:.1%})")

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

        # 7) Aplicar RISK SCALING DINÁMICO
        risk_multipliers = self.risk_scaler.calculate_risk_multipliers(
            confidence=intent.confidence,
            strategy=intent.strategy_key,
            market_data=market_data
        )

        # Calcular parámetros base con risk scaling
        base_leverage = min(self.config.get('leverage', 5), self.config.get('max_leverage_allowed', 5))
        base_size_pct = min(self.config.get('max_capital_pct', 0.10), self.config.get('max_capital_pct_allowed', 0.10))

        # Aplicar multiplicadores de risk scaling
        scaled_leverage = base_leverage * risk_multipliers.leverage_multiplier
        scaled_size_pct = base_size_pct * risk_multipliers.size_multiplier

        # Aplicar ajustes dinámicos adicionales (drawdown, etc.)
        final_size_pct = self._apply_dynamic_adjustments(scaled_size_pct, intent, portfolio)

        # 8) SL/TP calculation (usando ATR si disponible, con scaling)
        sl_price, tp_price = self._compute_sl_tp(intent, self.config, risk_multipliers)

        # 9) Preparar explicación del scaling aplicado
        scaling_explanation = self.risk_scaler.get_scaling_explanation(
            intent.confidence, intent.strategy_key, market_data
        )

        return RiskDecision(
            allow=True,
            reason=f"Aprobado\n{scaling_explanation}",
            target_exchange=target_exchange,
            leverage=min(scaled_leverage, self.config.get('max_leverage_allowed', 20)),  # Hard cap
            size_pct=min(final_size_pct, self.config.get('max_capital_pct_allowed', 0.25)),  # Hard cap
            sl_price=sl_price,
            tp_price=tp_price,
            adjustments={
                'risk_multipliers': risk_multipliers,
                'scaling_explanation': scaling_explanation
            }
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
        """Clasifica símbolo en subgrupos para control de exposición - SINCRONIZADO con settings.py"""
        major_caps = {'BTCUSDT', 'ETHUSDT', 'BNBUSDT'}
        
        l1_l2 = {
            # Core L1
            'SOLUSDT', 'AVAXUSDT', 'NEARUSDT', 'ALGOUSDT', 'XRPUSDT',
            # L2/Scaling  
            'ARBUSDT', 'MATICUSDT',
            # Legacy L1
            'LTCUSDT', 'BCHUSDT', 'ETCUSDT'
        }
        
        meme_coins = {
            'PEPEUSDT', '1000PEPEUSDT',  # PEPE variants
            'DOGEUSDT', 'SHIBUSDT',      # OG Memes
            'WIFUSDT', 'PONKEUSDT'       # Nuevos memes
        }
        
        defi = {
            'UNIUSDT', 'AAVEUSDT', 'SUSHIUSDT', 'COMPUSDT',
            'CRVUSDT', 'SNXUSDT', 'LDOUSDT', 'DYDXUSDT'
        }
        
        ai_tech = {'WLDUSDT', 'INJUSDT'}  # Nuevo cluster
        
        # Orden de prioridad (memes primero para evitar falsos positivos)
        if symbol in major_caps:
            return 'MAJOR_CAPS'
        elif symbol in meme_coins:
            return 'MEME_COINS'
        elif symbol in l1_l2:
            return 'L1_L2'
        elif symbol in defi:
            return 'DEFI'
        elif symbol in ai_tech:
            return 'AI_TECH'
        else:
            return 'OTHERS'

    def _check_correlation(self, symbol: str, portfolio: PortfolioState) -> Tuple[bool, str]:
        """
        Verifica correlación con posiciones existentes.
        Limita posiciones en grupos de alta correlación conocida.
        """
        # Máximo de posiciones permitidas por grupo de alta correlación
        max_per_corr_group = self.config.get('max_per_correlation_group', 2)
        
        # Encontrar si el símbolo pertenece a un grupo de alta correlación
        symbol_group = None
        for group_name, symbols in self.high_corr_groups.items():
            if symbol in symbols:
                symbol_group = group_name
                break
        
        if not symbol_group:
            # El símbolo no está en ningún grupo de alta correlación
            return True, ""
        
        # Contar posiciones existentes en el mismo grupo
        existing_in_group = sum(
            1 for p in portfolio.positions 
            if p.symbol in self.high_corr_groups[symbol_group]
        )
        
        if existing_in_group >= max_per_corr_group:
            group_symbols = ', '.join(list(self.high_corr_groups[symbol_group])[:3]) + '...'
            return False, f"Max posiciones en grupo {symbol_group} ({existing_in_group}/{max_per_corr_group}). Similar a: {group_symbols}"
        
        # También verificar correlación real si está disponible en portfolio
        if portfolio.corr_matrix:
            max_corr_threshold = self.config.get('max_correlation', 0.85)
            for pos in portfolio.positions:
                key = (symbol, pos.symbol)
                reverse_key = (pos.symbol, symbol)
                corr = portfolio.corr_matrix.get(key) or portfolio.corr_matrix.get(reverse_key)
                
                if corr and abs(corr) > max_corr_threshold:
                    return False, f"Alta correlación con {pos.symbol} ({corr:.2f})"
        
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

    def _compute_sl_tp(self, intent: StrategyIntent, config: Dict[str, Any], risk_multipliers: Optional['RiskMultipliers'] = None) -> Tuple[float | None, float | None]:
        """Calcula precios de SL/TP usando ATR o porcentajes"""
        if not intent.price > 0:
            return None, None

        # Aplicar risk multipliers si disponibles
        sl_mult = risk_multipliers.stop_loss_multiplier if risk_multipliers else 1.0
        tp_mult = risk_multipliers.take_profit_multiplier if risk_multipliers else 1.0

        # Debug multipliers
        if intent.action == "OPEN_SHORT":
            print(f"🔍 SHORT Multipliers: sl_mult={sl_mult:.3f}, tp_mult={tp_mult:.3f}, risk_multipliers={risk_multipliers}")

        # Usar ATR si disponible
        if intent.atr and intent.atr > 0:
            mult = config.get('atr_multiplier', 2.0)
            base_sl_dist = mult * intent.atr
            base_tp_dist = mult * config.get('tp_ratio', 2.0) * intent.atr

            # Aplicar scaling
            sl_dist = base_sl_dist * sl_mult
            tp_dist = base_tp_dist * tp_mult

            # Debug logging for SHORT positions
            if intent.action == "OPEN_SHORT":
                print(f"🔍 SHORT ATR Calc: price={intent.price:.6f}, atr={intent.atr:.6f}, mult={mult}, sl_mult={sl_mult:.3f}, tp_mult={tp_mult:.3f}")
                print(f"🔍 SHORT Distances: sl_dist={sl_dist:.6f}, tp_dist={tp_dist:.6f}")
                print(f"🔍 SHORT Final: sl_price={intent.price + sl_dist:.6f}, tp_price={intent.price - tp_dist:.6f}")

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
            print(f"🔍 FALLBACK TO PERCENTAGES: ATR not available or zero (atr={intent.atr})")
            stop_pct = config.get('stop_loss_pct', 0.02)
            tp_ratio = config.get('tp_ratio', 1.5)

            # Aplicar scaling: SL más ajustado si confianza alta, TP más agresivo
            scaled_stop_pct = stop_pct / sl_mult  # SL más ajustado = menor distancia
            scaled_tp_ratio = tp_ratio * tp_mult  # TP más agresivo = mayor distancia

            # Debug logging for SHORT positions
            if intent.action == "OPEN_SHORT":
                print(f"🔍 SHORT SL/TP Percent Debug: price={intent.price:.6f}, stop_pct={stop_pct:.4f}, tp_ratio={tp_ratio:.2f}")
                print(f"🔍 SHORT Scaling: sl_mult={sl_mult:.3f}, tp_mult={tp_mult:.3f}, scaled_stop_pct={scaled_stop_pct:.6f}, scaled_tp_ratio={scaled_tp_ratio:.2f}")
                print(f"🔍 SHORT Percent Calc: sl_price={intent.price * (1 + scaled_stop_pct):.6f}, tp_price={intent.price * (1 - (scaled_stop_pct * scaled_tp_ratio)):.6f}")

            if intent.action == "OPEN_LONG":
                sl_price = intent.price * (1 - scaled_stop_pct)
                tp_price = intent.price * (1 + (scaled_stop_pct * scaled_tp_ratio))
            elif intent.action == "OPEN_SHORT":
                sl_price = intent.price * (1 + scaled_stop_pct)
                tp_price = intent.price * (1 - (scaled_stop_pct * scaled_tp_ratio))
            else:
                return None, None

        # Final debug logging
        if intent.action == "OPEN_SHORT":
            print(f"🔍 SHORT FINAL RESULT: sl_price={sl_price:.6f}, tp_price={tp_price:.6f}")

        return sl_price, tp_price


async def build_portfolio_state(session, shadow_wallet) -> PortfolioState:
    """
    Construye estado completo de la cartera desde ShadowWallet y Bridge.
    MEJORADO: Calcula drawdown real basado en P&L no realizado.
    """
    positions = []
    exposure_notional_by_exchange = {'BINANCE': 0.0, 'BYBIT': 0.0, 'ALPACA': 0.0}
    exposure_by_cluster = {}
    net_direction_exposure = {'long': 0.0, 'short': 0.0}
    total_unrealized_pnl = 0.0

    try:
        # Obtener posiciones activas del bridge
        if session.bridge:
            bridge_positions = await session.bridge.get_positions()
            for pos_data in bridge_positions:
                symbol = pos_data.get('symbol', '')
                qty = float(pos_data.get('quantity', 0) or pos_data.get('amt', 0))
                entry_price = float(pos_data.get('entry', 0) or pos_data.get('avgPrice', 0))
                exchange = pos_data.get('exchange', 'BINANCE')  # Default assumption
                unrealized_pnl = float(pos_data.get('unrealizedPnl', 0) or pos_data.get('unRealizedProfit', 0))

                if abs(qty) > 0.001:  # Ignorar posiciones dust
                    side = 'LONG' if qty > 0 else 'SHORT'
                    notional_value = abs(qty) * entry_price

                    pos = Position(
                        symbol=symbol,
                        side=side,
                        quantity=abs(qty),
                        entry_price=entry_price,
                        exchange=exchange,
                        notional_value=notional_value,
                        unrealized_pnl=unrealized_pnl
                    )
                    positions.append(pos)

                    # Acumular P&L no realizado
                    total_unrealized_pnl += unrealized_pnl

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

    # NUEVO: Calcular drawdown real basado en P&L no realizado
    drawdown = 0.0
    try:
        # Obtener equity total
        total_equity = 0.0
        if shadow_wallet:
            # Intentar obtener equity de ShadowWallet
            wallet_data = shadow_wallet.get_combined_balance() if hasattr(shadow_wallet, 'get_combined_balance') else None
            if wallet_data:
                total_equity = float(wallet_data.get('total', 0) or wallet_data.get('equity', 0))
        
        # Si no tenemos equity de shadow_wallet, intentar obtenerlo de session
        if total_equity <= 0 and session:
            if hasattr(session, 'get_total_equity'):
                total_equity = await session.get_total_equity() or 0.0
            elif hasattr(session, 'bridge') and session.bridge:
                try:
                    equity_data = await session.bridge.get_total_equity()
                    total_equity = float(equity_data) if equity_data else 0.0
                except:
                    pass
        
        # Calcular drawdown como pérdida no realizada / equity total
        if total_equity > 0 and total_unrealized_pnl < 0:
            drawdown = abs(total_unrealized_pnl) / total_equity
            drawdown = min(drawdown, 1.0)  # Cap at 100%
        
        # Si hay pérdidas significativas, loguear
        if drawdown > 0.05:
            print(f"📉 Portfolio drawdown: {drawdown:.1%} (P&L: ${total_unrealized_pnl:.2f}, Equity: ${total_equity:.2f})")
    
    except Exception as e:
        print(f"⚠️ Error calculating drawdown: {e}")
        # Fallback conservador: asumir 5% DD si falla el cálculo
        drawdown = 0.05

    return PortfolioState(
        positions=positions,
        exposure_notional_by_exchange=exposure_notional_by_exchange,
        exposure_by_cluster=exposure_by_cluster,
        net_direction_exposure=net_direction_exposure,
        drawdown=drawdown,
        corr_matrix={},  # Se calcula bajo demanda
        corr_to_bench={}  # Se calcula bajo demanda
    )


def _get_subgroup(symbol: str) -> str:
    """Clasifica símbolo en subgrupos para control de exposición - SINCRONIZADO con settings.py"""
    major_caps = {'BTCUSDT', 'ETHUSDT', 'BNBUSDT'}
    
    l1_l2 = {
        # Core L1
        'SOLUSDT', 'AVAXUSDT', 'NEARUSDT', 'ALGOUSDT', 'XRPUSDT',
        # L2/Scaling  
        'ARBUSDT', 'MATICUSDT',
        # Legacy L1
        'LTCUSDT', 'BCHUSDT', 'ETCUSDT'
    }
    
    meme_coins = {
        'PEPEUSDT', '1000PEPEUSDT',  # PEPE variants
        'DOGEUSDT', 'SHIBUSDT',      # OG Memes
        'WIFUSDT', 'PONKEUSDT'       # Nuevos memes
    }
    
    defi = {
        'UNIUSDT', 'AAVEUSDT', 'SUSHIUSDT', 'COMPUSDT',
        'CRVUSDT', 'SNXUSDT', 'LDOUSDT', 'DYDXUSDT'
    }
    
    ai_tech = {'WLDUSDT', 'INJUSDT'}  # Nuevo cluster

    # Usar 'in' para matching parcial (ej: '1000PEPEUSDT' contiene 'PEPE')
    if symbol in major_caps:
        return 'MAJOR_CAPS'
    elif symbol in meme_coins or any(meme in symbol for meme in ['PEPE', 'DOGE', 'SHIB', 'WIF', 'PONKE']):
        return 'MEME_COINS'
    elif symbol in l1_l2:
        return 'L1_L2'
    elif symbol in defi:
        return 'DEFI'
    elif symbol in ai_tech:
        return 'AI_TECH'
    else:
        return 'OTHERS'


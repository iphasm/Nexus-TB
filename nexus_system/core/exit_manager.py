"""
Exit Manager - Sistema Avanzado de Salidas (Fase 3)
Implementa TP parciales, trailing stops, breakeven real y time-stops.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time


class ExitType(Enum):
    PARTIAL_TP = "partial_tp"
    TRAILING_STOP = "trailing_stop"
    BREAKEVEN = "breakeven"
    TIME_STOP = "time_stop"
    FULL_CLOSE = "full_close"


@dataclass
class ExitRule:
    """Regla de salida individual"""
    type: ExitType
    trigger_price: float
    quantity_pct: float  # Porcentaje de la posición original
    description: str


@dataclass
class ExitPlan:
    """Plan completo de salidas para una posición"""
    symbol: str
    side: str
    entry_price: float
    entry_time: float
    current_quantity: float
    exit_rules: List[ExitRule]
    trailing_stop_active: bool = False
    trailing_stop_level: float = 0.0


class ExitManager:
    """
    Gestor Avanzado de Salidas

    Implementa estrategias de salida sofisticadas:
    - TP parciales escalonados
    - Trailing stops dinámicos
    - Breakeven real con fees
    - Time-stops para posiciones estancadas
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active_exit_plans: Dict[str, ExitPlan] = {}  # symbol -> ExitPlan

    def create_exit_plan(self, symbol: str, side: str, entry_price: float,
                        quantity: float, atr: float = None) -> ExitPlan:
        """
        Crea un plan de salidas inteligente basado en la entrada
        """
        exit_rules = []
        entry_time = time.time()

        # 1. TP Parciales (escalonados)
        partial_tp_rules = self._create_partial_tp_rules(side, entry_price, atr)
        exit_rules.extend(partial_tp_rules)

        # 2. Trailing Stop (activado después del primer TP parcial)
        trailing_rule = self._create_trailing_stop_rule(side, entry_price, atr)
        if trailing_rule:
            exit_rules.append(trailing_rule)

        # 3. Time Stop (cierre forzado si no hay movimiento)
        time_rule = self._create_time_stop_rule()
        exit_rules.append(time_rule)

        plan = ExitPlan(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            entry_time=entry_time,
            current_quantity=quantity,
            exit_rules=exit_rules
        )

        self.active_exit_plans[symbol] = plan
        return plan

    def _create_partial_tp_rules(self, side: str, entry_price: float, atr: float = None) -> List[ExitRule]:
        """Crea reglas de TP parciales escalonados"""
        rules = []

        # Estrategia de TP: 50% en 1:1, 25% en 2:1, resto trailing
        if atr and atr > 0:
            # Usar ATR para cálculos dinámicos
            if side == 'LONG':
                # TP1: 1:1 ratio (entry + 2*ATR)
                tp1_price = entry_price + (2 * atr)
                rules.append(ExitRule(
                    type=ExitType.PARTIAL_TP,
                    trigger_price=tp1_price,
                    quantity_pct=0.5,
                    description="TP Parcial 1:1 (50% posición)"
                ))

                # TP2: 2:1 ratio (entry + 4*ATR)
                tp2_price = entry_price + (4 * atr)
                rules.append(ExitRule(
                    type=ExitType.PARTIAL_TP,
                    trigger_price=tp2_price,
                    quantity_pct=0.25,
                    description="TP Parcial 2:1 (25% posición)"
                ))
            else:  # SHORT
                # TP1: 1:1 ratio (entry - 2*ATR)
                tp1_price = entry_price - (2 * atr)
                rules.append(ExitRule(
                    type=ExitType.PARTIAL_TP,
                    trigger_price=tp1_price,
                    quantity_pct=0.5,
                    description="TP Parcial 1:1 (50% posición)"
                ))

                # TP2: 2:1 ratio (entry - 4*ATR)
                tp2_price = entry_price - (4 * atr)
                rules.append(ExitRule(
                    type=ExitType.PARTIAL_TP,
                    trigger_price=tp2_price,
                    quantity_pct=0.25,
                    description="TP Parcial 2:1 (25% posición)"
                ))
        else:
            # Fallback a porcentajes fijos
            tp_ratio = self.config.get('tp_ratio', 1.5)
            stop_loss_pct = self.config.get('stop_loss_pct', 0.02)

            if side == 'LONG':
                tp1_price = entry_price * (1 + stop_loss_pct)
                tp2_price = entry_price * (1 + (stop_loss_pct * tp_ratio))
            else:
                tp1_price = entry_price * (1 - stop_loss_pct)
                tp2_price = entry_price * (1 - (stop_loss_pct * tp_ratio))

            rules.append(ExitRule(
                type=ExitType.PARTIAL_TP,
                trigger_price=tp1_price,
                quantity_pct=0.5,
                description="TP Parcial 1:1 (50% posición)"
            ))

            rules.append(ExitRule(
                type=ExitType.PARTIAL_TP,
                trigger_price=tp2_price,
                quantity_pct=0.25,
                description="TP Parcial 2:1 (25% posición)"
            ))

        return rules

    def _create_trailing_stop_rule(self, side: str, entry_price: float, atr: float = None) -> Optional[ExitRule]:
        """Crea regla de trailing stop"""
        if not atr or atr <= 0:
            return None

        # Trailing stop inicial: 1.5 * ATR detrás del precio
        trailing_distance = 1.5 * atr

        return ExitRule(
            type=ExitType.TRAILING_STOP,
            trigger_price=0.0,  # Se calcula dinámicamente
            quantity_pct=1.0,    # El resto de la posición
            description=f"Trailing Stop ({trailing_distance:.4f} distancia)"
        )

    def _create_time_stop_rule(self) -> ExitRule:
        """Crea regla de time-stop para posiciones estancadas"""
        max_hold_hours = self.config.get('max_position_hold_hours', 24)  # 24 horas por defecto

        return ExitRule(
            type=ExitType.TIME_STOP,
            trigger_price=0.0,  # No aplica precio
            quantity_pct=1.0,
            description=f"Time Stop ({max_hold_hours}h max)"
        )

    def check_exit_conditions(self, symbol: str, current_price: float) -> List[Tuple[ExitRule, float]]:
        """
        Verifica si alguna regla de salida se activa
        Retorna lista de (regla, cantidad_a_cerrar)
        """
        if symbol not in self.active_exit_plans:
            return []

        plan = self.active_exit_plans[symbol]
        triggered_exits = []

        for rule in plan.exit_rules:
            should_trigger = False
            quantity_to_close = plan.current_quantity * rule.quantity_pct

            if rule.type == ExitType.PARTIAL_TP:
                # Verificar si precio cruzó el trigger
                if plan.side == 'LONG' and current_price >= rule.trigger_price:
                    should_trigger = True
                elif plan.side == 'SHORT' and current_price <= rule.trigger_price:
                    should_trigger = True

            elif rule.type == ExitType.TIME_STOP:
                # Verificar tiempo máximo de posición
                max_hold_seconds = self.config.get('max_position_hold_hours', 24) * 3600
                if time.time() - plan.entry_time > max_hold_seconds:
                    should_trigger = True
                    quantity_to_close = plan.current_quantity  # Cerrar todo

            elif rule.type == ExitType.TRAILING_STOP and plan.trailing_stop_active:
                # Verificar trailing stop
                if plan.side == 'LONG' and current_price <= plan.trailing_stop_level:
                    should_trigger = True
                    quantity_to_close = plan.current_quantity  # Cerrar todo
                elif plan.side == 'SHORT' and current_price >= plan.trailing_stop_level:
                    should_trigger = True
                    quantity_to_close = plan.current_quantity  # Cerrar todo

            if should_trigger:
                triggered_exits.append((rule, quantity_to_close))

        return triggered_exits

    def update_trailing_stop(self, symbol: str, current_price: float):
        """
        Actualiza trailing stop si está activo
        """
        if symbol not in self.active_exit_plans:
            return

        plan = self.active_exit_plans[symbol]

        # Buscar regla de trailing stop
        trailing_rule = None
        for rule in plan.exit_rules:
            if rule.type == ExitType.TRAILING_STOP:
                trailing_rule = rule
                break

        if not trailing_rule:
            return

        # Activar trailing después del primer TP parcial
        if not plan.trailing_stop_active and plan.current_quantity < plan.current_quantity:  # Si ya se cerró algo
            plan.trailing_stop_active = True

        # Actualizar nivel del trailing stop
        if plan.trailing_stop_active:
            trailing_distance = 1.5 * (plan.entry_price * 0.01)  # 1.5% por defecto si no hay ATR

            if plan.side == 'LONG':
                new_level = current_price - trailing_distance
                plan.trailing_stop_level = max(plan.trailing_stop_level, new_level)
            else:
                new_level = current_price + trailing_distance
                plan.trailing_stop_level = min(plan.trailing_stop_level, new_level)

    def execute_partial_exit(self, symbol: str, rule: ExitRule, quantity: float):
        """
        Ejecuta salida parcial y actualiza el plan
        """
        if symbol not in self.active_exit_plans:
            return

        plan = self.active_exit_plans[symbol]
        plan.current_quantity -= quantity

        # Remover regla ejecutada
        if rule in plan.exit_rules:
            plan.exit_rules.remove(rule)

        # Si se cerró todo, remover el plan
        if plan.current_quantity <= 0.001:
            del self.active_exit_plans[symbol]

    def calculate_real_breakeven(self, entry_price: float, fee_rate: float = 0.001,
                                slippage: float = 0.0005, side: str = 'LONG') -> float:
        """
        Calcula el breakeven real incluyendo fees y slippage
        """
        total_friction = (fee_rate * 2) + slippage  # Entry + Exit fees + slippage

        if side == 'LONG':
            breakeven_price = entry_price * (1 + total_friction)
        else:  # SHORT
            breakeven_price = entry_price * (1 - total_friction)

        return breakeven_price

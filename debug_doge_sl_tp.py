#!/usr/bin/env python3
"""
Debug del cálculo de SL/TP para DOGEUSDT SHORT position
"""
import os
import sys
import asyncio

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

async def debug_doge_sl_tp():
    """Debug del cálculo de SL/TP para DOGEUSDT"""
    print("🔍 DEBUG: SL/TP Calculation for DOGEUSDT SHORT")
    print("=" * 50)

    # Simular los datos que tendríamos en una señal de scalping
    signal_data = {
        'symbol': 'DOGEUSDT',
        'action': 'SELL',
        'price': 0.14917,  # Precio actual del log
        'confidence': 0.7,
        'atr': 0.0005,  # Valor de ATR estimado (necesitamos verificar)
        'metadata': {
            'atr': 0.0005,  # ATR que se pasa al metadata
            'strategy': 'Scalping'
        }
    }

    print(f"📊 Signal Data:")
    print(f"   Symbol: {signal_data['symbol']}")
    print(f"   Action: {signal_data['action']}")
    print(f"   Price: ${signal_data['price']:.6f}")
    print(f"   ATR: {signal_data['atr']}")
    print(f"   Confidence: {signal_data['confidence']}")

    # Simular el cálculo de scalping.py
    from nexus_system.cortex.scalping import ScalpingStrategy
    strategy = ScalpingStrategy()

    # Calcular entry params
    wallet_balance = 1000  # Dummy
    config = {'leverage': 10, 'max_capital_pct': 0.05}

    entry_params = strategy.calculate_entry_params(
        type('Signal', (), signal_data)(),  # Crear objeto signal dummy
        wallet_balance,
        config
    )

    print("\n🔧 Calculated Entry Params:")
    print(f"   Leverage: {entry_params['leverage']}")
    print(f"   Size Pct: {entry_params['size_pct']}")
    print(f"   Stop Loss Price: ${entry_params['stop_loss_price']:.6f}")
    print(f"   Take Profit Price: ${entry_params['take_profit_price']:.6f}")

    # Análisis detallado
    current_price = signal_data['price']
    atr = signal_data['atr']

    print("\n🧮 Detailed Calculation Breakdown:")
    print(f"   Current Price: ${current_price:.6f}")
    print(f"   ATR: {atr}")

    # Base calculations
    if atr > 0:
        sl_distance = 1.5 * atr
        tp_distance = 2.5 * atr
        print(f"   ATR-based SL distance: {sl_distance:.6f}")
        print(f"   ATR-based TP distance: {tp_distance:.6f}")
    else:
        sl_distance = current_price * 0.02
        tp_distance = current_price * 0.035
        print(f"   Fallback SL distance: {sl_distance:.6f}")
        print(f"   Fallback TP distance: {tp_distance:.6f}")

    # Apply risk scaling (simplified)
    print("\n🎯 Risk Scaling:")
    try:
        from nexus_system.core.risk_scaler import RiskScaler
        scaler = RiskScaler()
        multipliers = scaler.calculate_risk_multipliers(
            confidence=signal_data['confidence'],
            strategy="Scalping",
            market_data=None
        )
        print(f"   TP Multiplier: {multipliers.take_profit_multiplier:.3f}")

        sl_distance *= multipliers.stop_loss_multiplier
        tp_distance *= multipliers.take_profit_multiplier

        print(f"   SL distance after scaling: {sl_distance:.6f}")
        print(f"   TP distance after scaling: {tp_distance:.6f}")
    except Exception as e:
        print(f"   Risk scaling failed: {e}")

    # Final price calculations
    print("\n💰 Final Price Calculations:")
    if signal_data['action'] == "BUY":
        stop_loss_price = current_price - sl_distance
        take_profit_price = current_price + tp_distance
        print("   BUY position calculations:")
        print(f"     SL = {current_price:.6f} - {sl_distance:.6f} = {stop_loss_price:.6f}")
        print(f"     TP = {current_price:.6f} + {tp_distance:.6f} = {take_profit_price:.6f}")
    else:  # SHORT
        stop_loss_price = current_price + sl_distance
        take_profit_price = current_price - tp_distance
        print("   SHORT position calculations:")
        print(f"     SL = {current_price:.6f} + {sl_distance:.6f} = {stop_loss_price:.6f}")
        print(f"     TP = {current_price:.6f} - {tp_distance:.6f} = {take_profit_price:.6f}")

    # Validation
    print("\n✅ Validation:")
    if signal_data['action'] == "BUY":
        sl_valid = stop_loss_price < current_price
        tp_valid = take_profit_price > current_price
    else:  # SHORT
        sl_valid = stop_loss_price > current_price
        tp_valid = take_profit_price < current_price

    print(f"   SL direction valid: {sl_valid}")
    print(f"   TP direction valid: {tp_valid}")

    if not tp_valid:
        print("❌ ERROR: TP calculation is wrong!")
        print("   For SHORT positions, TP must be LOWER than entry price")
        if take_profit_price > current_price:
            print(f"   Current TP ({take_profit_price:.6f}) > Current Price ({current_price:.6f}) - INVALID!")
    else:
        print("✅ TP calculation appears correct")

if __name__ == "__main__":
    asyncio.run(debug_doge_sl_tp())

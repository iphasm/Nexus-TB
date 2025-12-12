import asyncio
import sys
import os

# Ensure root is in path
sys.path.append(os.getcwd())

from antigravity_quantum.backtest.engine import BacktestEngine

async def main():
    try:
        # Full Watchlist from QuantumEngine
        assets = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 
                  'ADAUSDT', 'LTCUSDT', 'LINKUSDT', 'DOGEUSDT', 'AVAXUSDT', 
                  'ZECUSDT', 'SUIUSDT']
        
        # User requested: 1000 USDT per asset
        capital = 1000.0
        
        # User requested: Last 3 Months (90 days)
        days = 90
        
        engine = BacktestEngine(assets, initial_capital=capital, days=days)
        results = await engine.run()
        
        print("\n\n📊 **INFORME FINAL DE BACKTEST (PILOT MODE)**")
        print("〰️" * 30)
        
        total_pnl = 0
        total_balance = 0
        total_start = len(assets) * capital
        
        for asset, data in results.items():
            symbol = asset.replace('USDT', '')
            balance = data['final_balance']
            roi = data['roi']
            trades = data['trades']
            
            pnl_usd = balance - capital
            total_pnl += pnl_usd
            total_balance += balance
            
            icon = "🟢" if roi > 0 else "🔴"
            print(f"{icon} **{symbol}**")
            print(f"   • Balance Final: ${balance:,.2f}")
            print(f"   • Rendimiento: {roi:+.2f}%")
            print(f"   • PnL: ${pnl_usd:+.2f}")
            print(f"   • Trades Ejecutados: {trades}")
            print("")
            
        total_roi = ((total_balance - total_start) / total_start) * 100
        
        print("〰️" * 30)
        print(f"💰 **CAPITAL TOTAL: ${total_balance:,.2f}** (Inicio: ${total_start:,.2f})")
        print(f"📈 **ROI GLOBAL: {total_roi:+.2f}%**")
        print(f"💵 **PROFIT/LOSS: ${total_pnl:+.2f}**")
        print("〰️" * 30)

    except Exception as e:
        print(f"❌ CRITICAL ERROR IN BACKTEST: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

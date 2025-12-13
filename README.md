# Antigravity Bot v3.3.2 🚀

**Advanced Hedge Fund-Grade Trading Bot** combining Multi-Timeframe (MTF) analysis, institutional strategies (Squeeze, Velocity, Mean Reversion), and robust risk management. Now with **Quantum Engine** and **Alpaca** integration.

## 🌟 Key Features

### 🧠 Intelligence Engine (Quantum)
- **Multi-Timeframe Logic (MTF):** Filters 15m signals against 1H macro trends.
- **Strategies:**
  - **Squeeze & Velocity (Futures):** Captures explosive moves after volatility contraction.
  - **Mean Reversion (Spot):** Buys dips during oversold conditions.
  - **Shark Sentinel 🦈:** Detects global market crashes (BTC/ETH drops) and halts trading instantly.
  - **Smart Filters:** Ignores noise using ATR, RSI, and Volume checks.

### 🛡️ Risk Management (Safety First)
- **Circuit Breaker 🚨:** Automatically downgrades from **PILOT** to **COPILOT** after **5 consecutive losses** to prevent account drain.
- **Shark Mode:** Freezes all buying during market crashes (>3% drops).
- **Dynamic Stop Loss:** Adapts to market volatility (ATR-based).
- **Position Sizing:** Fixed risk per trade (Default: 2% of Equity).
- **Max Margin:** Global limit on capital usage.

### 🎮 Operation Modes
1. **WATCHER:** (Default) Receives alerts only. No execution.
2. **COPILOT:** Receives proposals with "Approve/Reject" buttons.
3. **PILOT:** Fully autonomous execution (Buying & Selling).

## 🛠️ Configuration
Commands to control the bot via Telegram:

| Command | Description |
| :--- | :--- |
| `/start` | Bot status, main menu and connectivity check. |
| `/status` | Market dashboard, active positions, and system health. |
| `/config` | Interactive menu for leverage, margin, and personalities. |
| `/mode` | Switch risk profiles (`RONIN`, `GUARDIAN`, `QUANTUM`). |
| `/pilot` | Enable autonomous trading mode. |
| `/copilot` | Enable assisted trading mode. |
| `/watcher` | Enable alert-only mode. |
| `/price` | Real-time price and signal dashboard. |
| `/news` | AI-generated market briefing. |
| `/sentiment` | Global market sentiment analysis (Crypto + Macro). |
| `/sniper` | Scans for immediate high-probability opportunities. |
| `/personality` | Change the bot's tone (e.g., Vader, Rick, Wolf of Wall St). |

## 🚀 Deployment
Designed for **Railway** (Dockerized).

1. Set Environment Variables:
   - `BINANCE_API_KEY`, `BINANCE_SECRET`
   - `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` (Optional for Stocks)
   - `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_IDS`
   - `OPENAI_API_KEY` (For AI features)
2. Push to GitHub.
3. Railway auto-deploys.

---
*Built with Python 3.10, Pandas-TA, and Telegram Bot API.*

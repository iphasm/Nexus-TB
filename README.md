# Antigravity Bot v3.2 🚀

**Advanced Hedge Fund-Grade Trading Bot** combining Multi-Timeframe (MTF) analysis, institutional strategies (Squeeze, Velocity, Mean Reversion), and robust risk management.

## 🌟 Key Features

### 🧠 Intelligence Engine
- **Multi-Timeframe Logic (MTF):** Filters 15m signals against 1H macro trends.
- **Strategies:**
  - **Squeeze & Velocity (Futures):** Captures explosive moves after volatility contraction.
  - **Mean Reversion (Spot):** Buys dips during oversold conditions.
  - **Smart Filters:** Ignores noise using ATR, RSI, and Volume checks.

### 🛡️ Risk Management (Safety First)
- **Circuit Breaker 🚨:** Automatically downgrades from **PILOT** to **COPILOT** after **5 consecutive losses** to prevent account drain.
- **Dynamic Stop Loss:** Adapts to market volatility (2x ATR).
- **Position Sizing:** Fixed risk per trade (Default: 2% of Equity).
- **Max Margin:** Global limit on capital usage.

### 🎮 Operation Modes
1. **WATCHER:** (Default) Receives alerts only.
2. **COPILOT:** Receives proposals with "Approve/Reject" buttons.
3. **PILOT:** Fully autonomous execution.

## 🛠️ Configuration
Commands to control the bot via Telegram:

| Command | Description |
| :--- | :--- |
| `/start` | Bot status and connectivity check. |
| `/status` | Market dashboard and system health. |
| `/risk` | Explains current risk rules (incl. Circuit Breaker). |
| `/config` | Interactive menu for leverage, margin, and allocation. |
| `/set_keys` | Securely configure Binance API Keys. |
| `/stop` | Emergency stop (closes connection, not positions). |

## 🚀 Deployment
Designed for **Railway** (Dockerized).

1. Set Environment Variables:
   - `BINANCE_API_KEY`, `BINANCE_SECRET`
   - `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_IDS`
2. Push to GitHub.
3. Railway auto-deploys.

---
*Built with Python 3.10 and Telegram Bot API.*

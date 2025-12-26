# ⚡ Nexus Trading Bot

**Advanced Algorithmic Trading Platform** combining real-time WebSocket data, AI-powered analysis, machine learning strategy selection, and multi-market execution across cryptocurrency and traditional markets.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://t.me/nexusalgorithmbasedtradingbot)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#)

---

## 🌟 Key Features

### 📡 Real-Time Data
- **WebSocket Streaming**: Sub-second market data from Binance Futures (29+ pairs)
- **Hybrid Architecture**: WebSocket primary, REST API fallback
- **Adaptive Cycles**: 30s when WebSocket active, 60s for REST mode

### 🧠 AI & Machine Learning
- **GPT-4 Integration**: Market sentiment, news analysis, trade recommendations
- **XGBoost Classifier**: Dynamic strategy selection based on market regime
- **Feature Engineering**: 15+ technical indicators + time-based features
- **NexusLogger**: Centralized, debounced logging for clean diagnostics


### 🎯 Multi-Strategy Engine
| Strategy | Trigger | Best For |
|----------|---------|----------|
| **Trend Following** | EMA crossovers + ADX | Directional moves |
| **Scalping** | RSI extremes + Volume | High volatility |
| **Mean Reversion** | Bollinger touches | Range-bound markets |
| **Grid Trading** | EMA Mean Reversion | Sideways/Chop |
| **Black Swan** | -5% in 15min | Crash protection |

### 🛡️ Risk Management
- **Circuit Breaker**: Auto-pause after consecutive losses
- **Dynamic Cooldowns**: ATR-adjusted per-symbol cooldowns
- **Shark Mode**: Background crash detection and auto-exit
- **Position Sizing**: Configurable margin and leverage

---

## 🕹️ Operational Modes

| Mode | Description |
|------|-------------|
| `WATCHER` | Alerts only - no trades executed |
| `COPILOT` | Semi-automated - requires confirmation |
| `PILOT` | Fully autonomous trading |

---

## 🛠️ Commands

### Dashboard & Market
| Command | Description |
|---------|-------------|
| `/start` | Main control center |
| `/dashboard` | Balance, positions, PnL |
| `/price` | Market scanner (RSI, trend) |
| `/sync` | Synchronize SL/TP orders |

### Trading
| Command | Description |
|---------|-------------|
| `/long SYMBOL` | Open LONG position |
| `/short SYMBOL` | Open SHORT position |
| `/close SYMBOL` | Close position |
| `/closeall` | Emergency close all |

### AI Analysis
| Command | Description |
|---------|-------------|
| `/analyze SYMBOL` | Deep AI analysis |
| `/news` | Market briefing |
| `/sentiment` | Crypto + macro sentiment |
| `/fomc` | FED analysis |

### Configuration
| Command | Description |
|---------|-------------|
| `/config` | Interactive settings panel |
| `/strategies` | Enable/disable strategies |
| `/assets` | Asset management |
| `/personality` | Change bot voice |

### Admin (Owner Only)
| Command | Description |
|---------|-------------|
| `/wsstatus` | WebSocket health |
| `/ml_mode` | Toggle ML classifier |
| `/retrain` | Retrain ML model |
| `/subs` | Manage subscribers |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXUS TRADING BOT                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   UPLINK    │  │   CORTEX    │  │      EFFECTORS      │  │
│  │  (Data In)  │  │  (Brain)    │  │   (Trade Out)       │  │
│  ├─────────────┤  ├─────────────┤  ├─────────────────────┤  │
│  │ • WebSocket │  │ • Strategies│  │ • Order Execution   │  │
│  │ • Binance   │  │ • ML Class. │  │ • SL/TP Management  │  │
│  │ • Alpaca    │  │ • Signals   │  │ • Position Sizing   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   SHIELD    │  │   SERVOS    │  │      INTERFACE      │  │
│  │   (Risk)    │  │ (Services)  │  │    (Telegram)       │  │
│  ├─────────────┤  ├─────────────┤  ├─────────────────────┤  │
│  │ • Circuit   │  │ • Scheduler │  │ • Commands          │  │
│  │   Breaker   │  │ • Database  │  │ • Callbacks         │  │
│  │ • Shark     │  │ • Analytics │  │ • Sessions          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment

### Requirements
- Python 3.11+
- PostgreSQL database
- Railway or Docker-compatible hosting

### Environment Variables
```env
# Telegram
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_ADMIN_ID=your_chat_id

# Binance Futures
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret

# Alpaca (Optional - Stocks)
APCA_API_KEY_ID=your_key
APCA_API_SECRET_KEY=your_secret
APCA_API_BASE_URL=https://paper-api.alpaca.markets/v2

# AI Features
OPENAI_API_KEY=sk-...

# Static IP Proxy (Optional)
PROXY_URL=http://user:pass@ip:port
```

### Quick Start
```bash
# Clone repository
git clone https://github.com/iphasm/Nexus-TB.git
cd Nexus-TB

# Install dependencies
pip install -r requirements.txt

# Run
python nexus_loader.py
```

---

## 📊 Supported Markets

### Cryptocurrency (Binance Futures)
BTC, ETH, SOL, BNB, XRP, ADA, DOGE, SHIB, PEPE, FLOKI, BONK, WIF, SUI, SEI, INJ, RENDER, ICP, UNI, CRV, POL, BCH, ZEC, XLM, FET, and more...

### Stocks & ETFs (Alpaca)
TSLA, NVDA, AMD, AAPL, MSFT, SPY, QQQ, IWM

---

## 📖 Documentation

- **[Whitepaper](WHITEPAPER.md)** - Full technical documentation
- **[Landing Page](index.html)** - Commercial overview

---

## 📬 Contact

- **Telegram Bot**: [@nexusalgorithmbasedtradingbot](https://t.me/nexusalgorithmbasedtradingbot)
- **Developer**: Fabio Sepúlveda (iphasm)
- **GitHub**: [github.com/iphasm/Nexus-TB](https://github.com/iphasm/Nexus-TB)

---

## ⚠️ Disclaimer

Trading cryptocurrencies and securities involves substantial risk of loss. This software is provided as-is without warranty. Past performance is not indicative of future results. Use at your own risk.

---

*Built with Python 3.11, XGBoost, aiogram, CCXT, and WebSockets.*

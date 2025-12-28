# NEXUS TRADING BOT
## Whitepaper v1.0

---

## Executive Summary

Nexus Trading Bot is an advanced algorithmic trading platform that combines real-time market analysis, machine learning classification, and multi-strategy execution to deliver institutional-grade trading capabilities to individual traders. Built on a **modular biome architecture**, Nexus operates across cryptocurrency and traditional markets via **Binance, Bybit, and Alpaca** integrations, with persistent state managed through **PostgreSQL** and encrypted session handling.

---

## 1. Introduction

### 1.1 The Problem

Individual traders face significant challenges in today's fast-moving markets:

- **Information Overload**: Markets generate massive amounts of data 24/7
- **Emotional Trading**: Human psychology leads to poor decision-making
- **Execution Speed**: Manual trading cannot compete with algorithmic systems
- **Technical Barriers**: Building trading infrastructure requires significant expertise
- **Risk Management**: Consistent risk control is difficult to maintain manually

### 1.2 The Solution

Nexus Trading Bot addresses these challenges through:

- **Real-Time Data Streaming**: WebSocket connections for sub-second market data
- **AI-Powered Analysis**: GPT-4 integration for market sentiment and news analysis
- **Machine Learning Classification**: XGBoost-based strategy selection
- **Multi-Strategy Engine**: Dynamic switching between trend, scalping, and mean-reversion strategies
- **Automated Risk Management**: Circuit breakers, position sizing, and SL/TP automation

---

## 2. System Architecture

### 2.1 Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXUS TRADING BOT                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   UPLINK    │  │   CORTEX    │  │      EFFECTORS      │  │
│  │  (Data In)  │  │  (Brain)    │  │   (Trade Out)       │  │
│  ├─────────────┤  ├─────────────┤  ├─────────────────────┤  │
│  │ • Binance   │  │ • Strategies│  │ • Order Execution   │  │
│  │ • Bybit     │  │ • ML Class. │  │ • SL/TP Management  │  │
│  │ • Alpaca    │  │ • Signals   │  │ • Position Sizing   │  │
│  │ • WebSocket │  │ • Sentinel  │  │ • NexusBridge       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   SHIELD    │  │   SERVOS    │  │      INTERFACE      │  │
│  │   (Risk)    │  │ (Services)  │  │    (Telegram)       │  │
│  ├─────────────┤  ├─────────────┤  ├─────────────────────┤  │
│  │ • Circuit   │  │ • Scheduler │  │ • Commands          │  │
│  │   Breaker   │  │ • PostgreSQL│  │ • Callbacks         │  │
│  │ • Sentinel  │  │ • Sessions  │  │ • Sessions          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Modular Biome Architecture

| Biome | Responsibility | Key Files |
|-------|----------------|----------|
| **CORE** | Event loop, orchestration | `engine.py` |
| **CORTEX** | Strategies, ML Classifier, Signals | `trend.py`, `scalping.py`, `sentinel.py` |
| **SHIELD** | Risk management, Circuit Breaker | `manager.py` |
| **UPLINK** | Data ingestion, Exchange Adapters | `stream.py`, `binance_adapter.py`, `bybit_adapter.py` |
| **SERVOS** | Trading, Sessions, DB, Auth | `trading_manager.py`, `db.py` |
| **HANDLERS** | Telegram commands | `commands.py`, `config.py` |

### 2.3 Data Flow

1. **Market Data Ingestion**: WebSocket streams from Binance/Bybit Futures (29+ crypto pairs)
2. **Multi-Timeframe Analysis**: Main (15m), Macro (4h), Micro (1m) candles fetched in parallel
3. **Indicator Calculation**: EMA, RSI, Bollinger Bands, ATR, ADX computed in real-time
4. **Strategy Classification**: ML model selects optimal strategy based on market regime
5. **Signal Generation**: Strategy-specific analysis produces BUY/SELL/HOLD signals
6. **Risk Filtering**: Signals pass through Sentinel Protocol and cooldown filters
7. **Execution**: Orders placed via NexusBridge with automated SL/TP

---

## 3. Exchange Integration

### 3.1 Binance Futures
- **Primary exchange** for crypto perpetuals
- WebSocket streaming with REST fallback
- Full CCXT async implementation

### 3.2 Bybit V5 (Unified Trading)
Bybit offers **superior order management** capabilities:

| Feature | Binance | Bybit |
|---------|---------|-------|
| Cancel All Orders | Multiple API calls | **Single call** |
| TP/SL Linked to Position | No | **Yes** |
| Amend Order (Hot-Edit) | No | **Yes** |
| Native Trailing Stop | No | **Yes** |

**Key Bybit Adapter Methods:**
- `cancel_all_orders(symbol)`: Cancel all orders in one request
- `set_trading_stop(symbol, tp, sl)`: Set TP/SL linked to position (pass 0 to cancel)
- `amend_order(order_id, price)`: Modify existing order without cancel+replace
- `place_trailing_stop(symbol, callback_rate)`: Server-side trailing stops

### 3.3 Alpaca (Stocks & ETFs)
- Paper and Live trading support
- Real-time during US market hours
- Polygon WebSocket for premium data

---

## 3. Trading Strategies

### 3.1 Trend Following
- **Trigger**: EMA crossovers with ADX confirmation
- **Timeframe**: 15m - 4h
- **Best For**: Strong directional moves
- **Risk**: 1.5x ATR stop loss

### 3.2 Scalping
- **Trigger**: RSI extremes with volume confirmation
- **Timeframe**: 5m - 15m
- **Best For**: High volatility periods
- **Risk**: 1x ATR stop loss

### 3.3 Mean Reversion
- **Trigger**: Bollinger Band touches with momentum divergence
- **Timeframe**: 1h - 4h
- **Best For**: Range-bound markets
- **Risk**: 2x ATR stop loss

### 3.4 Grid Trading
- **Trigger**: Price mean reversion relative to EMA200
- **Mechanism**: Buy Low / Sell High within ATR-defined bands
- **Best For**: Sideways or choppy markets
- **Risk**: Dynamic stop loss below grid range

### 4.5 Sentinel Protocol (Unified Defense & Attack)
- **Module**: `sentinel.py`
- **Modes**:
  - **Black Swan (Defense)**: Auto-exit all Longs on >4% BTC crash
  - **Shark Mode (Offense)**: Aggressive shorting on vulnerable assets during "Sangria" markets
- **CoinMarketCap Integration**: Monitors BTC Dominance for macro context

---

## 4. Machine Learning System

### 4.1 Model Architecture
- **Algorithm**: XGBoost Classifier
- **Features**: 15+ technical indicators + time-based features
- **Training Data**: Historical market data with labeled regimes
- **Validation**: TimeSeriesSplit cross-validation

### 4.2 Feature Engineering
- EMA slopes (20, 50, 200)
- RSI with smoothing
- ATR normalization
- Volume relative to 20-period SMA
- Hour of day, day of week
- Distance to 50-period high/low

### 4.3 Prediction Pipeline
1. Real-time indicator calculation
2. Feature scaling (RobustScaler)
3. Model inference with confidence threshold (0.70)
4. Strategy assignment with fallback to rule-based classification

---

## 5. Risk Management

### 5.1 Position Sizing
- Default: 5% of account per trade
- Adjustable via configuration
- Leverage control (1x - 20x)

### 5.2 Circuit Breaker
- Triggers after N consecutive losses
- Pauses automated trading
- Requires manual reset

### 5.3 Dynamic Cooldowns
- Per-symbol cooldown after signals
- ATR-adjusted duration
- Prevents overtrading

### 5.4 Sentinel Protocol (The Guardian + Predator)
The **Sentinel** module (`sentinel.py`) is a unified strategy that handles both defensive and offensive operations:

1.  **Black Swan Mode (Defense)**:
    - **Trigger**: BTC crashes >4% in a single candle.
    - **Action**: Emits `EXIT_LONG` signal with confidence 1.0. Shorts remain open.
    
2.  **Shark Mode (Offense)**:
    - **Trigger**: Bearish momentum detected (ADX > 25, Price < EMA50 < EMA200).
    - **Action**: Opens leveraged SHORT positions on `SHARK_TARGETS` (volatile altcoins).

---

## 6. Database & Persistence

### 6.1 PostgreSQL Schema
Nexus uses PostgreSQL for durable state persistence:

| Table | Purpose |
|-------|--------|
| `sessions` | User API keys (encrypted), config (JSONB) |
| `users` | Subscription management, roles, timezones |
| `bot_state` | Global strategies, group toggles, disabled assets |
| `scheduled_tasks` | User-defined scheduled actions |

### 6.2 Security
- **Encryption**: Fernet AES-256 for API keys
- **Fallback**: JSON files if `DATABASE_URL` not set
- **Lazy Migration**: Auto-encrypts plaintext keys on load

---
## 7. Logging & Diagnostics

Nexus employs a centralized **NexusLogger** to maintain system health without saturating storage or API quotas.

### 7.1 Log Architecture
- **Centralized**: All modules feed into `NexusLogger`.
- **Debounced**: Repetitive errors (e.g., connection retries) are suppressed (logged once every N seconds).
- **Aggregated Startup**: Initialization logs are condensed into single-line summaries with user counts.

### 7.2 Operational Modes
- **INFO**: Standard production level (Events + Signals).
- **DEBUG**: Verbose trace for development.
- **ERROR**: Critical failures only.

---

## 8. Operational Modes

| Mode | Description | User Action |
|------|-------------|-------------|
| WATCHER | Alerts only | None required |
| COPILOT | Signals + Confirmation | Approve/Reject trades |
| PILOT | Fully autonomous | None required |

---

## 9. Supported Markets

### 9.1 Cryptocurrency (Binance/Bybit Futures)
- BTC, ETH, SOL, BNB, XRP, ADA
- DOGE, SHIB, PEPE, FLOKI, BONK
- 25+ additional pairs

### 9.2 Stocks & ETFs (Alpaca)
- TSLA, NVDA, AMD, AAPL, MSFT
- SPY, QQQ, IWM
- Real-time during US market hours

---

## 10. Technical Specifications

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.11+ |
| Framework | aiogram 3.x (Telegram) |
| Database | PostgreSQL |
| ML Library | XGBoost, scikit-learn |
| API | CCXT, python-binance, alpaca-py |
| Real-time | WebSockets |
| Hosting | Railway (cloud) |

---

## 11. Security

- **API Key Encryption**: Fernet AES-256
- **Session Isolation**: Per-user encrypted sessions
- **IP Whitelisting**: Static IP proxy for exchange security
- **Role-Based Access**: Owner, Admin, Subscriber levels

---

## 12. Future Roadmap

### Phase 1 (Current)
- ✅ Multi-strategy engine
- ✅ ML classification
- ✅ WebSocket streaming
- ✅ Telegram interface

### Phase 2 (Q1 2025)
- Options strategies
- Advanced portfolio management
- Social trading features

### Phase 3 (Q2 2025)
- Web dashboard
- Mobile app
- Copy trading marketplace

---

## 13. Conclusion

Nexus Trading Bot represents growing algorithmic trading platform. By combining real-time data processing, machine learning, and proven trading strategies, Nexus empowers traders to participate in markets with institutional-grade tools while maintaining full control over their risk parameters.

---

## Contact

- **Telegram**: @nexusalgorithmbasedtradingbot
- **Developer**: Fabio (iphasm)

---

*This document is for informational purposes only. Trading cryptocurrencies and securities involves substantial risk of loss. Past performance is not indicative of future results.*

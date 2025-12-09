import time
import os
import threading
import telebot
from dotenv import load_dotenv

# Import internal modules
from data.fetcher import get_market_data
from strategies.analyzer import analyze_market
from utils.trading_manager import SessionManager # CHANGED

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
WATCHLIST = [
    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'SUIUSDT', 'ZECUSDT',
    'TSLA', 'NVDA', 'MSFT',
    'GC=F', 'CL=F']
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')
# Note: TELEGRAM_CHAT_IDS is less relevant for commands now, but still useful for broadcasts?
# We will use valid sessions for broadcasts potentially, or keep the env var for admin alerts.
TELEGRAM_CHAT_IDS = [id.strip() for id in os.getenv('TELEGRAM_CHAT_ID', '').split(',') if id.strip()]

# Initialize Bot
bot = None
session_manager = None # Global session manager

if TELEGRAM_TOKEN:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
else:
    print("WARNING: TELEGRAM_TOKEN not found.")

def send_alert(message):
    """Broadcasts message to all registered sessions + Env Chat IDs"""
    # 1. Env Chat IDs
    targets = set(TELEGRAM_CHAT_IDS)
    
    # 2. Add Active Sessions
    if session_manager:
        for s in session_manager.get_all_sessions():
            targets.add(s.chat_id)
            
    if bot and targets:
        for chat_id in targets:
            try:
                bot.send_message(chat_id, message, parse_mode='Markdown')
            except Exception as e:
                print(f"Error sending alert to {chat_id}: {e}")
    else:
        print(f"ALERT (No Telegram): {message}")

# --- BOT COMMAND HANDLERS ---

@bot.message_handler(commands=['set_keys'])
def handle_set_keys(message):
    """
    Usage: /set_keys <API_KEY> <API_SECRET>
    """
    chat_id = str(message.chat.id)
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "⚠️ Usage: `/set_keys <API_KEY> <API_SECRET>`\n\n_We recommend deleting this message after sending._", parse_mode='Markdown')
            return
        
        api_key = args[1]
        api_secret = args[2]
        
        # Create or Update Session
        session = session_manager.create_or_update_session(chat_id, api_key, api_secret)
        
        if session.client:
            bot.reply_to(message, "✅ **API Keys Registered!**\nYou can now trade. Default settings: Leverage 5x, Margin 10%. Use /config to view.")
        else:
            bot.reply_to(message, "❌ Keys saved, but **Binance Connection Failed**. Please check your keys and permissions.")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['delete_keys'])
def handle_delete_keys(message):
    chat_id = str(message.chat.id)
    if session_manager.delete_session(chat_id):
        bot.reply_to(message, "🗑️ **Session Deleted.** Your keys have been removed from this bot.")
    else:
        bot.reply_to(message, "⚠️ No session found to delete.")

@bot.message_handler(commands=['long'])
def handle_long_position(message):
    """Manually trigger a LONG position for the current chat session"""
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session or not session.client:
        bot.reply_to(message, "⛔ **No Active Session.**\nPlease register your Binance API keys first using:\n`/set_keys <API_KEY> <API_SECRET>`", parse_mode='Markdown')
        return

    # Parse message: /long BTC
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/long <SYMBOL>` (e.g., `/long BTC`)", parse_mode='Markdown')
            return
            
        symbol = args[1].upper()
        if 'USDT' not in symbol:
            symbol += 'USDT'
            
        bot.reply_to(message, f"⚡ Executing LONG for **{symbol}**...", parse_mode='Markdown')
        
        # Execute on specific session
        success, msg = session.execute_long_position(symbol)
        if success:
            bot.reply_to(message, f"✅ {msg}")
        else:
            bot.reply_to(message, f"❌ Trade Failed: {msg}")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['price', 'precios'])
def handle_price_request(message):
    """Handles /price command to show current status of all assets"""
    # Public command, accessible to anyone or restricted?
    # Let's keep it open or restrict to known sessions/admin?
    # For now, open.
    
    bot.reply_to(message, "⏳ Fetching prices... please wait.")
    
    # Categories
    groups = {
        "📉 CRYPTO": [],
        "💵 ACCIONES": [], 
        "🛢️ MATERIAS PRIMAS": []
    }
    
    # Friendly Names
    name_map = {
        'GC=F': 'Oro (Gold)',
        'CL=F': 'Petróleo (Oil)',
        'BTCUSDT': 'Bitcoin (BTC)',
        'ETHUSDT': 'Ethereum (ETH)',
        'XRPUSDT': 'Ripple (XRP)',
        'SOLUSDT': 'Solana (SOL)',
        'SUIUSDT': 'SUI (SUI)',
        'ZECUSDT': 'Zcash (ZEC)',
        'TSLA': 'Tesla (TSLA)',
        'NVDA': 'Nvidia (NVDA)',
        'MSFT': 'Microsoft (MSFT)'
    }

    # Icons
    icon_map = {
        'BTCUSDT': '₿',
        'ETHUSDT': 'Ξ',
        'XRPUSDT': '✕',
        'SOLUSDT': '◎',
        'SUIUSDT': '💧',
        'ZECUSDT': '🛡️',
        'TSLA': '🚗',
        'NVDA': '🟢',
        'MSFT': '🪟',
        'GC=F': '🥇',
        'CL=F': '🛢️'
    }

    for asset in WATCHLIST:
        try:
            # Determine Category
            category = "💵 ACCIONES"
            if 'USDT' in asset: category = "📉 CRYPTO"
            elif '=F' in asset: category = "🛢️ MATERIAS PRIMAS"
            
            # Fetch
            df = get_market_data(asset, timeframe='15m', limit=300)
            if df.empty: continue
                
            latest = df.iloc[-1]
            price = latest['close']
            
            _, metrics = analyze_market(df)
            rsi = metrics.get('rsi', 0)
            stoch_k = metrics.get('stoch_k', 0)
            stoch_d = metrics.get('stoch_d', 0)
            vol_ratio = metrics.get('vol_ratio', 0)
            ema_200 = metrics.get('ema_200', 0)
            
            trend_icon = "📈" if price > ema_200 else "🐻"
            display_name = name_map.get(asset, asset)
            asset_icon = icon_map.get(asset, '💎')
            
            entry = (
                f"{asset_icon} **{display_name}**\n"
                f"💰 ${price:,.2f} {trend_icon}\n"
                f"📉 RSI: {rsi:.1f} | 🌊 Vol: {vol_ratio}x\n"
                f"📊 Stoch: {stoch_k:.1f}/{stoch_d:.1f}\n"
            )
            groups[category].append(entry)
            
        except Exception as e:
            print(f"Error {asset}: {e}")

    # Build Final Report
    report = "📋 **REPORTE ACTUAL DE PRECIOS**\n\n"
    for cat_name, items in groups.items():
        if items:
            report += f"{cat_name}\n" + "―"*15 + "\n"
            report += "\n".join(items)
            report += "\n\n"
    
    # Avoid empty message error
    if len(report) < 50: report = "❌ No data available."
    
    bot.send_message(message.chat.id, report, parse_mode='Markdown')

@bot.message_handler(commands=['debug'])
def handle_debug(message):
    """Runs system diagnostics"""
    user_id = str(message.chat.id)
    if TELEGRAM_ADMIN_ID and user_id != TELEGRAM_ADMIN_ID:
        bot.reply_to(message, "⛔ Access Denied.")
        return

    bot.reply_to(message, "🕵️ Running diagnostics...")
    try:
        from utils.diagnostics import run_diagnostics
        report = run_diagnostics()
        if len(report) > 4000:
            for x in range(0, len(report), 4000):
                bot.send_message(message.chat.id, report[x:x+4000], parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, report, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ diagnostic failed: {e}")

# --- CONFIGURATION COMMANDS ---

@bot.message_handler(commands=['config'])
def handle_config(message):
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        bot.reply_to(message, "❌ No session found. Use `/set_keys` first.")
        return

    cfg = session.get_configuration()
    
    msg = (
        "⚙️ **YOUR CONFIGURATION**\n\n"
        f"🔑 **API Access:** {'✅ Ready' if cfg['has_keys'] else '❌ Missing/Invalid'}\n"
        f"🕹️ **Leverage:** {cfg['leverage']}x\n"
        f"💰 **Max Margin:** {cfg['max_capital_pct']*100:.1f}% of balance\n"
        f"🛡️ **Stop Loss:** {cfg['stop_loss_pct']*100:.1f}%\n"
        f"🌍 **Proxy:** {'Enabled' if cfg['proxy_enabled'] else 'Disabled'}\n\n"
        "To change:\n"
        "`/set_leverage 10`\n"
        "`/set_margin 0.1`\n"
        "`/set_sl 0.02`"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.message_handler(commands=['set_leverage'])
def handle_set_leverage(message):
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    if not session: return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/set_leverage 10` (Integer 1-125)")
            return
            
        val = int(args[1])
        if 1 <= val <= 125:
            new_val = session.update_config('leverage', val)
            session_manager.save_sessions()
            bot.reply_to(message, f"✅ Leverage set to **{new_val}x**")
        else:
            bot.reply_to(message, "❌ Invalid value. Must be 1-125.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['set_margin'])
def handle_set_margin(message):
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    if not session: return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/set_margin 0.1` (Float 0.01-1.0)")
            return
            
        val = float(args[1])
        if 0.01 <= val <= 1.0:
            new_val = session.update_config('max_capital_pct', val)
            session_manager.save_sessions()
            bot.reply_to(message, f"✅ Max Margin set to **{new_val*100:.1f}%**")
        else:
            bot.reply_to(message, "❌ Invalid value. Must be 0.01 - 1.0")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['set_sl'])
def handle_set_sl(message):
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    if not session: return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/set_sl 0.02` (Float 0.005-0.5)")
            return
            
        val = float(args[1])
        if 0.001 <= val <= 0.5:
            new_val = session.update_config('stop_loss_pct', val)
            session_manager.save_sessions()
            bot.reply_to(message, f"✅ Stop Loss set to **{new_val*100:.2f}%**")
        else:
            bot.reply_to(message, "❌ Invalid value. Must be 0.001 - 0.5")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "🤖 **ANTIGRAVITY BOT HELP**\n\n"
        "**🔑 Session Management**\n"
        "`/set_keys <API_KEY> <API_SECRET>`\n"
        "Register your Binance keys to start trading.\n"
        "`/delete_keys` — Remove your keys.\n"
        "`/config` — View current settings.\n\n"
        
        "**⚙️ Configuration**\n"
        "`/set_leverage <1-125>` — Set leverage (e.g. 10).\n"
        "`/set_margin <0.01-1.0>` — Set max margin % per trade.\n"
        "`/set_sl <0.005-0.5>` — Set Stop Loss % (e.g. 0.02).\n\n"
        
        "**📊 Market & Trading**\n"
        "`/price` — View market prices & indicators.\n"
        "`/long <SYMBOL>` — Manually open a Long position.\n\n"
        
        "**🛠️ System**\n"
        "`/debug` — Run diagnostics (Admin only)."
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

# --- ENTRY POINT ---

def start_bot():
    global session_manager
    # 1. Initialize Session Manager
    session_manager = SessionManager()
    
    # 2. Start Telegram Polling
    if bot:
        print("📡 Starting Telegram Polling...")
        t = threading.Thread(target=bot.infinity_polling, kwargs={'interval': 1, 'timeout': 20}) 
        t.daemon = True 
        t.start()
    
    # 3. Run Trading Loop
    print("🚀 Trading Loop Started (60s interval)...")
    cycle_count = 0
    alert_history = {} 
    
    while True:
        cycle_count += 1
        
        # Heartbeat
        if cycle_count % 60 == 0:
            print(f"🟢 Cycle {cycle_count}: Bot online.")
        
        for asset in WATCHLIST:
            try:
                # 1. Fetch Data
                # Need 300 candles for EMA_200
                df = get_market_data(asset, timeframe='15m', limit=300)
                if df.empty: continue

                # 2. Analyze
                buy_signal, metrics = analyze_market(df)
                
                # 3. Alert & Trade
                if buy_signal:
                    current_time = time.time()
                    if asset not in alert_history: alert_history[asset] = []
                    alert_history[asset] = [t for t in alert_history[asset] if current_time - t < 300]
                    
                    if len(alert_history[asset]) < 3:
                        price = metrics.get('close', 0)
                        rsi = metrics.get('rsi', 0)
                        
                        msg = f"🚀 *SEÑAL DE COMPRA* \n\n💎 {asset}\n💰 ${price:.2f}\n📉 RSI: {rsi:.2f}"
                        # Broadcast
                        send_alert(msg)
                        
                        alert_history[asset].append(current_time)
                        
                        # --- BINANCE EXECUTION (Multi-Tenant) ---
                        if asset.endswith('USDT'): 
                            sessions = session_manager.get_all_sessions()
                            if not sessions:
                                print(f"⚠️ Signal for {asset}, but no active sessions.")
                            
                            for session in sessions:
                                if session.client: # Only execute if client is valid
                                    print(f"⚡ [Chat {session.chat_id}] Auto-Trading {asset}...")
                                    success, trade_msg = session.execute_long_position(asset)
                                    if success:
                                        bot.send_message(session.chat_id, f"✅ **Auto-Trade Executed:**\n{trade_msg}", parse_mode='Markdown')
                                    else:
                                        # Only notify user of failure if it was attempted (e.g. balance issues), 
                                        # silence connection errors to avoid spam?
                                        if "Insufficient" in trade_msg:
                                            bot.send_message(session.chat_id, f"⚠️ Auto-Trade Failed: {trade_msg}", parse_mode='Markdown')
                                        else:
                                            print(f"❌ [Chat {session.chat_id}] User Trade Failed: {trade_msg}")

                    else:
                        print(f"⚠️ Rate limit hit for {asset}.")
            
            except Exception as e:
                print(f"Error processing {asset}: {e}")
        
        print("--- Cycle complete. Waiting 60s ---")
        time.sleep(60)

if __name__ == "__main__":
    try:
        start_bot()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")

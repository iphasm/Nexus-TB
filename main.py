import time
import os
import threading
import telebot
from dotenv import load_dotenv

# Import internal modules
from data.fetcher import get_market_data
from strategies.analyzer import analyze_market

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
WATCHLIST = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 
    'ADA-USD', 'ZEC-USD', 
    'MSFT', 'TSLA', 'NVDA', 'GC=F', 'CL=F']
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_IDS = [id.strip() for id in os.getenv('TELEGRAM_CHAT_ID', '').split(',') if id.strip()]

# Initialize Bot
bot = None
trader = None # Global trader instance

if TELEGRAM_TOKEN:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
else:
    print("WARNING: TELEGRAM_TOKEN not found.")

TELEGRAM_ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')

def send_alert(message):
    """Wrapper to send messages using TeleBot instance"""
    if bot and TELEGRAM_CHAT_IDS:
        for chat_id in TELEGRAM_CHAT_IDS:
            try:
                bot.send_message(chat_id, message, parse_mode='Markdown')
            except Exception as e:
                print(f"Error sending alert to {chat_id}: {e}")
    else:
        print(f"ALERT (No Telegram): {message}")

# --- BOT COMMAND HANDLERS ---

@bot.message_handler(commands=['long'])
def handle_long_position(message):
    """Manually trigger a LONG position with calculated risk management"""
    user_id = str(message.chat.id)
    
    # 🔒 Security Check
    if not TELEGRAM_ADMIN_ID or user_id != TELEGRAM_ADMIN_ID:
        bot.reply_to(message, "⛔ Access Denied. You are not the administrator.")
        return

    # Parse message: /long BTC
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/long <SYMBOL>` (e.g., `/long BTC`)", parse_mode='Markdown')
            return
            
        symbol = args[1].upper()
        # Normalization
        if 'USDT' not in symbol:
            symbol += 'USDT'
            
        bot.reply_to(message, f"⚡ Executing LONG for **{symbol}**...", parse_mode='Markdown')
        
        # Execute
        if trader:
            success = trader.execute_long_position(symbol)
            if success:
                bot.reply_to(message, f"✅ Trade Executed for {symbol}!")
            else:
                bot.reply_to(message, f"❌ Trade Failed for {symbol}. Check logs.")
        else:
             bot.reply_to(message, "❌ Trading System not initialized.")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['price', 'precios'])
def handle_price_request(message):
    """Handles /price command to show current status of all assets"""
    user_id = str(message.chat.id)
    
    # Optional: Security check to only reply to owner
    if TELEGRAM_CHAT_IDS and user_id not in TELEGRAM_CHAT_IDS:
        bot.reply_to(message, "⛔ Unauthorized.")
        return

    bot.reply_to(message, "⏳ Fetching prices... please wait.")
    
    report = "📊 **MARKET REPORT**\n\n"
    
    for asset in WATCHLIST:
        try:
            # Fetch sufficient data for RSI (limit=100) instead of just 5
            df = get_market_data(asset, timeframe='15m', limit=100)
            
            if df.empty:
                report += f"❌ {asset}: No data\n"
                continue
                
            # Get latest close
            latest = df.iloc[-1]
            price = latest['close']
            
            # Simple RSI calculation for context (optional, reuse analyzer if inexpensive)
            # Re-running full analysis might be heavy, but let's do it for consistency
            _, metrics = analyze_market(df)
            rsi = metrics.get('rsi', 0)
            
            report += f"💎 **{asset}**\n💰 ${price:.2f} | 📉 RSI: {rsi:.1f}\n\n"
            
        except Exception as e:
            report += f"⚠️ {asset}: Error ({str(e)[:20]}...)\n"
    
    bot.send_message(message.chat.id, report, parse_mode='Markdown')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🤖 **Trading Bot Active**\n\nCommands:\n/price - Get current market prices")

# --- MAIN TRADING LOOP ---



# --- ENTRY POINT ---

# --- ENTRY POINT ---

def start_bot():
    global trader
    # 1. Initialize Binance Manager
    from utils.trading_manager import BinanceManager
    trader = BinanceManager()
    
    # 2. Start Telegram Polling in a separate thread
    if bot:
        print("📡 Starting Telegram Polling...")
        t = threading.Thread(target=bot.infinity_polling, kwargs={'interval': 1, 'timeout': 20}) 
        t.daemon = True 
        t.start()
    
    # 3. Run Trading Loop
    print("🚀 Trading Loop Started (60s interval)...")
    cycle_count = 0
    alert_history = {} # Key: asset, Value: list of timestamps
    
    while True:
        cycle_count += 1
        
        # Heartbeat
        if cycle_count % 60 == 0:
            send_alert(f"🟢 **STATUS REPORT**\nBot online. Scan cycle: {cycle_count}")
        
        for asset in WATCHLIST:
            try:
                # 1. Fetch Data
                df = get_market_data(asset, timeframe='15m', limit=100)
                
                if df.empty:
                    print(f"Skipping {asset}: No data.")
                    continue

                # 2. Analyze
                buy_signal, metrics = analyze_market(df)
                
                # 3. Alert & Trade
                if buy_signal:
                    current_time = time.time()
                    
                    if asset not in alert_history:
                        alert_history[asset] = []
                    
                    # Rate Limit
                    alert_history[asset] = [t for t in alert_history[asset] if current_time - t < 300]
                    
                    if len(alert_history[asset]) < 3:
                        price = metrics.get('close', 0)
                        rsi = metrics.get('rsi', 0)
                        print(f"🚨 BUY SIGNAL: {asset} | Price: {price:.2f} | RSI: {rsi:.2f}")
                        
                        msg = f"🚀 *SEÑAL DE COMPRA DETECTADA* \n\n💎 Activo: {asset}\n💰 Precio: {price:.2f}\n📉 RSI: {rsi:.2f}"
                        send_alert(msg)
                        
                        alert_history[asset].append(current_time)
                        
                        # --- BINANCE EXECUTION (Crypto Only) ---
                        if 'USD' in asset and '-' in asset: # e.g. BTC-USD
                            binance_symbol = asset.replace('-', '').replace('USD', 'USDT')
                            print(f"⚡ Attempting Trade on {binance_symbol}...")
                            trader.execute_long_position(binance_symbol)
                            
                    else:
                        print(f"⚠️ Rate limit hit for {asset}. Skipping.")
            
            except Exception as e:
                print(f"Error processing {asset}: {e}")
        
        print("--- Cycle complete. Waiting 60s ---")
        time.sleep(60)

if __name__ == "__main__":
    try:
        start_bot()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")

"""
ML Model Training Script v3.1 - XGBoost with Enhanced Features
- XGBoost Classifier with proper regularization
- RobustScaler for crypto outlier handling
- TimeSeriesSplit for chronological validation
- compute_sample_weight for class balancing (fixes scalp 1.5% imbalance)
- New features: ema20_slope, mfi, dist_50_high/low, hour_of_day, day_of_week
"""

import asyncio
import os
import sys
import time
import signal
import logging
import joblib
import pandas as pd
import numpy as np
import argparse
from tqdm import tqdm
from xgboost import XGBClassifier
from sklearn.preprocessing import RobustScaler, LabelEncoder
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import classification_report
from binance.client import Client
import warnings
import requests
warnings.filterwarnings('ignore')

import yfinance as yf
from system_directive import get_all_assets, is_crypto
import pandas_ta as ta
from add_new_features import add_all_new_features

# Configure logging with timeout awareness
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global timeout and retry settings
REQUEST_TIMEOUT = 30  # seconds for HTTP requests
MAX_RETRIES = 3  # maximum retry attempts
BATCH_SIZE = 5  # Process symbols in small batches to avoid overwhelming APIs

# Global flag for interruption handling
interrupted = False

def signal_handler(signum, frame):
    """Handle Ctrl+C interruption gracefully"""
    global interrupted
    interrupted = True
    logger.warning("⚠️  Interrupción detectada (Ctrl+C). Finalizando operaciones pendientes...")
    print("\n⚠️  Operación interrumpida por el usuario. Esperando finalización limpia...", flush=True)


def log_progress(message, start_time=None, phase="", force_flush=True):
    """Enhanced logging with timestamps and elapsed time."""
    current_time = time.time()
    timestamp = time.strftime("%H:%M:%S", time.localtime(current_time))

    if start_time:
        elapsed = current_time - start_time
        time_str = f"[{elapsed:.1f}s]"
    else:
        time_str = ""

    if phase:
        output = f"[{timestamp}] {phase} {message} {time_str}"
    else:
        output = f"[{timestamp}] {message} {time_str}"

    print(output, flush=force_flush)
    # Force flush stdout on Windows
    if force_flush:
        sys.stdout.flush()


# Configuration
SYMBOLS = get_all_assets()
INTERVAL = '15m'
# Local output (same directory as script)
MODEL_OUTPUT = 'ml_model.pkl'
SCALER_OUTPUT = 'scaler.pkl'

# Strategy SL/TP configurations (matching real trading logic)
STRATEGY_PARAMS = {
    'trend': {'sl_pct': 0.02, 'tp_pct': 0.04, 'min_adx': 25},
    'scalp': {'sl_pct': 0.008, 'tp_pct': 0.012, 'min_atr_pct': 1.5},
    'grid': {'sl_pct': 0.015, 'tp_pct': 0.015, 'max_atr_pct': 0.8},
    'mean_rev': {'sl_pct': 0.018, 'tp_pct': 0.025, 'rsi_low': 30, 'rsi_high': 70},
}


def fetch_data_with_timeout(symbol, max_candles=35000, verbose=False):
    """Fetches historical data with simple timeout handling."""
    global interrupted

    if interrupted:
        if verbose:
            print(f"  ⚠️  Fetch interrumpido para {symbol}", flush=True)
        return None

    try:
        if verbose:
            print(f"  📡 Conectando a API para {symbol}...", flush=True)

        start_time = time.time()

        if is_crypto(symbol):
            return fetch_crypto_data(symbol, max_candles, verbose, start_time)
        else:
            return fetch_stock_data(symbol, max_candles, verbose, start_time)

    except Exception as e:
        if verbose:
            print(f"  ❌ Error en {symbol}: {str(e)}", flush=True)
        return None

def fetch_crypto_data(symbol, max_candles, verbose, start_time):
    """Fetch crypto data from Binance."""
    global interrupted

    try:
        if verbose:
            print(f"  🔧 Creando cliente Binance...", flush=True)

        client = Client()

        if verbose:
            print(f"  📊 Descargando datos de {symbol}...", flush=True)

        # Single request for simplicity
        klines = client.futures_klines(
            symbol=symbol,
            interval=INTERVAL,
            limit=min(max_candles, 1500)  # Limit to max 1500 per request
        )

        if verbose:
            print(f"  ✅ Recibidos {len(klines)} registros de {symbol}", flush=True)

        # Process data
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        df = df.astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('timestamp').reset_index(drop=True)

        return df

    except Exception as e:
        if verbose:
            print(f"  ❌ Error en Binance para {symbol}: {str(e)}", flush=True)
        return None

def fetch_stock_data(symbol, max_candles, verbose, start_time):
    """Fetch stock data from Yahoo Finance."""
    try:
        if verbose:
            print(f"  📊 Descargando datos de Yahoo Finance para {symbol}...", flush=True)

        ticker = yf.Ticker(symbol)
        df = ticker.history(period="59d", interval="15m")

        if df.empty:
            if verbose:
                print(f"  ❌ {symbol}: Yahoo Finance retornó datos vacíos", flush=True)
            return None

        if verbose:
            print(f"  ✅ {symbol}: {len(df)} filas descargadas", flush=True)

        # Process the data
        df.reset_index(inplace=True)
        df.rename(columns={
            'Date': 'timestamp', 'Datetime': 'timestamp',
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume'
        }, inplace=True)

        if df['timestamp'].dt.tz is not None:
            df['timestamp'] = df['timestamp'].dt.tz_localize(None)

        return df

    except Exception as e:
        if verbose:
            print(f"  ❌ Error en Yahoo Finance para {symbol}: {str(e)}", flush=True)
        return None

# Alias for backward compatibility
def fetch_data(symbol, max_candles=35000, verbose=False):
    """Legacy function - redirects to timeout-aware version."""
    return fetch_data_with_timeout(symbol, max_candles, verbose)


def calculate_adx(df, period=14):
    """Calculate proper ADX using pandas-ta."""
    adx_df = ta.adx(df['high'], df['low'], df['close'], length=period)
    if adx_df is None:
        return pd.Series(0, index=df.index)
    return adx_df.iloc[:, 0].fillna(0).clip(0, 100)


def calculate_mfi(df, period=14):
    """Calculate MFI using pandas-ta."""
    mfi = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=period)
    if mfi is None:
        return pd.Series(50, index=df.index)
    return mfi.fillna(50).clip(0, 100)


def add_indicators(df):
    """
    Calculate ALL technical indicators for training.
    EXTENDED FEATURE SET for v3.1
    """
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    
    # === BASIC INDICATORS (using pandas-ta) ===
    # RSI (14)
    df['rsi'] = ta.rsi(close, length=14)
    if df['rsi'] is None:
        df['rsi'] = 50
    df['rsi'] = df['rsi'].fillna(50)
    
    # ATR (14)
    df['atr'] = ta.atr(high, low, close, length=14)
    if df['atr'] is None:
        df['atr'] = 0
    df['atr'] = df['atr'].fillna(0)
    df['atr_pct'] = (df['atr'] / close) * 100
    
    # ADX
    df['adx'] = calculate_adx(df, period=14)
    
    # EMAs (using pandas-ta)
    df['ema_9'] = ta.ema(close, length=9)
    df['ema_20'] = ta.ema(close, length=20)
    df['ema_50'] = ta.ema(close, length=50)
    df['ema_200'] = ta.ema(close, length=200)
    
    # ATR (14)
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    df['atr_pct'] = (df['atr'] / close) * 100
    
    # ADX (Proper calculation)
    df['adx'] = calculate_adx(df, period=14)
    
    # EMAs
    # Fill NaN in EMAs
    for col in ['ema_9', 'ema_20', 'ema_50', 'ema_200']:
        if df[col] is None:
            df[col] = close
        df[col] = df[col].fillna(method='bfill').fillna(close)
    
    # Trend Strength (EMA divergence)
    df['trend_str'] = (df['ema_20'] - df['ema_50']) / close * 100
    
    # Volume Change
    df['vol_ma_5'] = volume.rolling(5).mean()
    df['vol_ma_20'] = volume.rolling(20).mean()
    df['vol_change'] = (df['vol_ma_5'] - df['vol_ma_20']) / (df['vol_ma_20'] + 1e-10)
    
    # === v3.0 FEATURES ===
    
    # MACD (using pandas-ta)
    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    if macd_df is not None:
        df['macd'] = macd_df.iloc[:, 0]
        df['macd_signal'] = macd_df.iloc[:, 2]
        df['macd_hist'] = macd_df.iloc[:, 1]
    else:
        df['macd'] = 0
        df['macd_signal'] = 0
        df['macd_hist'] = 0
    df['macd_hist_norm'] = df['macd_hist'] / close * 100
    
    # Bollinger Bands (using pandas-ta)
    bb = ta.bbands(close, length=20, std=2.0)
    if bb is not None:
        df['bb_middle'] = bb.iloc[:, 1]
        df['bb_upper'] = bb.iloc[:, 2]
        df['bb_lower'] = bb.iloc[:, 0]
    else:
        df['bb_middle'] = close
        df['bb_upper'] = close
        df['bb_lower'] = close
    df['bb_std'] = (df['bb_upper'] - df['bb_middle']) / 2
    df['bb_width'] = (df['bb_std'] * 2) / (df['bb_middle'] + 1e-10) * 100
    df['bb_pct'] = (close - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-10)
    
    # Price Momentum (Rate of Change)
    df['roc_5'] = (close - close.shift(5)) / close.shift(5) * 100
    df['roc_10'] = (close - close.shift(10)) / close.shift(10) * 100
    
    # OBV (On-Balance Volume) - normalized
    obv = (np.sign(close.diff()) * volume).cumsum()
    df['obv_change'] = obv.diff(5) / (obv.rolling(20).mean() + 1e-10)
    
    # Price position in range (0-1), using 20 period
    df['price_position'] = (close - low.rolling(20).min()) / (
        high.rolling(20).max() - low.rolling(20).min() + 1e-10
    )
    
    # Candle patterns (simple)
    df['body_pct'] = abs(close - df['open']) / (high - low + 1e-10)
    df['upper_wick'] = (high - pd.concat([close, df['open']], axis=1).max(axis=1)) / (high - low + 1e-10)
    df['lower_wick'] = (pd.concat([close, df['open']], axis=1).min(axis=1) - low) / (high - low + 1e-10)
    
    # Trend direction binary
    df['above_ema200'] = (close > df['ema_200']).astype(int)
    df['ema_cross'] = (df['ema_9'] > df['ema_20']).astype(int)
    
    # === NEW v3.1 FEATURES ===
    
    # EMA20 Slope (momentum direction) - change over 5 periods
    df['ema20_slope'] = (df['ema_20'] - df['ema_20'].shift(5)) / close * 100
    
    # MFI (Money Flow Index) - volume-weighted RSI alternative
    df['mfi'] = calculate_mfi(df, period=14)
    
    # Distance to 50-period High/Low (structure)
    high_50 = high.rolling(50).max()
    low_50 = low.rolling(50).min()
    df['dist_50_high'] = (close - high_50) / close * 100  # Negative = below high
    df['dist_50_low'] = (close - low_50) / close * 100    # Positive = above low
    
    # Time-based features (seasonality)
    if 'timestamp' in df.columns:
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
    else:
        df['hour_of_day'] = 12  # Default to noon
        df['day_of_week'] = 2   # Default to Wednesday
    
    df.dropna(inplace=True)
    return df


def simulate_trade(df, idx, strategy, lookforward=24):
    """
    Simulate a trade starting at index 'idx' using strategy parameters.
    Returns True if TP was hit before SL (profitable), False otherwise.
    
    lookforward: number of candles to simulate (24 = 6 hours on 15m)
    """
    params = STRATEGY_PARAMS.get(strategy, STRATEGY_PARAMS['mean_rev'])
    entry_price = df.iloc[idx]['close']
    sl_pct = params['sl_pct']
    tp_pct = params['tp_pct']
    
    # Determine direction based on indicators
    rsi = df.iloc[idx]['rsi']
    trend = df.iloc[idx]['trend_str']
    
    # Simple direction logic
    if strategy == 'trend':
        is_long = trend > 0
    elif strategy == 'mean_rev':
        is_long = rsi < 50  # Buy oversold, sell overbought
    else:
        is_long = rsi < 50  # Default
    
    # Set SL/TP prices
    if is_long:
        sl_price = entry_price * (1 - sl_pct)
        tp_price = entry_price * (1 + tp_pct)
    else:
        sl_price = entry_price * (1 + sl_pct)
        tp_price = entry_price * (1 - tp_pct)
    
    # Simulate forward
    max_idx = min(idx + lookforward, len(df) - 1)
    
    for i in range(idx + 1, max_idx + 1):
        high = df.iloc[i]['high']
        low = df.iloc[i]['low']
        
        if is_long:
            if low <= sl_price:
                return False  # SL hit first
            if high >= tp_price:
                return True   # TP hit first
        else:
            if high >= sl_price:
                return False  # SL hit first
            if low <= tp_price:
                return True   # TP hit first
    
    # Neither hit - check if in profit at end
    final_price = df.iloc[max_idx]['close']
    if is_long:
        return final_price > entry_price
    else:
        return final_price < entry_price


def label_data_v3(df):
    """
    IMPROVED LABELING v3.1 - Trade Simulation Based
    
    For each row, simulates what would happen if each strategy was used.
    Labels with the strategy that would have been most profitable.
    """
    n = len(df)
    labels = ['mean_rev'] * n  # Default
    
    # Pre-compute conditions for strategy eligibility
    adx = df['adx'].values
    atr_pct = df['atr_pct'].values
    rsi = df['rsi'].values
    
    for idx in range(n - 25):  # Need 24 candles forward
        row = df.iloc[idx]
        
        # Determine which strategies are eligible based on current conditions
        eligible = []
        
        # TREND: ADX > 25 indicates trending market
        if adx[idx] > 25:
            eligible.append('trend')
        
        # SCALP: High volatility (ATR% > 1.5%)
        if atr_pct[idx] > 1.5:
            eligible.append('scalp')
        
        # GRID: Low volatility (ATR% < 0.8%)
        if atr_pct[idx] < 0.8:
            eligible.append('grid')
        
        # MEAN_REV: RSI at extremes
        if rsi[idx] < 35 or rsi[idx] > 65:
            eligible.append('mean_rev')
        
        # If no strategy is eligible, default to mean_rev
        if not eligible:
            eligible = ['mean_rev']
        
        # Simulate each eligible strategy and pick the best
        best_strategy = 'mean_rev'
        for strat in eligible:
            if simulate_trade(df, idx, strat):
                best_strategy = strat
                break  # Take first profitable strategy
        
        labels[idx] = best_strategy
    
    df['target'] = labels
    
    # Remove last 25 rows (no future data)
    df = df.iloc[:-25].copy()
    df.dropna(inplace=True)

    # Add new features to reduce ATR dependence
    df = add_all_new_features(df)

    return df


def train():
    # ANSI Colors
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    RESET = "\033[0m"

    # Setup signal handling for graceful interruption
    signal.signal(signal.SIGINT, signal_handler)

    # Start timing
    total_start_time = time.time()
    logger.info("🚀 Iniciando proceso de entrenamiento ML")

    print("=" * 70, flush=True)
    print("🧠 NEXUS CORTEX TRAINING v3.1 - Enhanced Progress Mode", flush=True)
    print("=" * 70, flush=True)
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"💻 Platform: {sys.platform}", flush=True)
    print(f"🐍 Python: {sys.version.split()[0]}", flush=True)
    print("", flush=True)
    log_progress("🔧 Verificando dependencias del sistema...", total_start_time)

    # Test basic imports before proceeding
    try:
        import pandas as pd
        import numpy as np
        import xgboost
        from binance.client import Client
        from system_directive import get_all_assets, is_crypto
        print("✅ Todas las dependencias cargadas correctamente", flush=True)
    except ImportError as e:
        print(f"❌ Error de importación crítica: {e}", flush=True)
        print("🔧 Verifica que todas las librerías estén instaladas: pip install -r requirements.txt", flush=True)
        return
    except Exception as e:
        print(f"❌ Error inesperado en carga de dependencias: {e}", flush=True)
        return

    log_progress("📊 Cargando configuración de activos...", total_start_time)

    # Test symbol configuration
    try:
        test_symbols = get_all_assets()
        print(f"✅ Configuración de {len(test_symbols)} símbolos cargada", flush=True)
    except Exception as e:
        print(f"❌ Error cargando configuración de símbolos: {e}", flush=True)
        return

    log_progress("🚀 Iniciando proceso de entrenamiento ML", total_start_time)

    # Parse Arguments
    log_progress("⚙️ Procesando argumentos de línea de comandos...", total_start_time)
    parser = argparse.ArgumentParser(description='Nexus Cortex Trainer - Enhanced ML Training with Real-time Progress')
    parser.add_argument('--candles', type=str, default='15000',
                       help='Number of 15m candles to analyze (default: 15000 = ~15.6 days)')
    parser.add_argument('--interactive', action='store_true',
                       help='Run in interactive mode (ask for input instead of using defaults)')
    parser.add_argument('--verbose', action='store_true',
                       help='Extra verbose output with additional debugging info')
    parser.add_argument('--symbols', type=int, default=None,
                       help='Limit number of symbols to process (for testing)')
    args = parser.parse_args()

    print(f"📋 Argumentos parseados: candles={args.candles}, interactive={args.interactive}, symbols={args.symbols}", flush=True)

    # Force flush output to ensure real-time display on Windows
    sys.stdout.flush()

    # Validate candles parameter
    try:
        max_candles = int(args.candles)
        if max_candles < 1000:
            print(f"{YELLOW}⚠️  Advertencia: {max_candles} velas es muy poco. Recomendado: mínimo 5000{RESET}", flush=True)
        elif max_candles > 50000:
            print(f"{YELLOW}⚠️  Advertencia: {max_candles} velas es mucho. Puede tomar mucho tiempo{RESET}", flush=True)
    except ValueError:
        print(f"{RED}❌ Error: '{args.candles}' no es un número válido{RESET}", flush=True)
        max_candles = 15000

    # Limit symbols if specified (for testing)
    global SYMBOLS
    if args.symbols:
        SYMBOLS = SYMBOLS[:args.symbols]
        print(f"{YELLOW}🧪 MODO TEST: Limitando a {args.symbols} símbolos{RESET}", flush=True)

    # Interactive Input (Only if explicitly requested)
    if args.interactive:
        try:
            user_input = input(f"⚡ Cantidad de velas a analizar? [Default {max_candles}]: ").strip()
            if user_input:
                max_candles = int(user_input)
                print(f"{GREEN}✅ Usando {max_candles} velas por símbolo{RESET}", flush=True)
        except ValueError:
            print(f"{RED}⚠️ Entrada inválida, usando {max_candles}.{RESET}", flush=True)

    # Show final configuration
    days_estimate = max_candles * 15 / (60 * 24)  # 15min candles to days
    log_progress(f"📊 Configuración final: {len(SYMBOLS)} símbolos, {max_candles} velas (≈{days_estimate:.1f} días), {INTERVAL} intervalo")
    print(f"🕯️ Velas por símbolo: {max_candles:,} (≈{days_estimate:.1f} días de datos)", flush=True)
    print(f"📈 Símbolos a procesar: {len(SYMBOLS)}", flush=True)
    if args.verbose:
        print(f"🔧 Modo verbose activado", flush=True)
    print("", flush=True)
    print(f"⏰ Intervalo temporal: {INTERVAL}")

    all_data = []
    data_collection_start = time.time()
    log_progress("📥 FASE 1: Descarga de datos históricos", data_collection_start, "📥")
    
    # Progress bar for downloading with enhanced progress and timeout handling
    total_symbols = len(SYMBOLS)
    symbols_processed = 0
    successful_downloads = 0

    log_progress(f"Iniciando descarga de {total_symbols} símbolos en lotes de {BATCH_SIZE}...", data_collection_start)

    # Process symbols in batches to avoid overwhelming APIs
    symbol_batches = [SYMBOLS[i:i + BATCH_SIZE] for i in range(0, len(SYMBOLS), BATCH_SIZE)]

    with tqdm(total=total_symbols, desc="📥 Descargando Datos", unit="sym",
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

        for batch_idx, batch in enumerate(symbol_batches):
            if interrupted:
                logger.warning("⚠️  Descarga interrumpida por el usuario")
                break

            log_progress(f"Procesando lote {batch_idx + 1}/{len(symbol_batches)}: {len(batch)} símbolos", data_collection_start)

            for symbol in batch:
                if interrupted:
                    break

                symbol_start_time = time.time()
                log_progress(f"Descargando {symbol}...", symbol_start_time, f"📊 [{symbols_processed+1}/{total_symbols}]")
            try:
                log_progress(f"Descargando {symbol}...", symbol_start_time, f"📊 [{symbols_processed+1}/{total_symbols}]")

                # Use interactive max_candles with verbose output
                verbose_fetch = args.verbose or args.interactive
                df = fetch_data(symbol, max_candles=max_candles, verbose=verbose_fetch)

                if df is not None and not df.empty:
                    log_progress(f"Calculando indicadores técnicos para {symbol}...", symbol_start_time)
                    df = add_indicators(df)

                    log_progress(f"Simulando trades y etiquetando datos para {symbol}...", symbol_start_time)
                    df = label_data_v3(df)

                    if len(df) > 100:
                        all_data.append(df)
                        successful_downloads += 1
                        pbar.set_postfix_str(f"{GREEN}✓ {symbol} ({len(df)} muestras){RESET}")
                        log_progress(f"✅ {symbol} completado - {len(df)} muestras válidas", symbol_start_time)
                    else:
                        pbar.set_postfix_str(f"{YELLOW}⚠ {symbol} (Datos insuficientes){RESET}")
                        log_progress(f"⚠️ {symbol} - Datos insuficientes ({len(df)} muestras)", symbol_start_time)
                else:
                    pbar.set_postfix_str(f"{RED}✗ {symbol} (Sin datos){RESET}")
                    log_progress(f"❌ {symbol} - Error en descarga", symbol_start_time)

            except Exception as e:
                pbar.set_postfix_str(f"{RED}💥 {symbol} (Error){RESET}")
                log_progress(f"💥 Error procesando {symbol}: {str(e)[:50]}...", symbol_start_time)

            symbols_processed += 1
            pbar.update(1)

    data_collection_time = time.time() - data_collection_start
    log_progress(f"✅ FASE 1 completada en {data_collection_time:.1f}s", data_collection_start)
    log_progress(f"📊 Resultados: {successful_downloads}/{total_symbols} símbolos exitosos")

    if not all_data:
        log_progress("❌ ERROR CRÍTICO: No se pudo recolectar datos de ningún símbolo", data_collection_start)
        print(f"\n{RED}❌ No data collected.{RESET}")
        return

    # FASE 2: Preparación de datos
    data_prep_start = time.time()
    log_progress("🔧 FASE 2: Preparación y preprocesamiento de datos", data_prep_start, "🔧")

    log_progress("Uniendo datasets de todos los símbolos...", data_prep_start)
    full_df = pd.concat(all_data, ignore_index=True)

    log_progress(f"✅ Dataset consolidado: {len(full_df):,} filas totales", data_prep_start)

    # EXTENDED FEATURE SET for v3.1 (21 features)
    X_cols = [
        # Core (original)
        'rsi', 'adx', 'atr_pct', 'trend_str', 'vol_change',
        # v3.0 features
        'macd_hist_norm', 'bb_pct', 'bb_width',
        'roc_5', 'roc_10', 'obv_change',
        'price_position', 'body_pct',
        'above_ema200', 'ema_cross',
        # NEW v3.1 features (reduce ATR dependence)
        'ema20_slope', 'mfi', 'dist_50_high', 'dist_50_low',
        'hour_of_day', 'day_of_week',
        # NEW v3.2 features (further reduce ATR dependence)
        # Momentum features
        'roc_21', 'roc_50', 'williams_r', 'cci', 'ultimate_osc',
        # Volume features
        'volume_roc_5', 'volume_roc_21', 'chaikin_mf', 'force_index', 'ease_movement',
        # Structure features
        'dist_sma20', 'dist_sma50', 'pivot_dist', 'fib_dist',
        # Correlation features
        'morning_volatility', 'afternoon_volatility', 'gap_up', 'gap_down', 'range_change',
        # Sentiment features
        'bull_power', 'bear_power', 'momentum_div', 'vpt', 'intraday_momentum'
    ]

    log_progress(f"Seleccionando {len(X_cols)} features del dataset...", data_prep_start)
    X = full_df[X_cols]
    y = full_df['target']

    print(f"\n{YELLOW}{'='*70}")
    print(f"📊 ESTADÍSTICAS DEL DATASET:")
    print(f"{'='*70}{RESET}")
    print(f"📊 Total muestras: {len(X):,}")
    print(f"📈 Features: {len(X_cols)}")
    print(f"🎯 Estrategias disponibles: {y.nunique()}")
    print(f"📈 Distribución de clases:")
    for label, count in y.value_counts().items():
        pct = count / len(y) * 100
        bar = "█" * int(pct / 2)  # Visual bar
        print(f"   • {label:8}: {count:>8,} ({pct:5.1f}%) {bar}")
    print()

    # Check for data quality
    missing_data = X.isnull().sum().sum()
    if missing_data > 0:
        log_progress(f"⚠️ Detectados {missing_data} valores faltantes - serán tratados", data_prep_start)
    else:
        log_progress("✅ No se detectaron valores faltantes en el dataset", data_prep_start)
    
    # FASE 3: Preprocesamiento de features
    preprocessing_start = time.time()
    log_progress("🔄 FASE 3: Preprocesamiento y transformación de datos", preprocessing_start, "🔄")

    log_progress("Codificando etiquetas de estrategia...", preprocessing_start)
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    class_names = label_encoder.classes_
    log_progress(f"✅ Etiquetas codificadas: {len(class_names)} clases ({', '.join(class_names)})", preprocessing_start)

    log_progress("Aplicando RobustScaler (maneja outliers de cripto)...", preprocessing_start)
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)
    log_progress("✅ Features escalados con RobustScaler", preprocessing_start)

    log_progress("Configurando TimeSeriesSplit para validación chronológica...", preprocessing_start)
    tscv = TimeSeriesSplit(n_splits=5)
    log_progress("✅ Validación cross-temporal configurada (5-fold)", preprocessing_start)

    log_progress("Calculando pesos de muestra para balanceo de clases...", preprocessing_start)
    sample_weights = compute_sample_weight('balanced', y_encoded)
    weight_stats = pd.Series(sample_weights).describe()
    log_progress(f"✅ Pesos calculados - Media: {weight_stats['mean']:.3f}, Rango: [{weight_stats['min']:.3f}, {weight_stats['max']:.3f}]", preprocessing_start)
    
    # FASE 4: Entrenamiento del modelo XGBoost
    training_start = time.time()
    log_progress("🚀 FASE 4: Entrenamiento del modelo XGBoost", training_start, "🚀")

    log_progress("Configurando hiperparámetros del modelo...", training_start)
    model = XGBClassifier(
        objective='multi:softprob',
        num_class=len(class_names),
        max_depth=5,
        n_estimators=300,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,  # L1 regularization
        reg_lambda=1.0, # L2 regularization
        random_state=42,
        n_jobs=-1,
        use_label_encoder=False,
        eval_metric='mlogloss'
    )

    hyperparams = {
        "Profundidad máxima": model.max_depth,
        "Estimadores": model.n_estimators,
        "Tasa de aprendizaje": model.learning_rate,
        "Subsample": model.subsample,
        "Regularización L1": model.reg_alpha,
        "Regularización L2": model.reg_lambda
    }

    print(f"{CYAN}Hiperparámetros del modelo:")
    for param, value in hyperparams.items():
        print(f"   • {param}: {value}")
    print(f"{RESET}")

    # TimeSeriesSplit Cross-Validation (manual to support sample_weight)
    cv_scores = []
    log_progress("Ejecutando validación cruzada chronológica (5-fold)...", training_start)

    fold_start_time = time.time()

    # Progress bar for CV with enhanced formatting
    with tqdm(total=5, desc="🔍 Cross-Validation", unit="fold",
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as cv_pbar:

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X_scaled)):
            fold_start = time.time()
            log_progress(f"Entrenando fold {fold+1}/5...", fold_start, f"📊 Fold {fold+1}")

            X_cv_train, X_cv_val = X_scaled[train_idx], X_scaled[val_idx]
            y_cv_train, y_cv_val = y_encoded[train_idx], y_encoded[val_idx]
            weights_cv = sample_weights[train_idx]

            log_progress(f"Preparando datos: {len(X_cv_train):,} train, {len(X_cv_val):,} val", fold_start)

            cv_model = XGBClassifier(
                objective='multi:softprob',
                num_class=len(class_names),
                max_depth=5,
                n_estimators=300,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=-1,
                verbosity=0
            )

            cv_model.fit(X_cv_train, y_cv_train, sample_weight=weights_cv)
            score = cv_model.score(X_cv_val, y_cv_val)
            cv_scores.append(score)

            fold_time = time.time() - fold_start
            log_progress(f"✅ Fold {fold+1} completado - Accuracy: {score:.3f} ({fold_time:.1f}s)", fold_start)
            cv_pbar.update(1)

    cv_scores = np.array(cv_scores)
    cv_time = time.time() - fold_start_time
    log_progress(f"✅ Validación cruzada completada en {cv_time:.1f}s", training_start)

    print(f"\n{GREEN}📊 RESULTADOS CROSS-VALIDATION:")
    print(f"   • Accuracy promedio: {cv_scores.mean():.3f}")
    print(f"   • Desviación estándar: {cv_scores.std():.3f}")
    print(f"   • Rango: [{cv_scores.min():.3f}, {cv_scores.max():.3f}]")
    print(f"   • Intervalo confianza (95%): {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    print(f"{RESET}")
    
    # FASE 5: Entrenamiento final y evaluación
    final_training_start = time.time()
    log_progress("🏋️ FASE 5: Entrenamiento final en dataset completo", final_training_start, "🏋️")

    log_progress("Entrenando modelo final con todos los datos...", final_training_start)
    model.fit(X_scaled, y_encoded, sample_weight=sample_weights)
    training_time = time.time() - final_training_start
    log_progress(f"✅ Entrenamiento completado en {training_time:.1f}s", final_training_start)

    # Evaluate on last 20% (time-respecting split)
    log_progress("Evaluando modelo en conjunto de test (últimas 20% muestras chronológicas)...", final_training_start)
    split_idx = int(len(X_scaled) * 0.8)
    X_test = X_scaled[split_idx:]
    y_test = y_encoded[split_idx:]

    log_progress(f"Conjunto de test: {len(X_test):,} muestras ({len(X_test)/len(X_scaled)*100:.1f}% del total)", final_training_start)

    print(f"\n{MAGENTA}{'='*70}")
    print(f"📈 EVALUACIÓN EN CONJUNTO DE TEST:")
    print(f"{'='*70}{RESET}")

    preds = model.predict(X_test)
    # Use explicit labels to avoid errors when test set doesn't contain all classes
    print(classification_report(y_test, preds, target_names=class_names, 
                                labels=range(len(class_names)), zero_division=0))

    # Feature Importance (top 15)
    log_progress("Analizando importancia de features...", final_training_start)
    print(f"\n{YELLOW}🔑 TOP 15 FEATURES MÁS IMPORTANTES:")
    print(f"{'='*50}{RESET}")

    importance_pairs = sorted(zip(X_cols, model.feature_importances_), key=lambda x: -x[1])
    for i, (feat, imp) in enumerate(importance_pairs[:15], 1):
        bar = "█" * int(imp * 50)
        rank_indicator = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}"
        print(f"   {rank_indicator} {feat:18} {imp:.3f} {bar}")

    # Check ATR dependence reduction
    atr_importance = dict(importance_pairs).get('atr_pct', 0)
    print(f"\n{CYAN}📊 ANÁLISIS DE DEPENDENCIA ATR:")
    print(f"   • Importancia actual de ATR: {atr_importance:.1%}")
    print(f"   • Objetivo: <25% para reducir dependencia de volatilidad")

    if atr_importance < 0.25:
        print(f"   ✅ {GREEN}ATR dependence reduced: {atr_importance:.1%} (target <25%){RESET}")
    else:
        print(f"   ⚠️ {RED}ATR still high: {atr_importance:.1%} (consider adding more features){RESET}")

    # FASE 6: Guardado del modelo
    save_start = time.time()
    log_progress("💾 FASE 6: Guardando modelo y scaler", save_start, "💾")

    model_dir = os.path.dirname(MODEL_OUTPUT)
    if model_dir:  # Only create directory if path specified
        os.makedirs(model_dir, exist_ok=True)
        log_progress(f"Creando directorio {model_dir}...", save_start)

    # Store class names with model for proper decoding
    model_data = {
        'model': model,
        'label_encoder': label_encoder,
        'feature_names': X_cols
    }

    log_progress(f"Guardando modelo en {MODEL_OUTPUT}...", save_start)
    joblib.dump(model_data, MODEL_OUTPUT)

    log_progress(f"Guardando scaler en {SCALER_OUTPUT}...", save_start)
    joblib.dump(scaler, SCALER_OUTPUT)

    save_time = time.time() - save_start
    log_progress(f"✅ Archivos guardados exitosamente en {save_time:.1f}s", save_start)

    # RESUMEN FINAL
    total_time = time.time() - total_start_time
    end_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*70}", flush=True)
    print(f"🎉 ENTRENAMIENTO COMPLETADO EXITOSAMENTE!", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"⏱️  Tiempo total: {total_time:.1f}s ({total_time/60:.1f} minutos)", flush=True)
    print(f"📊 Muestras procesadas: {len(X):,}", flush=True)
    print(f"🎯 Accuracy CV: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})", flush=True)
    print(f"📁 Modelo guardado: {MODEL_OUTPUT}", flush=True)
    print(f"📁 Scaler guardado: {SCALER_OUTPUT}", flush=True)
    print(f"🏁 Finalizado en: {end_timestamp}", flush=True)
    print(f"👉 Para activar ML: restart bot or run: /ml_mode on", flush=True)
    print(f"{'='*70}", flush=True)


if __name__ == "__main__":
    try:
        train()
    except KeyboardInterrupt:
        logger.info("👋 Operación cancelada por el usuario (Ctrl+C)")
        print("\n👋 Operación cancelada por el usuario.")
    except Exception as e:
        logger.error(f"Ocurrió un error inesperado: {e}")
        print(f"\n❌ Ocurrió un error inesperado:\n{e}")
        import traceback
        traceback.print_exc()
    finally:
        if interrupted:
            print("\n🧹 Operación interrumpida - realizando cleanup...")
        print()
        if '--auto' not in str(sys.argv):
             input("🔴 Presione ENTER para salir...")


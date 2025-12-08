import yfinance as yf
import pandas as pd
from pycoingecko import CoinGeckoAPI

# Initialize CoinGecko API
cg = CoinGeckoAPI()

# Symbol Mapping for CoinGecko
# Maps the 'BASE' of 'BASE/QUOTE' to CoinGecko ID
SYMBOL_MAP = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'SOL': 'solana',
    'XRP': 'ripple',
    'ADA': 'cardano',
    'DOGE': 'dogecoin',
    # Add others as needed
}

def get_market_data(symbol: str, timeframe: str = '15m', limit: int = 100) -> pd.DataFrame:
    """
    Fetches market data for a given symbol.
    
    Args:
        symbol: Ticker symbol (e.g., 'BTC/USDT' for crypto, 'AAPL' for stock).
        timeframe: Candle timeframe (default '15m').
        limit: Number of candles to return (default 100).
        
    Returns:
        pd.DataFrame: Columns ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
                      Sorted ascending by timestamp.
    """
    
    # Expected columns
    expected_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    
    try:
        if '/' in symbol:
            # --- CRYPTO (CoinGecko) ---
            base, quote = symbol.split('/')
            coin_id = SYMBOL_MAP.get(base.upper())
            
            if not coin_id:
                print(f"Error: Symbol {base} not found in SYMBOL_MAP for CoinGecko.")
                return pd.DataFrame(columns=expected_cols)
                
            # CoinGecko granularity logic:
            # days=1 -> 30 min candles (Closest to 15m we can get for free)
            # days=14 -> 4 hour candles
            # days=30 -> 4 hour candles
            days = '1' 
            
            # CoinGecko uses 'usd' not 'usdt' typically for vs_currency
            quote_currency = quote.lower()
            if quote_currency == 'usdt':
                quote_currency = 'usd'
            
            # Fetch OHLC
            # Returns: [[time, open, high, low, close], ...]
            ohlc_data = cg.get_coin_ohlc_by_id(id=coin_id, vs_currency=quote_currency, days=days)
            
            if not ohlc_data:
                 print(f"No data returned from CoinGecko for {symbol}")
                 return pd.DataFrame(columns=expected_cols)

            # Convert to DataFrame
            # CoinGecko OHLC does NOT return volume.
            df = pd.DataFrame(ohlc_data, columns=['timestamp', 'open', 'high', 'low', 'close'])
            
            # Add fake volume (0)
            df['volume'] = 0.0
            
            # Convert timestamp (ms to datetime)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
        else:
            # --- STOCK (YFINANCE) ---
            ticker = yf.Ticker(symbol)
            
            # Map timeframe/limit to period for yfinance
            fetch_period = "1mo"
            if timeframe in ['1m', '2m', '5m']:
                fetch_period = "5d"
                
            # Fetch history
            df = ticker.history(interval=timeframe, period=fetch_period)
            
            if df.empty:
                return pd.DataFrame(columns=expected_cols)
            
            # Reset index to make Date/Datetime a column
            df = df.reset_index()
            
            # Rename columns to match expected format
            rename_map = {
                'Date': 'timestamp', 
                'Datetime': 'timestamp',
                'Open': 'open', 
                'High': 'high', 
                'Low': 'low', 
                'Close': 'close', 
                'Volume': 'volume'
            }
            df = df.rename(columns=rename_map)
            
        # --- NORMALIZATION ---
        
        # Ensure correct column order
        # If stock, we have volume. If crypto, we have volume=0.
        # Ensure all cols exist
        for col in expected_cols:
            if col not in df.columns:
                df[col] = 0.0
        
        df = df[expected_cols]
        
        # Ensure ascending order
        df = df.sort_values('timestamp', ascending=True)
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Limit to requested number (tail because we want the MOST RECENT data)
        if len(df) > limit:
            df = df.tail(limit).reset_index(drop=True)
            
        # Ensure numeric types
        cols_numeric = ['open', 'high', 'low', 'close', 'volume']
        df[cols_numeric] = df[cols_numeric].astype(float)
            
        return df

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame(columns=expected_cols)

# Binance API Configuration Fix

## What this fixes
This ensures the bot connects to Binance International API (api.binance.com) 
instead of Binance US (api.binance.us).

## Changes applied
- Added `tld='com'` parameter to all Binance Client initializations
- Updated in: data/fetcher.py, utils/trading_manager.py, debug_binance.py

## Deployment trigger
Last updated: 2025-12-08 23:48

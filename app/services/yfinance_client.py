import yfinance as yf
import asyncio
import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 1  # seconds (doubles each retry: 1s, 2s, 4s)

def retry_with_backoff(func, retries=MAX_RETRIES):
    """Retry a blocking function with exponential backoff."""
    for attempt in range(retries):
        try:
            result = func()
            if result is not None:
                return result
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed: {e}")
        if attempt < retries - 1:
            time.sleep(RETRY_BACKOFF * (2 ** attempt))
    return None

# Indian exchange suffixes to try when a bare symbol isn't found
EXCHANGE_SUFFIXES = ["", ".NS", ".BO"]

def _get_price(ticker):
    """Extract price from a yfinance Ticker object."""
    try:
        if hasattr(ticker, 'fast_info') and 'lastPrice' in ticker.fast_info:
            return ticker.fast_info['lastPrice']
    except Exception:
        pass
    try:
        history = ticker.history(period="1d")
        if not history.empty:
            return history['Close'].iloc[-1]
    except Exception:
        pass
    return None

def resolve_symbol(symbol: str):
    """
    Try the symbol as-is, then with .NS (NSE) and .BO (BSE) suffixes.
    Returns (resolved_symbol, ticker, price) or (None, None, None).
    """
    for suffix in EXCHANGE_SUFFIXES:
        candidate = f"{symbol}{suffix}"
        try:
            ticker = yf.Ticker(candidate)
            price = _get_price(ticker)
            if price is not None:
                return candidate, ticker, price
        except Exception:
            continue
    return None, None, None

async def fetch_stock_price(symbol: str) -> Optional[float]:
    """
    Fetches the latest stock price using yfinance.
    Tries bare symbol, then .NS and .BO for Indian stocks.
    Retries up to 3 times with exponential backoff.
    """
    def _fetch():
        _, _, price = resolve_symbol(symbol)
        return price
            
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: retry_with_backoff(_fetch))

async def fetch_stock_info(symbol: str) -> Optional[Dict[str, any]]:
    """
    Fetches price, company name, sector, and industry.
    Tries bare symbol, then .NS and .BO for Indian stocks.
    Retries up to 3 times with exponential backoff.
    """
    def _fetch():
        resolved, ticker, price = resolve_symbol(symbol)
        if resolved is None:
            return None
        
        try:
            info = ticker.info
            name = info.get('shortName') or info.get('longName') or symbol
            sector = info.get('sector') or "Unknown"
            industry = info.get('industry') or "Unknown"
        except Exception:
            name = symbol
            sector = "Unknown"
            industry = "Unknown"
        
        return {
            "price": price,
            "name": name,
            "sector": sector,
            "industry": industry,
            "resolved_symbol": resolved
        }
            
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: retry_with_backoff(_fetch))

async def fetch_multiple_stock_prices(symbols: list[str]) -> Dict[str, float]:
    """
    Fetches multiple stock prices concurrently.
    """
    tasks = [fetch_stock_price(sym) for sym in symbols]
    prices = await asyncio.gather(*tasks)
    return {sym: price for sym, price in zip(symbols, prices) if price is not None}

async def fetch_multiple_stock_infos(symbols: list[str]) -> Dict[str, Dict[str, any]]:
    """
    Fetches multiple stock infos concurrently.
    """
    tasks = [fetch_stock_info(sym) for sym in symbols]
    infos = await asyncio.gather(*tasks)
    return {sym: info for sym, info in zip(symbols, infos) if info is not None}

async def fetch_fx_rate(base_currency: str, target_currency: str) -> Optional[float]:
    """
    Fetches the latest Forex conversion rate.
    Retries up to 3 times with exponential backoff.
    """
    if base_currency == target_currency:
        return 1.0
        
    def _fetch():
        symbol = f"{base_currency}{target_currency}=X"
        ticker = yf.Ticker(symbol)
        if hasattr(ticker, 'fast_info') and 'lastPrice' in ticker.fast_info:
            return ticker.fast_info['lastPrice']
        history = ticker.history(period="1d")
        if not history.empty:
            return history['Close'].iloc[-1]
        return None
            
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: retry_with_backoff(_fetch))


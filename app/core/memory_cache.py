from cachetools import TTLCache

# Stock price cache: 10,000 items, 60 second TTL
stock_cache = TTLCache(maxsize=10000, ttl=60)

# FX rate cache: 100 items, 300 second (5 min) TTL
fx_cache = TTLCache(maxsize=100, ttl=300)

async def get_from_cache(key: str):
    if key.startswith("FX:"):
        return fx_cache.get(key)
    return stock_cache.get(key)

async def set_to_cache(key: str, value: any, ttl: int = None):
    if key.startswith("FX:"):
        fx_cache[key] = value
    else:
        stock_cache[key] = value

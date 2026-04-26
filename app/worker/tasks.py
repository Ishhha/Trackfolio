import json
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.core.memory_cache import set_to_cache
from app.models.domain import Stock, Portfolio, PortfolioSnapshot
from app.services.yfinance_client import fetch_multiple_stock_prices
from app.services.portfolio_service import calculate_portfolio_summary
from datetime import datetime

async def fetch_active_stock_prices():
    """APScheduler task to fetch and cache stock prices"""
    async with AsyncSessionLocal() as session:
        # Get all distinct active stock symbols
        stmt = select(Stock.symbol).distinct()
        result = await session.execute(stmt)
        symbols = [row[0] for row in result.all()]
        
    if not symbols:
        return
        
    prices = await fetch_multiple_stock_prices(symbols)
    
    # Cache the prices
    for symbol, price in prices.items():
        data = json.dumps({"price": price, "last_updated": datetime.utcnow().isoformat()})
        await set_to_cache(f"STOCK:{symbol}", data)

async def take_portfolio_snapshots():
    """APScheduler task to record daily portfolio snapshots"""
    async with AsyncSessionLocal() as session:
        stmt = select(Portfolio).options(selectinload(Portfolio.stocks))
        result = await session.execute(stmt)
        portfolios = result.scalars().all()
        
        for portfolio in portfolios:
            summary = await calculate_portfolio_summary(portfolio, session)
            
            snapshot = PortfolioSnapshot(
                portfolio_id=portfolio.id,
                total_value=summary.current_value,
                invested_value=summary.total_invested,
                pnl=summary.total_pnl
            )
            session.add(snapshot)
            
        await session.commit()

# ──────────────────────────────────────────────────────────────────
# DISABLED: Periodic FX Rate Fetching
# ──────────────────────────────────────────────────────────────────
# Currently FX rates are fetched on-demand when a user hits the API.
# To enable periodic background fetching instead, do TWO things:
#
# 1. Uncomment the function below.
# 2. In app/main.py, add this line inside the lifespan() function:
#      scheduler.add_job(fetch_fx_rates, 'interval', minutes=5, id='fetch_fx_rates')
# ──────────────────────────────────────────────────────────────────

# async def fetch_fx_rates():
#     """APScheduler task to periodically fetch and cache FX rates."""
#     from app.services.yfinance_client import fetch_fx_rate
#     
#     # Define the currency pairs you want to pre-fetch
#     fx_pairs = [("USD", "INR"), ("INR", "USD")]
#     
#     for base, target in fx_pairs:
#         rate = await fetch_fx_rate(base, target)
#         if rate is not None:
#             await set_to_cache(f"FX:{base}_{target}", str(rate))

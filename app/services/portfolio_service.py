from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.domain import Portfolio, Stock, StockMetadata
from app.schemas.portfolio import PortfolioSummary, StockInsight
from app.core.memory_cache import get_from_cache, set_to_cache
from app.services.yfinance_client import fetch_fx_rate
import json

async def get_stock_price_from_cache(symbol: str) -> float | None:
    """Fetch real-time stock price from memory cache."""
    data = await get_from_cache(f"STOCK:{symbol}")
    if data:
        try:
            parsed = json.loads(data)
            return parsed.get("price")
        except:
            return None
    return None

async def get_fx_rate_from_cache(base: str, target: str) -> float:
    """Fetch live FX rate, with 5-min cache."""
    if base == target:
        return 1.0
        
    cache_key = f"FX:{base}_{target}"
    data = await get_from_cache(cache_key)
    if data:
        try:
            return float(data)
        except:
            pass
            
    # Fetch live and cache
    rate = await fetch_fx_rate(base, target)
    if rate is not None:
        await set_to_cache(cache_key, str(rate), ttl=300) # 5 minutes
        return rate
        
    # Fallback
    return 1.0

async def calculate_portfolio_summary(portfolio: Portfolio, db: AsyncSession = None) -> PortfolioSummary:
    total_invested = 0.0
    current_value = 0.0
    sector_distribution = {}
    stock_pnl_tracker = []  # Track each stock's P&L for top gainer/loser
    stock_value_map = {}  # Track each stock's value for portfolio allocation
    
    # Pre-fetch metadata if DB is provided
    metadata_map = {}
    if db and portfolio.stocks:
        symbols = [s.symbol for s in portfolio.stocks]
        stmt = select(StockMetadata).where(StockMetadata.symbol.in_(symbols))
        result = await db.execute(stmt)
        metas = result.scalars().all()
        metadata_map = {m.symbol: m.sector for m in metas}
    
    for stock in portfolio.stocks:
        invested = stock.quantity * stock.avg_buy_price
        
        current_price = await get_stock_price_from_cache(stock.symbol)
        fx_rate = await get_fx_rate_from_cache(stock.currency, portfolio.currency)
        
        # Convert invested to portfolio currency
        invested_converted = invested * fx_rate
        total_invested += invested_converted
        
        if current_price is not None:
            # Set dynamically on the stock object for the response
            stock.current_price = current_price
            stock.current_value = stock.quantity * current_price
            stock.invested_value = invested
            stock.pnl = stock.current_value - stock.invested_value
            
            current_value_converted = stock.current_value * fx_rate
            current_value += current_value_converted
            stock_value_map[stock.symbol] = current_value_converted
            
            # Track P&L for top gainer/loser
            pnl_pct = (stock.pnl / invested * 100) if invested > 0 else 0.0
            stock_pnl_tracker.append({
                "symbol": stock.symbol,
                "name": getattr(stock, 'name', None) or stock.symbol,
                "pnl": stock.pnl * fx_rate,
                "pnl_percentage": pnl_pct
            })
            
            # Add to sector distribution
            sector = metadata_map.get(stock.symbol, "Unknown")
            sector_distribution[sector] = sector_distribution.get(sector, 0.0) + current_value_converted
        else:
            # Fallback if price is not in cache yet
            stock.current_price = None
            stock.current_value = None
            stock.invested_value = invested
            stock.pnl = None
            current_value += invested_converted
            stock_value_map[stock.symbol] = invested_converted
            
            sector = metadata_map.get(stock.symbol, "Unknown")
            sector_distribution[sector] = sector_distribution.get(sector, 0.0) + invested_converted
    
    total_pnl = current_value - total_invested
    pnl_percentage = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0
    
    # Compute portfolio allocation (percentage weight of each stock)
    stock_allocation = {}
    if current_value > 0:
        stock_allocation = {
            sym: round(val / current_value * 100, 2) for sym, val in stock_value_map.items()
        }
    
    # Determine top gainer and top loser
    top_gainer = None
    top_loser = None
    if stock_pnl_tracker:
        best = max(stock_pnl_tracker, key=lambda x: x["pnl"])
        worst = min(stock_pnl_tracker, key=lambda x: x["pnl"])
        top_gainer = StockInsight(**best)
        top_loser = StockInsight(**worst)
    
    return PortfolioSummary(
        total_invested=total_invested,
        current_value=current_value,
        total_pnl=total_pnl,
        pnl_percentage=pnl_percentage,
        sector_distribution=sector_distribution,
        stock_allocation=stock_allocation,
        top_gainer=top_gainer,
        top_loser=top_loser
    )

async def get_portfolio_by_id(db: AsyncSession, portfolio_id: str, user_id: str) -> Portfolio | None:
    stmt = select(Portfolio).options(selectinload(Portfolio.stocks)).where(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

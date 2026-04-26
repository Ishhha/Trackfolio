from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.core.database import get_db
from app.models.domain import Stock, Portfolio, StockMetadata
from app.schemas.stock import StockCreate, StockResponse, StockUpdate
from app.api.endpoints.portfolios import get_user_id
from app.services.portfolio_service import get_portfolio_by_id
from app.services.yfinance_client import fetch_stock_info

router = APIRouter()

@router.post("/", response_model=StockResponse)
async def add_stock(
    stock_in: StockCreate,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    # Verify portfolio belongs to user
    portfolio = await get_portfolio_by_id(db, stock_in.portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    # Validate stock symbol and get info
    symbol = stock_in.symbol.upper()
    stock_info = await fetch_stock_info(symbol)
    if stock_info is None:
        raise HTTPException(status_code=400, detail="Put correct stock name, stock name is invalid")
    
    # Use the resolved symbol (e.g. INFY -> INFY.NS)
    resolved = stock_info.get("resolved_symbol", symbol)
    
    stock = Stock(
        portfolio_id=stock_in.portfolio_id,
        symbol=resolved,
        name=stock_info["name"],
        quantity=stock_in.quantity,
        avg_buy_price=stock_in.avg_buy_price,
        currency=stock_in.currency
    )
    db.add(stock)
    
    # Save or update metadata
    metadata = StockMetadata(
        symbol=resolved,
        sector=stock_info["sector"],
        industry=stock_info["industry"]
    )
    await db.merge(metadata)
    
    await db.commit()
    await db.refresh(stock)
    return stock

@router.patch("/{stock_id}", response_model=StockResponse)
async def update_stock(
    stock_id: str,
    stock_in: StockUpdate,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    # Fetch stock with portfolio check
    stmt = select(Stock).join(Portfolio).where(
        Stock.id == stock_id,
        Portfolio.user_id == user_id
    )
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
        
    update_data = stock_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stock, key, value)
        
    await db.commit()
    await db.refresh(stock)
    return stock

@router.delete("/{stock_id}")
async def delete_stock(
    stock_id: str,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Stock).join(Portfolio).where(
        Stock.id == stock_id,
        Portfolio.user_id == user_id
    )
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
        
    await db.delete(stock)
    await db.commit()
    return {"status": "deleted"}

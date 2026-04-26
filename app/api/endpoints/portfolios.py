from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import pandas as pd
import io
import uuid
from app.core.database import get_db
from app.models.domain import Portfolio, Stock, StockMetadata, PortfolioSnapshot
from app.schemas.portfolio import PortfolioCreate, PortfolioResponse, PortfolioUpdate, PortfolioSnapshotResponse
from app.services.portfolio_service import calculate_portfolio_summary, get_portfolio_by_id
from app.services.yfinance_client import fetch_multiple_stock_infos
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

router = APIRouter()

def get_user_id(
    x_user_id: Optional[str] = Header(
        default=None,
        description="Optional user identifier. If omitted, a new UUID is auto-generated for anonymous tracking.",
        include_in_schema=True,
    )
) -> str:
    """
    Get the user ID from the X-User-ID header.
    If not provided, auto-generates a UUID for anonymous tracking.
    The caller should save the returned user_id for future requests.
    """
    if not x_user_id:
        return str(uuid.uuid4())
    return x_user_id

@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio_in: PortfolioCreate,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    portfolio = Portfolio(
        user_id=user_id,
        name=portfolio_in.name,
        currency=portfolio_in.currency,
        is_public=portfolio_in.is_public
    )
    db.add(portfolio)
    await db.commit()
    
    # Re-query to eagerly load relationships for the response model
    stmt = select(Portfolio).options(selectinload(Portfolio.stocks)).where(Portfolio.id == portfolio.id)
    result = await db.execute(stmt)
    return result.scalar_one()

@router.get("/", response_model=List[PortfolioResponse])
async def list_portfolios(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Portfolio).options(selectinload(Portfolio.stocks)).where(Portfolio.user_id == user_id)
    result = await db.execute(stmt)
    portfolios = result.scalars().all()
    
    # We won't calculate summary for list to keep it fast, but we could
    return portfolios

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    portfolio = await get_portfolio_by_id(db, portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    summary = await calculate_portfolio_summary(portfolio, db)
    portfolio.summary = summary
    return portfolio

@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: str,
    portfolio_in: PortfolioUpdate,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    portfolio = await get_portfolio_by_id(db, portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    update_data = portfolio_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(portfolio, key, value)
        
    await db.commit()
    return portfolio

@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: str,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    portfolio = await get_portfolio_by_id(db, portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    await db.delete(portfolio)
    await db.commit()
    return {"status": "deleted"}

@router.get("/{portfolio_id}/history", response_model=List[PortfolioSnapshotResponse])
async def get_portfolio_history(
    portfolio_id: str,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve historical portfolio snapshots for performance tracking."""
    portfolio = await get_portfolio_by_id(db, portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    stmt = select(PortfolioSnapshot).where(
        PortfolioSnapshot.portfolio_id == portfolio_id
    ).order_by(PortfolioSnapshot.timestamp.desc())
    result = await db.execute(stmt)
    snapshots = result.scalars().all()
    return snapshots

@router.post("/{portfolio_id}/import")
async def import_portfolio_csv(
    portfolio_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    portfolio = await get_portfolio_by_id(db, portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # Verify columns
        required_cols = {'symbol', 'quantity', 'avg_price'}
        if not required_cols.issubset(set(df.columns)):
            raise HTTPException(status_code=400, detail="CSV must contain columns: symbol, quantity, avg_price")
            
        # Extract all unique symbols from the CSV
        symbols = [str(sym).upper() for sym in df['symbol'].unique()]
        
        # Validate symbols concurrently
        stock_infos = await fetch_multiple_stock_infos(symbols)
        invalid_symbols = [sym for sym in symbols if sym not in stock_infos]
        
        if invalid_symbols:
            raise HTTPException(status_code=400, detail=f"Put correct stock name, stock name is invalid: {', '.join(invalid_symbols)}")
            
        for _, row in df.iterrows():
            sym = str(row['symbol']).upper()
            info = stock_infos[sym]
            resolved = info.get("resolved_symbol", sym)
            stock = Stock(
                portfolio_id=portfolio_id,
                symbol=resolved,
                name=info["name"],
                quantity=float(row['quantity']),
                avg_buy_price=float(row['avg_price'])
            )
            db.add(stock)
            
            # Save or update metadata
            metadata = StockMetadata(
                symbol=resolved,
                sector=info["sector"],
                industry=info["industry"]
            )
            await db.merge(metadata)
            
        await db.commit()
        return {"status": "imported", "count": len(df)}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

@router.get("/{portfolio_id}/export")
async def export_portfolio_csv(
    portfolio_id: str,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    portfolio = await get_portfolio_by_id(db, portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    data = []
    for stock in portfolio.stocks:
        data.append({
            "symbol": stock.symbol,
            "quantity": stock.quantity,
            "avg_price": stock.avg_buy_price,
            "currency": stock.currency
        })
        
    df = pd.DataFrame(data)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=portfolio_{portfolio_id}.csv"
    return response


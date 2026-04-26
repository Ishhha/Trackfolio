from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.portfolio import PortfolioResponse
from app.services.portfolio_service import calculate_portfolio_summary, get_portfolio_by_public_id

router = APIRouter()

@router.get("/portfolio/{public_id}", response_model=PortfolioResponse)
async def get_public_portfolio(
    public_id: str,
    db: AsyncSession = Depends(get_db)
):
    portfolio = await get_portfolio_by_public_id(db, public_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Public portfolio not found")
        
    summary = await calculate_portfolio_summary(portfolio, db)
    portfolio.summary = summary
    return portfolio

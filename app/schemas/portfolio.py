from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.stock import StockResponse

class PortfolioBase(BaseModel):
    name: str
    currency: Optional[str] = "USD"

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    currency: Optional[str] = None

class StockInsight(BaseModel):
    symbol: str
    name: Optional[str] = None
    pnl: float = 0.0
    pnl_percentage: float = 0.0

class PortfolioSummary(BaseModel):
    total_invested: float = 0.0
    current_value: float = 0.0
    total_pnl: float = 0.0
    pnl_percentage: float = 0.0
    sector_distribution: dict[str, float] = {}
    stock_allocation: dict[str, float] = {}
    top_gainer: Optional[StockInsight] = None
    top_loser: Optional[StockInsight] = None

class PortfolioResponse(PortfolioBase):
    id: str
    user_id: str
    created_at: datetime
    
    stocks: List[StockResponse] = []
    summary: Optional[PortfolioSummary] = None

    model_config = ConfigDict(from_attributes=True)

class PortfolioSnapshotResponse(BaseModel):
    id: str
    timestamp: datetime
    total_value: float
    invested_value: float
    pnl: float

    model_config = ConfigDict(from_attributes=True)

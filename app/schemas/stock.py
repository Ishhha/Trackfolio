from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class StockBase(BaseModel):
    symbol: str
    name: Optional[str] = None
    quantity: float
    avg_buy_price: float
    currency: Optional[str] = "USD"

class StockCreate(StockBase):
    portfolio_id: str

class StockUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_buy_price: Optional[float] = None

class StockResponse(StockBase):
    id: str
    portfolio_id: str
    created_at: datetime
    
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    invested_value: Optional[float] = None
    pnl: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

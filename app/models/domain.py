import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False) # Client-side UUID
    name = Column(String, nullable=False)
    currency = Column(String, default="USD")
    public_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4())[:8])
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stocks = relationship("Stock", back_populates="portfolio", cascade="all, delete")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete")

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("portfolios.id", ondelete="CASCADE"))
    symbol = Column(String, index=True, nullable=False)
    name = Column(String, nullable=True)
    quantity = Column(Float, nullable=False)
    avg_buy_price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    portfolio = relationship("Portfolio", back_populates="stocks")

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("portfolios.id", ondelete="CASCADE"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    total_value = Column(Float, nullable=False)
    invested_value = Column(Float, nullable=False)
    pnl = Column(Float, nullable=False)
    
    portfolio = relationship("Portfolio", back_populates="snapshots")

class StockMetadata(Base):
    __tablename__ = "stock_metadata"
    
    symbol = Column(String, primary_key=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)

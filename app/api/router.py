from fastapi import APIRouter
from app.api.endpoints import portfolios, stocks, public

api_router = APIRouter()
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(public.router, prefix="/public", tags=["public"])

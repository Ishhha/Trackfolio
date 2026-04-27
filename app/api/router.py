from fastapi import APIRouter
from app.api.endpoints import portfolios, stocks, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])

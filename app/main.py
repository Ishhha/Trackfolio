from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import engine, Base
from app.api.router import api_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.worker.tasks import fetch_active_stock_prices, take_portfolio_snapshots

# Initialize the scheduler
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Start the scheduler
    scheduler.add_job(fetch_active_stock_prices, 'interval', seconds=10, id='fetch_prices')
    scheduler.add_job(take_portfolio_snapshots, 'cron', hour=23, minute=59, id='take_snapshots')
    scheduler.start()
    
    yield
    
    # Cleanup on shutdown
    scheduler.shutdown()
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

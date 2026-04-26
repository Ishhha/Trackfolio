from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Portfolio Tracker"
    
    # SQLite Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./stock_tracker.db"

    class Config:
        env_file = ".env"

settings = Settings()

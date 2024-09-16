from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import POSTGRES_PASSWORD, POSTGRES_DB,POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER

# Database configuration
DATABASE_URL = f'postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

# Create an async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a sessionmaker factory
async_session = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Base model
Base = declarative_base()



# postgresql+asyncpg://postgres:admin123@localhost:5432/binit
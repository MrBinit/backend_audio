from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = 'postgresql+asyncpg://postgres:admin123@localhost:5432/binit'

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


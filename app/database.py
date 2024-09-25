from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER
from sqlalchemy import MetaData, text
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncAttrs

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
Base = declarative_base(cls=AsyncAttrs)

# Function to create tables in the database
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Define a function to fetch data from PostgreSQL
async def fetch_data(table_name):
    try:
        # Open a new session
        async with async_session() as session:
            # Construct a dynamic SQL query
            query = text(f'SELECT * FROM {table_name}')
            result = await session.execute(query)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        return df
    except SQLAlchemyError as e:
        print(f"Error fetching data from PostgreSQL: {e}")
        return None

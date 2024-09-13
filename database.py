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



# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from models import Base
# from app.core.config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT


# DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# engine = create_engine(DATABASE_URL)


# def create_tables():
#     Base.metadata.create_all(bind=engine)


# SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


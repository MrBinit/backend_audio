import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from datasets import Dataset
from sqlalchemy import text

# Database URL
DATABASE_URL = "postgresql+asyncpg://postgres:admin123@localhost:5432/binit"

# Define a function to fetch data from PostgreSQL
async def fetch_data(table_name):
    # Create an async engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    # Create a sessionmaker, binding it to the engine
    async_session = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    
    # Open a new session
    async with async_session() as session:
        # Construct a dynamic SQL query
        query = text(f'SELECT * FROM {table_name}')
        result = await session.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

    # Close the engine
    await engine.dispose()
    
    return df

# Main function to execute the data fetching and uploading
async def main(table_name):
    # Fetch data from the PostgreSQL database
    df = await fetch_data(table_name)
    
    # Convert the DataFrame to a Hugging Face dataset
    hf_dataset = Dataset.from_pandas(df)
    
    # Upload the dataset to Hugging Face (Replace 'your_dataset_name' and 'your_hf_username' with appropriate values)
    hf_dataset.push_to_hub("MrBinit/srijan")

# Get table name from the user
table_name = input("Enter the table name: ")

# Run the main function with the table name
import asyncio
asyncio.run(main(table_name))

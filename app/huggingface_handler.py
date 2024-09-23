from datasets import load_dataset, Dataset
from app.database import async_session, create_tables, Base
from sqlalchemy import Column, Integer, String
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
from app.core.config import HUGGINGFACE_TOKEN
from huggingface_hub import HfApi

HF_TOKEN = HUGGINGFACE_TOKEN

# Function to determine SQLAlchemy data types
def determine_column_types(sample):
    column_types = {}
    for key, value in sample.items():
        if isinstance(value, int):
            column_types[key] = Integer
        elif isinstance(value, str):
            column_types[key] = String
    return column_types

# Function to dynamically create a table class
def create_table_class(table_name, columns):
    # Create a dynamic table class
    class DynamicTable(Base):
        __tablename__ = table_name
        __table_args__ = {'extend_existing': True}
        id = Column(Integer, primary_key=True, autoincrement=True)
        for name, dtype in columns.items():
            locals()[name] = Column(dtype)
    
    return DynamicTable

async def insert_data_to_postgres(dataset_name: str, table_name: str):
    try:
        # Load the dataset from Hugging Face
        dataset = load_dataset(dataset_name, split='train')
        
        # Extract column types from the first sample
        sample = dataset[0]
        column_types = determine_column_types(sample)
        
        # Create the table class dynamically
        TableClass = create_table_class(table_name, column_types)
        
        # Create the table if it doesn't exist
        await create_tables()
        
        # Insert data into the table
        async with async_session() as session:
            for item in dataset:
                record = TableClass(**item)
                session.add(record)
            
            await session.commit()
        return f"Dataset '{dataset_name}' successfully loaded into table '{table_name}'"
    
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

# Function to convert pandas DataFrame to Hugging Face dataset and upload to Hugging Face hub
def upload_to_huggingface(df):
    # Convert the DataFrame to a Hugging Face dataset
    hf_dataset = Dataset.from_pandas(df)
    
    # Upload the dataset to Hugging Face
    hf_dataset.push_to_hub("MrBinit/srijan")

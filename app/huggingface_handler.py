from datasets import load_dataset
from sqlalchemy import Column, Integer, String
from app.database import async_session, create_tables, Base, engine
from datasets import load_dataset, Dataset, DatasetDict
from sqlalchemy import Column, Integer, String
from sqlalchemy import select, MetaData
import pandas as pd
from app.core.config import HUGGINGFACE_TOKEN


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

#now function to fetch data from postgresSQL
async def fetch_data_from_postgres(table_name):
    """Fetch data from PostgreSQL table and return as a DataFrame."""
    async with async_session() as session:
        # Use reflection to dynamically get the table
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table = metadata.tables.get(table_name)

        if table is None:
            raise Exception(f"Table {table_name} does not exist.")

        # Query the table
        result = await session.execute(select(table))
        rows = result.fetchall()
        
        # Convert the result to a pandas DataFrame
        df = pd.DataFrame([dict(row) for row in rows])
    return df

# Function to upload data to Hugging Face
def upload_data_to_huggingface(df, hf_dataset_name):
    # Convert the DataFrame to a Hugging Face dataset
    hf_dataset = Dataset.from_pandas(df)
    
    # Upload the dataset to Hugging Face
    hf_dataset.push_to_hub(hf_dataset_name, token=HUGGINGFACE_TOKEN)
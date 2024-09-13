from sqlalchemy import Column, String, MetaData, Table

# Metadata instance
metadata = MetaData()

# Define the database table
videos_table = Table(
    'videos',
    metadata,
    Column('uuid', String, primary_key=True),
    Column('video_url', String),
    Column('video_name', String),
)

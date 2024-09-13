# # models.py
# from sqlalchemy import Column, String, MetaData, Table

# # Metadata instance
# metadata = MetaData()

# # Define the database table
# videos_table = Table(
#     'videos',
#     metadata,
#     Column('uuid', String, primary_key=True),
#     Column('video_url', String),
#     Column('video_name', String),
#     Column('file_path', String)
# )

import uuid
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'
    UUID = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    video_url = Column(String(200), unique=True, nullable=False)
    video_name = Column(String(200), nullable=True)
    chunk_output_directory = Column(String(200), nullable=False)


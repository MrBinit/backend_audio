import uuid
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Video(Base):
    __tablename__ = 'chunk_videos'
    UUID = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    video_url = Column(String(200), unique=True, nullable=False)
    video_name = Column(String(200), nullable=True)
    chunk_output_directory = Column(String(200), nullable=False)

class Download_videos(Base):
    __tablename__ = "download_videos"
    uuid = Column(String, primary_key=True, index=True)
    video_name = Column(String, index=True)
    video_url = Column(String, index=True)
    video_location = Column(String)

# models.py
import uuid  # Make sure this import is here
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Download_videos(Base):
    __tablename__ = "download_videos"
    uuid = Column(String, primary_key=True, index=True)
    video_name = Column(String, index=True)
    video_url = Column(String, index=True)
    location = Column(String)

    # Establish relationship with AudioChunks
    chunks = relationship("AudioChunks", backref="video")

class AudioChunks(Base):
    __tablename__ = "audio_chunks"
    chunk_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # Ensure uuid is properly used here
    video_uuid = Column(String, ForeignKey('download_videos.uuid'), nullable=False)
    file_path = Column(String, nullable=False)

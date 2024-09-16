import uuid
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.database import Base

class Download_videos(Base):
    __tablename__ = "download_videos"
    id = Column(Integer, primary_key=True, autoincrement=True)  # New auto-incrementing id column
    uuid = Column(String, unique=True, index=True)  # Keep the UUID for reference
    video_name = Column(String, index=True)
    video_url = Column(String, index=True)
    location = Column(String)

    # Establish relationship with AudioChunks
    chunks = relationship("AudioChunks", backref="video")

class AudioChunks(Base):
    __tablename__ = "audio_chunks"
    chunk_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # UUID for chunks
    video_id = Column(Integer, ForeignKey('download_videos.id'), nullable=False)  # Foreign key to id
    video_uuid = Column(String, nullable=False)  # Keep the UUID for reference
    file_path = Column(String, nullable=False)

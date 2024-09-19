# models.py
import uuid
from sqlalchemy import Column, String, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Download_videos(Base):
    __tablename__ = "download_videos"
    id = Column(Integer, primary_key=True, autoincrement=True) 
    uuid = Column(String, unique=True, index=True) 
    video_name = Column(String, index=True)
    video_url = Column(String, index=True)
    location = Column(String, unique = True)

    # Establish relationship with AudioChunks
    chunks = relationship("AudioChunks", backref="video")

class AudioChunks(Base):
    __tablename__ = "audio_chunks"
    chunk_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  
    video_id = Column(Integer, ForeignKey('download_videos.id'), nullable=False) 
    video_uuid = Column(String, nullable=False) 
    file_path = Column(String, nullable=False)
    transcribe = Column(Text, nullable=True)  



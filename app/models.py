import uuid
from sqlalchemy import Column, String, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Download_videos(Base):
    __tablename__ = "download_videos"
    id = Column(Integer, primary_key=True, autoincrement=True) 
    uuid = Column(String, unique=True, index=True) 
    video_name = Column(String, index=True)
    video_url = Column(String, index=True, nullable=True)  # Optional URL field
    location = Column(String, unique=True, nullable=False)  # Path to local file

    # Establish relationship with AudioChunks
    chunks = relationship("AudioChunks", backref="video")

class AudioChunks(Base):
    __tablename__ = "audio_chunks"
    chunk_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  
    video_id = Column(Integer, ForeignKey('download_videos.id'), nullable=False)  # Reference to the video
    video_uuid = Column(String, nullable=False)  # UUID of the video
    file_path = Column(String, nullable=False)  # File path of the audio chunk
    transcribe = Column(Text, nullable=True)  # Optional transcription field

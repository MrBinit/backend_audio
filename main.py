from fastapi import FastAPI, HTTPException, Query
import yt_dlp
import uuid
import os
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from models import Video, Base
from database import engine, async_session

app = FastAPI()

# Ensure the table is created on startup
@app.on_event("startup")
async def startup_event():
    # Use sync engine for schema creation
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def sanitize_filename(s):
    # Replace invalid characters with underscores
    return re.sub(r'[\\/*?:"<>|]', "_", s)

# Endpoint to download audio and save data to the database
@app.get("/download_audio")
async def download_audio(youtube_url: str = Query(..., description="The YouTube video URL")):
    output_directory = '/Users/mrbinit/Desktop/untitled folder/datasets'

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Set up yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_directory}/%(title)s.mp3',  # Force output to .mp3
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    # Download the audio
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading audio from: {youtube_url}")
            info_dict = ydl.extract_info(youtube_url, download=True)
            video_title = info_dict.get('title', 'unknown')
            print("Download completed!")
    except Exception as e:
        print(f"Failed to download from {youtube_url}. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download. Error: {e}")

    # Sanitize the video title to create a safe file name
    video_title_sanitized = sanitize_filename(video_title)
    file_name = f"{video_title_sanitized}.mp3"
    file_path = os.path.join(output_directory, file_name)

    # Generate a UUID for the video
    video_uuid = str(uuid.uuid4())

    # Insert data into the database
    async with async_session() as session:
        async with session.begin():
            new_video = Video(
                UUID=video_uuid,
                video_url=youtube_url,
                video_name=video_title,
                file_path=file_path
            )
            session.add(new_video)
        await session.commit()

    return {
        "uuid": video_uuid,
        "video_url": youtube_url,
        "video_name": video_title,
        "file_path": file_path
    }

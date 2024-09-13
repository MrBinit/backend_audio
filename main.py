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
from pydub import AudioSegment
from pydub.silence import split_on_silence
from audio_chunker import process_single_audio  

app = FastAPI()

# Ensure the table is created on startup
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def sanitize_filename(s):
    return re.sub(r'[\\/*?:"<>|]', "_", s)


@app.get("/download_audio")
async def download_audio(youtube_url: str = Query(..., description="The YouTube video URL")):
    output_directory = '/Users/mrbinit/Desktop/untitled folder/datasets'
    chunk_output_directory = '/Users/mrbinit/Desktop/untitled folder/output_chunk'
    csv_file_path = '/Users/mrbinit/Desktop/untitled folder/output_chunk/file_uuids.csv'

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Set up yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_directory}/%(title)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading audio from: {youtube_url}")
            info_dict = ydl.extract_info(youtube_url, download=True)
            video_title = info_dict.get('title', 'unknown')
            print("Download completed!")
    except Exception as e:
        print(f"Failed to download from {youtube_url}. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download. Error: {e}")

    video_title_sanitized = sanitize_filename(video_title)
    file_name = f"{video_title_sanitized}.mp3"
    file_path = os.path.join(output_directory, file_name)

    # Chunk the downloaded audio
    process_single_audio(file_path, chunk_output_directory, csv_file_path)

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
        "file_path": file_path,
        "chunk_output_directory": chunk_output_directory  # Return chunk directory
    }
from fastapi import FastAPI, HTTPException, Query
import yt_dlp
import uuid
import os

from database import engine, async_session
from models import metadata, videos_table

app = FastAPI()

# Ensure the table is created on startup
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

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
        'outtmpl': f'{output_directory}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    # Download the audio
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print(f"Downloading audio from: {youtube_url}")
            info_dict = ydl.extract_info(youtube_url, download=True)
            video_title = info_dict.get('title', 'unknown')
            print("Download completed!")
        except Exception as e:
            print(f"Failed to download from {youtube_url}. Error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to download. Error: {e}")

    # Generate a UUID for the video
    video_uuid = str(uuid.uuid4())

    # Insert data into the database
    async with async_session() as session:
        async with session.begin():
            insert_stmt = videos_table.insert().values(
                uuid=video_uuid,
                video_url=youtube_url,
                video_name=video_title,
            )
            await session.execute(insert_stmt)
            await session.commit()

    return {
        "uuid": video_uuid,
        "video_url": youtube_url,
        "video_name": video_title
    }

from fastapi import FastAPI, HTTPException, Query
import yt_dlp
import uuid
import os
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Download_videos, Base
from app.database import engine, async_session
from app.topics import topics_to_download

app = FastAPI()

# Ensure the table is created on startup
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def sanitize_filename(s):
    return re.sub(r'[\\/*?:"<>|]', "_", s)

@app.get("/download_all_audios")
async def download_all_audios():
    results = []
    
    for topic in topics_to_download:
        downloaded_video = await download_audio(query=topic, is_url=False)
        results.append(downloaded_video)

    return {"audios_downloaded": results}

@app.get("/download_audio_by_url")
async def download_audio_by_url(youtube_url: str = Query(..., description="The YouTube video URL to download")):
    result = await download_audio(query=youtube_url, is_url=True)
    return result

async def download_audio(query: str, is_url: bool):
    output_directory = '/Users/mrbinit/Desktop/untitled folder/datasets'

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Set options for yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_directory}/%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if is_url:
                print(f"Downloading audio from URL: {query}")
                # Extract and download the video directly from the URL
                info_dict = ydl.extract_info(query, download=False)  # Don't download yet to get the info
                video_url = info_dict.get('webpage_url')
            else:
                print(f"Searching for the first audio for topic: {query}")
                # Use ytsearch to find the first video for the topic without downloading
                search_results = ydl.extract_info(f"ytsearch:{query}", download=False)
                if 'entries' in search_results and len(search_results['entries']) > 0:
                    first_result = search_results['entries'][0]
                    video_url = first_result.get('webpage_url')
                    print(f"Found video URL: {video_url}")
                else:
                    raise HTTPException(status_code=404, detail="No video found for the topic.")

            # Check for duplicate in the database
            async with async_session() as session:
                async with session.begin():
                    stmt = select(Download_videos).where(Download_videos.video_url == video_url)
                    result = await session.execute(stmt)
                    existing_video = result.scalars().first()
                    if existing_video:
                        raise HTTPException(status_code=400, detail="Audio already exists in the database.")

            # Get video title for file name
            video_title = info_dict.get('title', 'unknown')
            video_title_sanitized = sanitize_filename(video_title)
            file_name = f"{video_title_sanitized}.mp3"
            file_path = os.path.join(output_directory, file_name)

            # Check if the file already exists in the directory
            if os.path.exists(file_path):
                raise HTTPException(status_code=400, detail="Audio file already exists in the directory.")

            # Now proceed to download the video since it's not a duplicate
            info_dict = ydl.extract_info(video_url, download=True)

            # Display the video is downloaded 
            print(f"Download completed for: {video_title}")

            # Generate a UUID for the video
            video_uuid = str(uuid.uuid4())

            # Save video info to the database
            async with async_session() as session:
                async with session.begin():
                    new_video = Download_videos(
                        uuid=video_uuid,
                        video_url=video_url,
                        video_name=video_title,
                        location=file_path  
                    )
                    session.add(new_video)
                await session.commit()

            # Display message after pushing to the database
            print(f"Video information pushed to the database for: {video_title}")
            
            return {
                "uuid": video_uuid,
                "video_name": video_title,
                "video_url": video_url,
                "location": file_path
            }
    except Exception as e:
        print(f"Failed to download audio for query {query}. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download. Error: {e}")

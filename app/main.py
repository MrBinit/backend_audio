from fastapi import FastAPI, HTTPException
import yt_dlp
import uuid
import os
import re
from sqlalchemy.ext.asyncio import AsyncSession
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
        downloaded_video = await download_audio_by_topic(topic)
        results.append(downloaded_video)

    return {"audios_downloaded": results}

async def download_audio_by_topic(topic: str):
    output_directory = '/Users/mrbinit/Desktop/untitled folder/datasets'

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    search_opts = {
        'default_search': 'ytsearch1',  # Search for the first 1 video
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_directory}/%(title)s.%(ext)s',
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            print(f"Searching and downloading audio for topic: {topic}")
            info_dicts = ydl.extract_info(f"ytsearch1:{topic}", download=True)

            # Since we are only downloading one video, we can directly access the first entry
            info_dict = info_dicts['entries'][0]
            video_title = info_dict.get('title', 'unknown')
            video_url = info_dict.get('webpage_url', None)
            if not video_url:
                raise HTTPException(status_code=404, detail="Video URL not found")

            video_title_sanitized = sanitize_filename(video_title)
            file_name = f"{video_title_sanitized}.mp3"
            file_path = os.path.join(output_directory, file_name)

            # display the video is downloaded 
            print(f"Download completed for: {video_title}")

            # Generate a UUID for the video
            video_uuid = str(uuid.uuid4())

            # Save video info to the database
            async with async_session() as session:
                async with session.begin():
                    new_video = Download_videos(
                        uuid=video_uuid,
                        url=video_url,
                        name=video_title,
                        location=file_path  # Save the location of the downloaded audio
                    )
                    session.add(new_video)
                await session.commit()
            # Display message after pushing to the database
            print(f"Video information pushed to the database for: {video_title}")
            
            return {
                "uuid": video_uuid,
                "video_url": video_url,
                "video_name": video_title,
                "location": file_path
            }
                
    except Exception as e:
        print(f"Failed to download audio for topic {topic}. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download. Error: {e}")

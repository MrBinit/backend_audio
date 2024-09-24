import yt_dlp
import uuid
import os
import re
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Download_videos
from app.core.config import ORIGINAL_DIRECTORY
from app.database import async_session

def sanitize_filename(s):
    return re.sub(r'[\\/*?:"<>|]', "_", s)

async def download_audio(query: str, is_url: bool, use_sample_rate_16000: bool = False):
    output_directory = ORIGINAL_DIRECTORY

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Set options for yt-dlp to save audio in WAV format
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'outtmpl': f'{output_directory}/%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True
    }

    # If the user opts for a sample rate of 16000, add corresponding FFmpeg arguments
    if use_sample_rate_16000:
        ydl_opts['postprocessor_args'] = ['-ar', '16000', '-ac', '1']  # Set sample rate to 16000 Hz and convert to mono

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if is_url:
                print(f"Downloading audio from URL: {query}")
                # Extract and download the video directly from the URL
                info_dict = ydl.extract_info(query, download=False)  # Don't download yet to get the info
                video_url = info_dict.get('webpage_url')
                video_title = info_dict.get('title', 'unknown')  # Extract title here
            else:
                print(f"Searching for the first audio for topic: {query}")
                # Use ytsearch to find the first video for the topic without downloading
                search_results = ydl.extract_info(f"ytsearch:{query}", download=False)
                if 'entries' in search_results and len(search_results['entries']) > 0:
                    first_result = search_results['entries'][0]
                    video_url = first_result.get('webpage_url')
                    video_title = first_result.get('title', 'unknown')  # Extract title here
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

            # Sanitize the video title and prepare the file name
            video_title_sanitized = sanitize_filename(video_title)
            file_name = f"{video_title_sanitized}.wav"
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
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

def get_next_video_name(directory):
    # Find all files in the directory that match the pattern 'videoX.wav'
    existing_files = [f for f in os.listdir(directory) if f.startswith("video") and f.endswith(".wav")]
    
    # Extract numbers from file names and find the next available number
    video_numbers = [int(re.findall(r'\d+', f)[0]) for f in existing_files if re.findall(r'\d+', f)]
    
    next_video_number = max(video_numbers) + 1 if video_numbers else 1
    return f"video{next_video_number}.wav"

async def download_audio(query: str, is_url: bool, use_sample_rate_16000: bool = False):
    output_directory = ORIGINAL_DIRECTORY

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Generate the next available video name (video1, video2, etc.)
    file_name = get_next_video_name(output_directory)
    file_path = os.path.join(output_directory, file_name)

    # Set options for yt-dlp to save audio in WAV format and directly name the file as 'videoX.wav'
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'outtmpl': f'{file_path}',  # Directly set the output template to the desired videoX.wav name
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
                video_title = info_dict.get('title', 'unknown')  # Extract the original title
            else:
                print(f"Searching for the first audio for topic: {query}")
                # Use ytsearch to find the first video for the topic without downloading
                search_results = ydl.extract_info(f"ytsearch:{query}", download=False)
                if 'entries' in search_results and len(search_results['entries']) > 0:
                    first_result = search_results['entries'][0]
                    video_url = first_result.get('webpage_url')
                    video_title = first_result.get('title', 'unknown')  # Extract the original title
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

            # Now proceed to download the video since it's not a duplicate
            info_dict = ydl.extract_info(video_url, download=True)

            # Extract metadata 
            audio_length = info_dict.get('duration')
            audio_size = info_dict.get('filesize')
            audio_codec = info_dict.get('acodec')
            audio_sample_rate = info_dict.get('asr')

            # Prepare meta dictionary
            meta_data = {
                'audio_length(sec)': audio_length,
                "audio_size(bytes)": audio_size,
                "audio_codec": audio_codec,
                "sampling_frequency(Hz)": audio_sample_rate
            }

            # Display the video download is completed
            print(f"Download completed and saved as: {file_name}")

            # Generate a UUID for the video
            video_uuid = str(uuid.uuid4())

            # Save video info to the database with the original name and file location
            async with async_session() as session:
                async with session.begin():
                    new_video = Download_videos(
                        uuid=video_uuid,
                        video_url=video_url,
                        video_name=video_title,  # Save the original name in the database
                        location=file_path,       # Save the file path with the new name (videoX.wav)
                        meta_data=meta_data,
                        chunk_status="False"
                    )
                    session.add(new_video)
                await session.commit()

            # Display message after pushing to the database
            print(f"Video information pushed to the database for: {video_title}")
            
            return {
                "uuid": video_uuid,
                "video_name": video_title,  # Return the original title as the video name
                "video_url": video_url,
                "location": file_path        # File location where the renamed file is stored
            }
    except Exception as e:
        print(f"Failed to download audio for query {query}. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download. Error: {e}")

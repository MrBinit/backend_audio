import os
import uuid
from pydub import AudioSegment
from pydub.silence import split_on_silence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import async_session
from app.models import AudioChunks, Download_videos

def dynamic_silence_thresh(audio_segment, target_dbfs=-40):
    average_dbfs = audio_segment.dBFS
    return max(target_dbfs, average_dbfs - 10)

def chunk_audio(input_file, 
                min_duration=6000,  # Minimum chunk duration in milliseconds (6 seconds)
                max_duration=18000,  # Maximum chunk duration in milliseconds (18 seconds)
                target_dbfs=-40,
                keep_silence=500, 
                overlap=0):
    try:
        # Load the audio file
        audio = AudioSegment.from_file(input_file)
    except Exception as e:
        print(f"Error loading audio file: {e}")
        return []

    # Determine the silence threshold dynamically
    silence_thresh = dynamic_silence_thresh(audio, target_dbfs)

    # Split audio into chunks based on silence
    chunks = split_on_silence(audio, 
                              min_silence_len=500, 
                              silence_thresh=silence_thresh, 
                              keep_silence=keep_silence)

    output_chunks = []
    
    for chunk in chunks:
        if len(chunk) < min_duration:
            # Skip chunks that are too short
            continue
        
        if len(chunk) > max_duration:
            # Split this chunk further if it's longer than max_duration
            start = 0
            while start < len(chunk):
                end = start + max_duration
                sub_chunk = chunk[start:end]
                if len(sub_chunk) >= min_duration:
                    output_chunks.append(sub_chunk)
                start += max_duration - overlap
        else:
            output_chunks.append(chunk)

    return output_chunks

async def check_if_processed(filename):
    """Check if the audio file has already been processed."""
    async with async_session() as session:
        async with session.begin():
            stmt = select(Download_videos).where(Download_videos.video_name == filename)
            result = await session.execute(stmt)
            return result.scalars().first()

async def save_chunk_to_db(video_id, video_uuid, file_path):
    async with async_session() as session:
        async with session.begin():
            new_chunk = AudioChunks(
                video_id=video_id,  # Save using video_id
                video_uuid=video_uuid,  # Save using video_uuid
                file_path=file_path
            )
            session.add(new_chunk)
        await session.commit()

async def save_video_to_db(file_uuid, filename):
    async with async_session() as session:
        async with session.begin():
            new_video = Download_videos(
                uuid=file_uuid,
                video_name=filename,
                video_url='',  # If URL is not available, set it accordingly
                location=''  # Set the location if needed
            )
            session.add(new_video)
        await session.flush()  # This will allow us to access new_video.id without committing
            # Return the new video's id
        return new_video.id

async def process_single_audio(input_file, output_base_directory):
    filename = os.path.basename(input_file)

    # Check if this audio file has already been processed
    processed_video = await check_if_processed(filename)
    if processed_video:
        print(f"Skipping {filename} as it has already been processed.")
        return

    print(f"Processing file: {filename}")

    # Generate UUID for the audio file
    file_uuid = str(uuid.uuid4())

    # Save the video to the database and get the video ID
    video_id = await save_video_to_db(file_uuid, filename)

    # Create a folder named after the UUID
    uuid_directory = os.path.join(output_base_directory, file_uuid)
    os.makedirs(uuid_directory, exist_ok=True)

    # Chunk the audio
    chunks = chunk_audio(input_file, min_duration=6000, max_duration=18000, target_dbfs=-40, keep_silence=500, overlap=1000)

    # Save chunks in the UUID-named folder and to the database
    for i, chunk in enumerate(chunks):
        chunk_filename = os.path.join(uuid_directory, f"chunk_{i+1}.mp3")
        chunk.export(chunk_filename, format="mp3")
        print(f"Saved {chunk_filename}, duration: {len(chunk) / 1000:.2f} seconds")

        # Save chunk info to the database
        await save_chunk_to_db(video_id, file_uuid, chunk_filename)  # Use video_id and video_uuid

    print(f"All chunks for {filename} have been saved in the folder: {uuid_directory}")

async def process_all_audios(input_directory, output_base_directory):
    results = []
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
                input_file = os.path.join(root, file)
                await process_single_audio(input_file, output_base_directory)
                results.append(file)
    return results

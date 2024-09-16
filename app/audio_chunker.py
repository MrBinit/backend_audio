# audio_chunker.py
import os
import uuid
import csv
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

def read_existing_uuids(csv_file_path):
    existing_uuids = set()
    if os.path.isfile(csv_file_path):
        with open(csv_file_path, mode='r', newline='') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader, None)  # Skip header
            for row in csv_reader:
                if len(row) >= 2:
                    existing_uuids.add(row[1])
    return existing_uuids

def save_uuid_to_csv(file_path, filename, file_uuid):
    file_exists = os.path.isfile(file_path)
    with open(file_path, mode='a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        if not file_exists:
            csv_writer.writerow(['Filename', 'UUID'])
        csv_writer.writerow([filename, file_uuid])

async def save_chunk_to_db(video_uuid, file_path):
    async with async_session() as session:
        async with session.begin():
            new_chunk = AudioChunks(
                video_uuid=video_uuid,
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
        await session.commit()

async def process_single_audio(input_file, output_base_directory, csv_file_path):
    print("Processing file:", input_file)
    existing_uuids = read_existing_uuids(csv_file_path)

    # Generate UUID for the audio file
    file_uuid = str(uuid.uuid4())
    filename = os.path.basename(input_file)

    # Skip if the file has been processed before
    if file_uuid in existing_uuids:
        print(f"Skipping {filename} as it has already been processed with UUID {file_uuid}.")
        return

    # Save the video to the database
    await save_video_to_db(file_uuid, filename)

    # Create a folder named after the UUID
    uuid_directory = os.path.join(output_base_directory, file_uuid)
    os.makedirs(uuid_directory, exist_ok=True)

    # Save UUID and filename to the CSV
    save_uuid_to_csv(csv_file_path, filename, file_uuid)

    # Chunk the audio
    chunks = chunk_audio(input_file, min_duration=6000, max_duration=18000, target_dbfs=-40, keep_silence=500, overlap=1000)

    # Save chunks in the UUID-named folder and to the database
    for i, chunk in enumerate(chunks):
        chunk_filename = os.path.join(uuid_directory, f"chunk_{i+1}.mp3")
        chunk.export(chunk_filename, format="mp3")
        print(f"Saved {chunk_filename}, duration: {len(chunk) / 1000:.2f} seconds")

        # Save chunk info to the database
        await save_chunk_to_db(file_uuid, chunk_filename)  # Ensure this is awaited

    print(f"All chunks for {filename} have been saved in the folder: {uuid_directory}")
    print(f"File UUID has been saved in: {csv_file_path}")

async def process_all_audios(input_directory, output_base_directory, csv_file_path):
    results = []
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
                input_file = os.path.join(root, file)
                await process_single_audio(input_file, output_base_directory, csv_file_path)
                results.append(file)
    return results

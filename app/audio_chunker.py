import os
import uuid
from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_nonsilent
from sqlalchemy.exc import SQLAlchemyError
from app.models import AudioChunks
from app.database import async_session
from app.models import Download_videos

async def save_chunk_to_db(video_id, video_uuid, file_path):
    try:
        async with async_session() as session:
            async with session.begin():
                new_chunk = AudioChunks(
                    video_id=video_id,
                    video_uuid=video_uuid,
                    file_path=file_path
                )
                session.add(new_chunk)
            await session.commit()
    except SQLAlchemyError as e:
        print(f"Error saving chunk to the database: {e}")
        raise  # Reraise the exception for further handling

async def save_video_to_db(file_uuid, filename, file_location):
    try:
        async with async_session() as session:
            async with session.begin():
                new_video = Download_videos(
                    uuid=file_uuid,
                    video_name=filename,
                    video_url='',
                    location=os.path.normpath(file_location)
                )
                session.add(new_video)
                await session.flush()
                return new_video.id  # Return the new video's id
    except SQLAlchemyError as e:
        print(f"Error saving video to the database: {e}")
        raise  # Reraise for external handling

def split_audio_with_silence(audio_file, output_dir):
    """Split audio file based on silence and export chunks."""
    try:
        audio = AudioSegment.from_wav(audio_file)
        silence_duration = 1000  # 1 second
        max_chunk_size = 18 * 1000  # 18 seconds
        min_chunk_size = 5 * 1000  # 5 seconds

        nonsilent_ranges = detect_nonsilent(
            audio, min_silence_len=silence_duration, silence_thresh=-40, seek_step=100
        )

        final_chunks = []
        if not nonsilent_ranges:
            print("No nonsilent ranges detected.")
            return []

        for start, end in nonsilent_ranges:
            chunk = audio[start:end]
            if min_chunk_size <= len(chunk) <= max_chunk_size:
                final_chunks.append(chunk)
            elif len(chunk) > max_chunk_size:
                split_chunks = split_on_silence(chunk, min_silence_len=silence_duration, silence_thresh=-40, keep_silence=500)
                for sub_chunk in split_chunks:
                    if min_chunk_size <= len(sub_chunk) <= max_chunk_size:
                        final_chunks.append(sub_chunk)

        if not final_chunks:
            print("No chunks created after processing.")
            return []

        output_paths = []
        for i, final_chunk in enumerate(final_chunks):
            output_path = os.path.join(output_dir, f"chunk_{i+1}.wav")
            final_chunk.export(output_path, format="wav")
            output_paths.append(output_path)

        return output_paths
    except Exception as e:
        print(f"Error splitting audio: {e}")
        return []

async def process_single_audio(input_file, output_base_directory):
    filename = os.path.basename(input_file)
    print(f"Processing file: {filename}")
    file_uuid = str(uuid.uuid4())
    uuid_directory = os.path.join(output_base_directory, file_uuid)
    os.makedirs(uuid_directory, exist_ok=True)

    chunk_filenames = split_audio_with_silence(input_file, uuid_directory)

    if chunk_filenames:
        # Save video details to the database
        video_id = await save_video_to_db(file_uuid, filename, uuid_directory)
        
        # Save each chunk to the database
        for chunk_path in chunk_filenames:
            await save_chunk_to_db(video_id, file_uuid, chunk_path)
        print(f"All chunks for {filename} have been saved in the folder: {uuid_directory}")
    else:
        print(f"No chunks were created for {filename}")

async def process_all_audios(input_directory, output_base_directory):
    results = []
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.lower().endswith(('.wav', '.flac', '.ogg')):
                input_file = os.path.join(root, file)
                await process_single_audio(input_file, output_base_directory)
                results.append(file)
    return results

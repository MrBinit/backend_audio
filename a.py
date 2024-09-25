from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_nonsilent
import os
import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models import AudioChunks, Download_videos

def split_audio_with_silence(audio_file, output_dir):
    """Split audio file based on silence and export chunks."""
    try:
        audio = AudioSegment.from_wav(audio_file)
        
        silence_duration = 1000  # Initial silence duration (1 second)
        max_chunk_size = 18 * 1000  # Max chunk size (18 seconds)
        min_chunk_size = 5 * 1000  # Min chunk size (5 seconds)
        
        nonsilent_ranges = detect_nonsilent(audio, min_silence_len=silence_duration, silence_thresh=-40, seek_step=100)
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
    
async def check_if_processed(file_location):
    """Check if the audio file has already been processed using its location."""
    # Normalize the file location path
    normalized_location = os.path.normpath(file_location)
    async with async_session() as session:
        async with session.begin():
            stmt = select(Download_videos).where(Download_videos.location == normalized_location)
            result = await session.execute(stmt)
            video = result.scalars().first()
            if video and video.chunks:
                return video
            return None
def process_single_audio(input_file, output_base_directory):
    """Process a single audio file: split into chunks and save in UUID folders."""
    try:
        filename = os.path.basename(input_file)
        print(f"Processing file: {filename}")

        # Generate a unique UUID for this audio file
        unique_id = str(uuid.uuid4())

        # Create a directory for this UUID
        output_dir = os.path.join(output_base_directory, unique_id)
        os.makedirs(output_dir, exist_ok=True)

        # Split the audio and save chunks in the UUID directory
        chunks = split_audio_with_silence(input_file, output_dir)
        if not chunks:
            print(f"No chunks found for {filename}.")
            return

        # Log each chunk path
        for chunk_path in chunks:
            print(f"Saved {chunk_path}")

        print(f"All chunks for {filename} have been saved in the folder: {output_dir}")
    except Exception as e:
        print(f"Error processing single audio: {e}")


def process_all_audios(input_directory, output_base_directory):
    """Process all audio files in the input directory, creating UUIDs based on audio files."""
    try:
        for filename in os.listdir(input_directory):
            if filename.lower().endswith(('.wav', '.flac', '.ogg')):  # Only process WAV, FLAC, OGG
                input_file = os.path.join(input_directory, filename)

                # Generate a unique UUID based on the audio file's path
                unique_id = str(uuid.uuid5(uuid.NAMESPACE_URL, input_file))

                # Create a directory for this UUID
                output_dir = os.path.join(output_base_directory, unique_id)
                os.makedirs(output_dir, exist_ok=True)

                # Process this single audio file
                process_single_audio(input_file, output_dir) 
    except Exception as e:
        print(f"Error processing all audios: {e}")
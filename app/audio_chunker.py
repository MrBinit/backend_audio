import os
from pydub import AudioSegment
from pydub.silence import detect_nonsilent, split_on_silence
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from app.models import Download_videos, AudioChunks
from app.database import async_session

# Fetch video from database using UUID and return its location
async def audio_chunker(uuid, output_dir):
    try:
        async with async_session() as session:
            async with session.begin():
                stmt = select(Download_videos).where(Download_videos.uuid == uuid)
                result = await session.execute(stmt)
                video = result.scalars().first()
                
                if video:
                    #Create output directory using the UUID of the video
                    output_dir = os.path.join(output_dir, uuid)

                    #ensure the output directory exist
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    print(f"Saving chunks in directory: {output_dir}")

                    # # If the video exists, display the file location and process audio
                    # print(f"File location for UUID {uuid}: {video.location}")
                    audio_chunks = split_audio_with_silence(video.location, output_dir)

                    # Save each chunk to the database
                    if audio_chunks:
                        await save_chunks_to_db(uuid, video.id, audio_chunks)
                    
                    # Update chunk_status in the Download_videos table
                    video.chunk_status = "True"
                    await session.commit()

                    return {"location": video.location, "chunks": audio_chunks}
                else:
                    print(f"No video found with UUID {uuid}")
                    return {"error": "No video found with this UUID"}
    except SQLAlchemyError as e:
        print(f"Error querying the database: {e}")
        raise

# Split audio based on silence and export chunks
def split_audio_with_silence(audio_file, output_dir):
    """Split audio file based on silence and export chunks."""
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Load audio file
        audio = AudioSegment.from_wav(audio_file)

        # Parameters for silence detection
        silence_duration = 1000  # 1 second of silence
        max_chunk_size = 18 * 1000  # 18 seconds max chunk size
        min_chunk_size = 5 * 1000  # 5 seconds min chunk size

        # Detect non-silent ranges in the audio
        nonsilent_ranges = detect_nonsilent(
            audio, 
            min_silence_len=silence_duration, 
            silence_thresh=-40, 
            seek_step=100
        )

        final_chunks = []
        if not nonsilent_ranges:
            print("No nonsilent ranges detected.")
            return []

        # Process and create chunks
        for start, end in nonsilent_ranges:
            chunk = audio[start:end]
            if min_chunk_size <= len(chunk) <= max_chunk_size:
                final_chunks.append(chunk)
            elif len(chunk) > max_chunk_size:
                # Split larger chunks based on additional silence
                split_chunks = split_on_silence(
                    chunk, 
                    min_silence_len=silence_duration, 
                    silence_thresh=-40, 
                    keep_silence=500
                )
                for sub_chunk in split_chunks:
                    if min_chunk_size <= len(sub_chunk) <= max_chunk_size:
                        final_chunks.append(sub_chunk)

        # Export chunks to the output directory and return paths
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

# Save audio chunks to the database
async def save_chunks_to_db(video_uuid, video_id, chunk_paths):
    """Save each chunk's metadata to the AudioChunks table."""
    try:
        async with async_session() as session:
            async with session.begin():
                for chunk_path in chunk_paths:
                    new_chunk = AudioChunks(
                        video_id=video_id,
                        video_uuid=video_uuid,
                        file_path=chunk_path
                    )
                    session.add(new_chunk)
            await session.commit()
            print(f"Audio chunks saved to database for video UUID: {video_uuid}")
    except SQLAlchemyError as e:
        print(f"Error saving chunks to database: {e}")
        raise

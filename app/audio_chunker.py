import os
import uuid
from pydub import AudioSegment
from pydub.silence import split_on_silence

# Function to calculate dynamic silence threshold
def dynamic_silence_thresh(audio_segment, target_dbfs=-40):
    average_dbfs = audio_segment.dBFS
    return max(target_dbfs, average_dbfs - 10)

# Updated chunk_audio function with dynamic silence adjustment
def chunk_audio(input_file, 
                min_duration=6000,  # Minimum chunk duration in ms
                max_duration=18000,  # Maximum chunk duration in ms
                target_dbfs=-40,     # Target silence threshold
                keep_silence=1000,   # Initial keep silence duration
                overlap=0,           # Overlap duration between chunks
                use_sample_rate_16000=False):
    
    try:
        # Load the audio file
        audio = AudioSegment.from_file(input_file)
        
        # If the user opts for 16000 Hz sample rate, resample and convert to mono
        if use_sample_rate_16000:
            audio = audio.set_frame_rate(16000).set_channels(1)

    except Exception as e:
        print(f"Error loading audio file: {e}")
        return []

    # Determine the silence threshold dynamically
    silence_thresh = dynamic_silence_thresh(audio, target_dbfs)

    # Try splitting audio using dynamic silence adjustment logic
    silence_duration = keep_silence
    output_chunks = []
    while silence_duration >= 100:  # Minimum allowable silence duration is 100ms
        # Split audio into chunks based on silence
        chunks = split_on_silence(audio, 
                                  min_silence_len=silence_duration, 
                                  silence_thresh=silence_thresh, 
                                  keep_silence=silence_duration)

        for chunk in chunks:
            chunk_length = len(chunk)

            if chunk_length < min_duration:
                # Skip chunks that are too short
                continue

            if chunk_length > max_duration:
                # If chunk is too long, reduce silence duration and retry splitting
                silence_duration -= 100
                break  # Retry splitting with reduced silence duration
            else:
                # If chunk is within valid range, append to output_chunks
                output_chunks.append(chunk)
        
        # If all chunks are within limits, exit loop
        if all(min_duration <= len(chunk) <= max_duration for chunk in chunks):
            break

    return output_chunks

# Main function to process a single audio file
async def process_single_audio(input_file, output_base_directory, use_sample_rate_16000=False):
    filename = os.path.basename(input_file)
    file_location = os.path.normpath(input_file)  # Normalize the file path

    print(f"Processing file: {filename}")

    # Generate UUID for the audio file (just for folder name usage)
    file_uuid = str(uuid.uuid4())

    # Commented out the database tasks below
    # video_id = await save_video_to_db(file_uuid, filename, file_location)

    # Create a folder named after the UUID
    uuid_directory = os.path.join(output_base_directory, file_uuid)
    os.makedirs(uuid_directory, exist_ok=True)

    # Chunk the audio, with dynamic silence adjustment
    chunks = chunk_audio(input_file, 
                         min_duration=6000, 
                         max_duration=18000, 
                         target_dbfs=-40, 
                         keep_silence=1000, 
                         overlap=1000, 
                         use_sample_rate_16000=use_sample_rate_16000)

    # Save each chunk as a file (no database saving for now)
    for i, chunk in enumerate(chunks):
        chunk_filename = os.path.join(uuid_directory, f"chunk_{i+1}.wav")
        chunk.export(chunk_filename, format="wav")  # Save chunk as a WAV file
        print(f"Saved {chunk_filename}, duration: {len(chunk) / 1000:.2f} seconds")

    print(f"All chunks for {filename} have been saved in the folder: {uuid_directory}")

# Process all audio files in a directory
async def process_all_audios(input_directory, output_base_directory, use_sample_rate_16000=False):
    results = []
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.lower().endswith(('.wav', '.flac', '.ogg')):  # Process WAV, FLAC, OGG files
                input_file = os.path.join(root, file)
                await process_single_audio(input_file, output_base_directory, use_sample_rate_16000=use_sample_rate_16000)
                results.append(file)
    return results

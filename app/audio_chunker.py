import os
from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_nonsilent
import uuid

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


def process_single_audio(input_file, output_base_directory, use_sample_rate_16000=False):
    # Include file extension in filename
    filename = os.path.basename(input_file)

    print(f"Processing file: {filename}")

    # Generate UUID for the audio file
    file_uuid = str(uuid.uuid4())

    # Create a folder named after the UUID
    uuid_directory = os.path.join(output_base_directory, file_uuid)
    os.makedirs(uuid_directory, exist_ok=True)

    # Split the audio into chunks using the provided function
    chunk_filenames = split_audio_with_silence(input_file, uuid_directory)

    print(f"All chunks for {filename} have been saved in the folder: {uuid_directory}")

def process_all_audios(input_directory, output_base_directory, use_sample_rate_16000=False):
    results = []
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.lower().endswith(('.wav', '.flac', '.ogg')):  # Only process WAV, FLAC, OGG
                input_file = os.path.join(root, file)
                process_single_audio(input_file, output_base_directory, use_sample_rate_16000=use_sample_rate_16000)
                results.append(file)
    return results
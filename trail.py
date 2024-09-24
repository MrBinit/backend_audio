from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

def split_audio_with_variable_silence(audio_file, output_dir):
    # Load the audio file
    audio = AudioSegment.from_wav(audio_file)
    
    # Set initial silence duration to 1 second (1000ms)
    silence_duration = 1000
    max_chunk_size = 18 * 1000  # 18 seconds in milliseconds
    min_chunk_size = 5 * 1000  # 5 seconds in milliseconds
    
    chunks = split_on_silence(
        audio, 
        min_silence_len=silence_duration, 
        silence_thresh=-40, 
        keep_silence=100  # Add a bit of silence at the start/end of each chunk
    )
    
    # Adjust chunks to meet size requirements
    final_chunks = []
    chunk_index = 1
    for chunk in chunks:
        while len(chunk) > max_chunk_size and silence_duration > 0:
            # Reduce silence duration if chunk is too large
            silence_duration -= 100  # Decrease by 100ms
            chunks = split_on_silence(
                audio, 
                min_silence_len=silence_duration, 
                silence_thresh=-40, 
                keep_silence=100
            )
        final_chunks.append(chunk)
        
        # Export the chunk to the output directory
        output_path = os.path.join(output_dir, f"chunk_{chunk_index}.wav")
        chunk.export(output_path, format="wav")
        chunk_index += 1

# File paths
audio_file = "/Users/mrbinit/Desktop/audio_backend/datasets/Bagaichama Najau Timi (Cover) ｜ Subodh KC ｜ Sansic Records.wav"
output_dir = "/Users/mrbinit/Desktop/audio_backend/output"

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Split the audio and save the chunks
split_audio_with_variable_silence(audio_file, output_dir)

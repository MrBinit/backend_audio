from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_nonsilent
import os

def split_audio_with_silence(audio_file, output_dir):
    # Load the audio file
    audio = AudioSegment.from_wav(audio_file)
    
    # Set parameters
    silence_duration = 1000  # Initial silence duration (1 second)
    max_chunk_size = 18 * 1000  # Max chunk size (18 seconds)
    min_chunk_size = 5 * 1000  # Min chunk size (5 seconds)
    
    # Detect non-silent segments but with some silence retained
    nonsilent_ranges = detect_nonsilent(audio, min_silence_len=silence_duration, silence_thresh=-40, seek_step=100)
    final_chunks = []
    
    # If there are no non-silent ranges, return an empty list
    if not nonsilent_ranges:
        return []

    for start, end in nonsilent_ranges:
        chunk = audio[start:end]
        
        # If the chunk is larger than the minimum size, keep silence
        if min_chunk_size <= len(chunk) <= max_chunk_size:
            final_chunks.append(chunk)
        elif len(chunk) > max_chunk_size:
            # Further split the chunk if it's too large, keeping silence
            split_chunks = split_on_silence(chunk, min_silence_len=silence_duration, silence_thresh=-40, keep_silence=500)
            for sub_chunk in split_chunks:
                if min_chunk_size <= len(sub_chunk) <= max_chunk_size:
                    final_chunks.append(sub_chunk)
    
    # If no valid chunks were found, return an empty list
    if not final_chunks:
        return []

    # Export the final chunks and return their paths
    output_paths = []
    for i, final_chunk in enumerate(final_chunks):
        output_path = os.path.join(output_dir, f"chunk_{i+1}.wav")
        final_chunk.export(output_path, format="wav")
        output_paths.append(output_path)

    return output_paths  # Always return a list (empty if no chunks were exported)

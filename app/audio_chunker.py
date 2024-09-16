# audio_chunker.py
import os
import uuid
import csv
from pydub import AudioSegment
from pydub.silence import split_on_silence

def dynamic_silence_thresh(audio_segment, target_dbfs=-40):
    average_dbfs = audio_segment.dBFS
    return max(target_dbfs, average_dbfs - 10)

def chunk_audio(input_file, 
                min_duration=6000, 
                max_duration=18000, 
                target_dbfs=-40,
                keep_silence=500, 
                overlap=0):
    try:
        # Load the audio file
        audio = AudioSegment.from_file(input_file)
    except Exception as e:
        print(f"Error loading audio file: {e}")
        return []

    silence_thresh = dynamic_silence_thresh(audio, target_dbfs)

    chunks = split_on_silence(audio, 
                              min_silence_len=500, 
                              silence_thresh=silence_thresh, 
                              keep_silence=keep_silence)

    output_chunks = []
    current_chunk = AudioSegment.empty()
    
    for chunk in chunks:
        if len(current_chunk) + len(chunk) - overlap <= max_duration:
            current_chunk += chunk
        else:
            if len(current_chunk) >= min_duration:
                output_chunks.append(current_chunk)
            current_chunk = chunk
    
    if len(current_chunk) >= min_duration:
        output_chunks.append(current_chunk)
    
    if len(current_chunk) < min_duration and output_chunks:
        output_chunks[-1] += current_chunk

    if overlap > 0:
        output_chunks = [chunk[:-overlap] for chunk in output_chunks[:-1]] + [output_chunks[-1]]

    return output_chunks

def read_existing_uuids(csv_file_path):
    existing_uuids = set()
    if os.path.isfile(csv_file_path):
        with open(csv_file_path, mode='r', newline='') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader, None)
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

def process_single_audio(input_file, output_base_directory, csv_file_path):
    print("Processing file:", input_file)
    existing_uuids = read_existing_uuids(csv_file_path)

    # Generate UUID for the audio file
    file_uuid = str(uuid.uuid4())
    filename = os.path.basename(input_file)

    # Skip if the file has been processed before
    if file_uuid in existing_uuids:
        print(f"Skipping {filename} as it has already been processed with UUID {file_uuid}.")
        return

    # Create a folder named after the UUID
    uuid_directory = os.path.join(output_base_directory, file_uuid)
    os.makedirs(uuid_directory, exist_ok=True)

    # Save UUID and filename to the CSV
    save_uuid_to_csv(csv_file_path, filename, file_uuid)

    # Chunk the audio
    chunks = chunk_audio(input_file, min_duration=6000, max_duration=18000, target_dbfs=-40, keep_silence=500, overlap=1000)

    # Save chunks in the UUID-named folder
    for i, chunk in enumerate(chunks):
        chunk_filename = os.path.join(uuid_directory, f"chunk_{i+1}.mp3")
        chunk.export(chunk_filename, format="mp3")
        print(f"Saved {chunk_filename}, duration: {len(chunk) / 1000:.2f} seconds")

    print(f"All chunks for {filename} have been saved in the folder: {uuid_directory}")
    print(f"File UUID has been saved in: {csv_file_path}")

def process_all_audios(input_directory, output_base_directory, csv_file_path):
    results = []
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
                input_file = os.path.join(root, file)
                process_single_audio(input_file, output_base_directory, csv_file_path)
                results.append(file)
    return results

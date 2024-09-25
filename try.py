import os
import requests
from app.core.config import CHUNK_OUTPUT  # Assuming CHUNK_OUTPUT is the root directory

# API endpoint
url = "http://192.168.88.10:8028/transcribe/"

# Text file to save transcriptions
output_file_path = os.path.join(CHUNK_OUTPUT, "transcriptions.txt")

# Function to transcribe an audio file
def transcribe_audio(audio_file_path):
    with open(audio_file_path, 'rb') as audio_file:
        # Send the POST request with the audio file
        files = {'audio': audio_file}
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            return response.json()  # Assuming the API returns the transcription as JSON
        else:
            print(f"Failed to transcribe {audio_file_path}. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None

# Function to traverse directories recursively and find all audio files
def find_audio_files(directory):
    audio_files = []
    # Walk through the directory and subdirectories
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".wav"):  # Only process .wav files
                audio_files.append(os.path.join(root, file))
    return audio_files

# Main logic
with open(output_file_path, 'w') as output_file:
    # Find all audio files recursively in CHUNK_OUTPUT
    audio_files = find_audio_files(CHUNK_OUTPUT)

    # Process each audio file
    for audio_file_path in audio_files:
        print(f"Transcribing {audio_file_path}...")
        
        # Transcribe the audio file
        transcription = transcribe_audio(audio_file_path)
        
        # If transcription is successful, save to file
        if transcription:
            output_file.write(f"Transcription for {audio_file_path}:\n")
            output_file.write(transcription + "\n\n")  # Save the transcription
            print(f"Transcription saved for {audio_file_path}")
        else:
            output_file.write(f"Transcription failed for {audio_file_path}\n\n")

print(f"All transcriptions saved to {output_file_path}")

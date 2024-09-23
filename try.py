from pydub import AudioSegment

# Load the audio file (any format)
audio = AudioSegment.from_file("/Users/mrbinit/Desktop/untitled folder/output_chunk/e6eeb965-0755-47cf-a08c-8f2deab69a3c/chunk_2.wav")  # replace with your file path

# Get the sample rate and number of channels
sample_rate = audio.frame_rate
channels = audio.channels

# Check if the audio is mono or stereo
if channels == 1:
    print(f"The audio is mono with a sample rate of {sample_rate} Hz.")
else:
    print(f"The audio is stereo with a sample rate of {sample_rate} Hz.")

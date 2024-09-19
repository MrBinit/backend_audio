import requests

# The URL of the server where you want to send the POST request
url = 'http://192.168.88.10:8028/transcribe/'

# The path to the audio file you want to upload
file_path = '/Users/mrbinit/Desktop/untitled folder/output_chunk/5d54e5f2-b798-403f-a1eb-de629f959d37/chunk_1.mp3'

# Prepare the files and headers
files = {'audio': ('chunk_1.mp3', open(file_path, 'rb'), 'audio/mpeg')}
headers = {
    'accept': 'application/json'
}

# Send the POST request
response = requests.post(url, headers=headers, files=files)

# Print the response from the server
print('Status Code:', response.status_code)
print('Response JSON:', response.json())

import os
import requests
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models import AudioChunks
from app.core.config import TRANSCRIPTION_API_URL

async def transcribe_chunks():
    # Fetch all audio chunks that need transcription
    async with async_session() as session:
        async with session.begin():
            stmt = select(AudioChunks).where(AudioChunks.transcribe == None)
            result = await session.execute(stmt)
            audio_chunks = result.scalars().all()

            if not audio_chunks:
                print("No audio chunks found that need transcription.")
                return {"message": "No audio chunks to transcribe."}

            # Process each chunk with the transcription API
            for chunk in audio_chunks:
                try:
                    # Read the chunk audio file
                    print(f"Processing chunk: {chunk.file_path}")
                    with open(chunk.file_path, 'rb') as audio_file:
                        files = {'audio': ('chunk_1.mp3', audio_file, 'audio/mpeg')}
                        headers = {
                            'accept': 'application/json'
                        }
                        # Send the audio file to the transcription API
                        response = requests.post(TRANSCRIPTION_API_URL, headers=headers, files=files)
                        response.raise_for_status()  # Raise an error for bad status codes

                        # Debugging: Print raw response text to understand what is being returned
                        print(f"Raw response: {response.text}")

                        # Attempt to parse JSON response
                        try:
                            response_data = response.json()
                            transcription = response_data.get('transcription', 'No transcription found')
                        except ValueError:
                            # If response is not JSON, handle the error
                            print(f"Error: Response is not in JSON format. Response text: {response.text}")
                            transcription = 'Error: Non-JSON response'

                        print(f"Transcription for {chunk.file_path}: {transcription}")
                    
                    # Update the chunk's transcribe field
                    chunk.transcribe = transcription

                    # Update the database entry
                    session.add(chunk)
                except requests.exceptions.RequestException as e:
                    print(f"Request error for chunk {chunk.file_path}: {e}")
                    chunk.transcribe = 'Transcription failed'
                    session.add(chunk)
                except FileNotFoundError:
                    print(f"File not found: {chunk.file_path}")
                    chunk.transcribe = 'File not found'
                    session.add(chunk)
                except Exception as e:
                    print(f"Error processing chunk {chunk.file_path}: {e}")
                    chunk.transcribe = 'Error during transcription'
                    session.add(chunk)
            
        await session.commit()  # Commit changes to the database

    return {"message": f"Transcription completed for {len(audio_chunks)} chunks."}


 
# import random
# import string
# from sqlalchemy.future import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.database import async_session
# from app.models import AudioChunks

# async def transcribe_chunks():
#     # Fetch all audio chunks that need transcription
#     async with async_session() as session:
#         async with session.begin():
#             stmt = select(AudioChunks).where(AudioChunks.transcribe == None)
#             result = await session.execute(stmt)
#             audio_chunks = result.scalars().all()

#             # Simulate transcription for each chunk
#             for chunk in audio_chunks:
#                 try:
#                     # Simulate a transcription by generating random text
#                     transcription = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
                    
#                     # Update the chunk's transcribe field
#                     chunk.transcribe = transcription

#                     # Update the database entry
#                     session.add(chunk)
#                 except Exception as e:
#                     print(f"Error processing chunk {chunk.file_path}: {e}")
            
#         await session.commit()  # Commit changes to the database

#     return {"message": f"Transcription completed for {len(audio_chunks)} chunks."}

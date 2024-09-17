# import os
# import requests
# from sqlalchemy.future import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.database import async_session
# from app.models import AudioChunks

# # Replace with your transcription API URL
# TRANSCRIPTION_API_URL = "https://your-transcription-api.com/transcribe"

# async def transcribe_chunks():
#     # Fetch all audio chunks that need transcription
#     async with async_session() as session:
#         async with session.begin():
#             stmt = select(AudioChunks).where(AudioChunks.transcribe == None)
#             result = await session.execute(stmt)
#             audio_chunks = result.scalars().all()

#             # Process each chunk with the transcription API
#             for chunk in audio_chunks:
#                 try:
#                     # Read the chunk audio file
#                     with open(chunk.file_path, 'rb') as audio_file:
#                         files = {'file': audio_file}
#                         # Send the audio file to the transcription API
#                         response = requests.post(TRANSCRIPTION_API_URL, files=files)
#                         response.raise_for_status()  # Raise an error for bad status codes
#                         transcription = response.json().get('transcription', 'No transcription found')
                    
#                     # Update the chunk's transcribe field
#                     chunk.transcribe = transcription

#                     # Update the database entry
#                     session.add(chunk)
#                 except Exception as e:
#                     print(f"Error transcribing chunk {chunk.file_path}: {e}")
            
#         await session.commit()  # Commit changes to the database

#     return {"message": f"Transcription completed for {len(audio_chunks)} chunks."}
 
import random
import string
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models import AudioChunks

async def transcribe_chunks():
    # Fetch all audio chunks that need transcription
    async with async_session() as session:
        async with session.begin():
            stmt = select(AudioChunks).where(AudioChunks.transcribe == None)
            result = await session.execute(stmt)
            audio_chunks = result.scalars().all()

            # Simulate transcription for each chunk
            for chunk in audio_chunks:
                try:
                    # Simulate a transcription by generating random text
                    transcription = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
                    
                    # Update the chunk's transcribe field
                    chunk.transcribe = transcription

                    # Update the database entry
                    session.add(chunk)
                except Exception as e:
                    print(f"Error processing chunk {chunk.file_path}: {e}")
            
        await session.commit()  # Commit changes to the database

    return {"message": f"Transcription completed for {len(audio_chunks)} chunks."}

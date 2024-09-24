from fastapi import FastAPI, Query, HTTPException
from app.audio_download import download_audio
from app.audio_chunker import split_audio_with_silence
from app.database import engine
from app.models import Base
from app.topics import topics_to_download
from app.database import fetch_data
from app.core.config import ORIGINAL_DIRECTORY, CHUNK_OUTPUT
from app.transcribe import transcribe_chunks
from app.huggingface_handler import insert_data_to_postgres, upload_to_huggingface
import asyncio
import os

app = FastAPI()

# Ensure the table is created on startup
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/download_all_audios")
async def download_all_audios():
    results = []
    
    for topic in topics_to_download:
        downloaded_video = await download_audio(query=topic, is_url=False)  # Add 'await'
        results.append(downloaded_video)

    return {"audios_downloaded": results}

@app.get("/download_audio_by_url")
async def download_audio_by_url(
    youtube_url: str = Query(..., description="The YouTube video URL to download"), 
    use_sample_rate_16000: bool = Query(False, description="Set the sample rate to 16000 Hz and mono audio (True or False)")
):
    result = await download_audio(query=youtube_url, is_url=True, use_sample_rate_16000=use_sample_rate_16000)  # Add 'await'
    return result

# @app.post("/chunk_audios")
# async def chunk_audios():
#     input_directory = ORIGINAL_DIRECTORY
#     output_directory = CHUNK_OUTPUT
    
#     processed_files = await split_audio_with_silence(input_directory, output_directory) 
#     return {"processed_files": processed_files}

@app.post("/transcribe_chunks")
async def transcribe_audio_chunks():
    result = await transcribe_chunks()  # Add 'await'
    return result

@app.post("/load_dataset_to_db/")
async def load_dataset_to_db(dataset_name: str = Query(..., description="Name of the dataset to load"), 
                             table_name: str = Query(..., description="Name of the table to create")):
    try:
        result = await insert_data_to_postgres(dataset_name, table_name)  # Add 'await'
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/{table_name}")
async def upload_data(table_name: str):
    try:
        # Fetch data from the PostgreSQL database
        df = await fetch_data(table_name)  # Add 'await'

        if df.empty:
            raise HTTPException(status_code=404, detail="No data found in the table")

        # Upload data to Hugging Face
        upload_to_huggingface(df)

        return {"message": f"Data from table '{table_name}' uploaded successfully to Hugging Face"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/chunk_audios")
async def chunk_audios():
    input_directory = ORIGINAL_DIRECTORY
    output_directory = CHUNK_OUTPUT
    processed_files = []

    # Loop through each file in the input directory
    for file_name in os.listdir(input_directory):
        file_path = os.path.join(input_directory, file_name)
        
        if os.path.isfile(file_path):
            # Call the split_audio_with_silence function
            result = split_audio_with_silence(file_path, output_directory)
            
            # Check if result is a valid list (even if it's empty, that's fine)
            if result:
                processed_files.extend(result)

    return {"processed_files": processed_files}

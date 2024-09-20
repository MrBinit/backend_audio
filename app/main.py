from fastapi import FastAPI, Query, HTTPException
from app.audio_download import download_audio
from app.audio_chunker import process_all_audios
from app.database import engine
from app.models import Base
from app.topics import topics_to_download
import os
from app.core.config import ORIGINAL_DIRECTORY, CHUNK_OUTPUT
from app.transcribe import transcribe_chunks
from app.huggingface_handler import insert_data_to_postgres, fetch_data_from_postgres, upload_data_to_huggingface

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
        downloaded_video = await download_audio(query=topic, is_url=False)
        results.append(downloaded_video)

    return {"audios_downloaded": results}

@app.get("/download_audio_by_url")
async def download_audio_by_url(
    youtube_url: str = Query(..., description="The YouTube video URL to download"), 
    format_choice: str = Query("mp3", description="Choose the audio format: mp3 or wav")
):
    result = await download_audio(query=youtube_url, is_url=True, format_choice=format_choice)
    return result


@app.post("/chunk_audios")
async def chunk_audios():
    input_directory = ORIGINAL_DIRECTORY
    output_directory = CHUNK_OUTPUT
    
    # Call with the correct number of arguments
    processed_files = await process_all_audios(input_directory, output_directory)
    return {"processed_files": processed_files}

@app.post("/transcribe_chunks")
async def transcribe_audio_chunks():
    result = await transcribe_chunks()
    return result

@app.post("/load_dataset_to_db/")
async def load_dataset_to_db(dataset_name: str = Query(..., description="Name of the dataset to load"), 
                             table_name: str = Query(..., description="Name of the table to create")):
    try:
        result = await insert_data_to_postgres(dataset_name, table_name)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_data_to_huggingface/")
async def upload_data_to_hf(table_name: str = Query(..., description="Name of the table to fetch data from"), 
                            hf_dataset_name: str = Query(..., description="Name of the Hugging Face dataset to create")):
    try:
        # Fetch data from PostgreSQL
        df = await fetch_data_from_postgres(table_name)
        
        # Upload data to Hugging Face
        upload_data_to_huggingface(df, hf_dataset_name)
        
        return {"message": f"Data from table '{table_name}' successfully uploaded to Hugging Face as '{hf_dataset_name}'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
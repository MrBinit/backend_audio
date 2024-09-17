# main.py
from fastapi import FastAPI, Query
from app.audio_download import download_audio
from app.audio_chunker import process_all_audios
from app.database import engine, async_session
from app.models import Base
from app.topics import topics_to_download
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
        downloaded_video = await download_audio(query=topic, is_url=False)
        results.append(downloaded_video)

    return {"audios_downloaded": results}

@app.get("/download_audio_by_url")
async def download_audio_by_url(youtube_url: str = Query(..., description="The YouTube video URL to download")):
    result = await download_audio(query=youtube_url, is_url=True)
    return result

@app.post("/chunk_audios")
async def chunk_audios():
    input_directory = "/Users/mrbinit/Desktop/untitled folder/datasets"
    output_directory = "/Users/mrbinit/Desktop/untitled folder/output_chunk"
    csv_file_path = os.path.join(output_directory, "audio_chunks.csv")
    
    # Call with the correct number of arguments
    processed_files = await process_all_audios(input_directory, output_directory)
    return {"processed_files": processed_files}

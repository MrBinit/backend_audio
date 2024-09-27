from fastapi import FastAPI, Query, HTTPException
from app.audio_download import download_audio
from app.database import engine
from app.models import Base
from app.topics import topics_to_download
from app.database import fetch_data
from app.core.config import CHUNK_OUTPUT
from app.transcribe import transcribe_chunks
from app.huggingface_handler import insert_data_to_postgres, upload_to_huggingface
from app.audio_chunker import audio_chunker
import os
from sqlalchemy.future import select
from app.models import Download_videos
from app.database import async_session

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
        downloaded_video = await download_audio(query=topic, is_url=False, topic_name = topic)  # Add 'await'
        results.append(downloaded_video)

    return {"audios_downloaded": results}

@app.get("/download_audio_by_url")
async def download_audio_by_url(
    youtube_url: str = Query(..., description="The YouTube video URL to download"), 
    use_sample_rate_16000: bool = Query(False, description="Set the sample rate to 16000 Hz and mono audio (True or False)")
):
    result = await download_audio(query=youtube_url, is_url=True, use_sample_rate_16000=use_sample_rate_16000)  # Add 'await'
    return result


@app.post("/split-audio/{uuid}")
async def split_audio(uuid: str):
    # Call the audio_chunker function which will handle chunking and database saving
    video_info = await audio_chunker(uuid, CHUNK_OUTPUT)

    # If an error occurs in audio_chunker, raise an HTTPException
    if "error" in video_info:
        raise HTTPException(status_code=404, detail=video_info["error"])

    # Retrieve the paths of the split audio chunks
    chunk_paths = video_info.get("chunks")
    
    if not chunk_paths:
        raise HTTPException(status_code=500, detail="Failed to split the audio into chunks")

    # Return the paths of the saved chunks
    return {"chunk_paths": chunk_paths}

@app.get("/check_and_chunk_all")
async def check_and_chunk_all():
    try:
        processed_videos = []

        async with async_session() as session:
            async with session.begin():
                stmt = select(Download_videos).where(Download_videos.chunk_status == 'False')
                result = await session.execute(stmt)
                videos_to_process = result.scalars().all()

                if not videos_to_process:
                    return {"message": "No audio to chunk. All audios are already chunked."}
                for video in videos_to_process:
                    response = await audio_chunker(video.uuid, CHUNK_OUTPUT)
                    processed_videos.append({
                        "video_uuid": video.uuid,
                        "status": response.get("Message", "Complete"),
                        "chunks": response.get("chunks", [])
                    })
            return {
                "message" : f"Processed {len(processed_videos)} videos",
                "processed_videos": processed_videos
            }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code= 500, detail = "An error occured while processing the request")

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
    
@app.post("/get_audio_location/")
async def get_audio_location(uuid: str = Query(..., description = "UUID of the audio")):
    try:
        result = await audio_chunker(uuid)
        if 'location' not in result:
            raise HTTPException (status_code = 404, detail= result.get("error", "No video found with this UUID"))
        return {"file_location": result['location']}
    except Exception as e:
        raise HTTPException(status_code= 500, detail= str(e))
    





from fastapi import FastAPI, Query
from app.audio_download import download_audio
from app.database import engine, async_session
from app.models import Base
from app.topics import topics_to_download

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
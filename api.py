from fastapi import FastAPI
from pydantic import BaseModel
from relic_extractor import extract_relics

app = FastAPI()

class VideoRequest(BaseModel):
    video_path: str
    start_second: int = 0

@app.post("/extract-relics/")
async def extract_relics_endpoint(request: VideoRequest):
    data = extract_relics(request.video_path, request.start_second)
    return {"relics": data}

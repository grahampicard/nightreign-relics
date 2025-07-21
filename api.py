from fastapi import FastAPI, File, UploadFile
from relic_extractor import extract_relics
import shutil
import tempfile

app = FastAPI()


@app.post("/extract-relics/")
async def extract_relics_endpoint(video: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        shutil.copyfileobj(video.file, tmp)
        tmp_path = tmp.name
    print("starting")
    data = extract_relics(tmp_path)
    print("done")
    return {"relics": data}

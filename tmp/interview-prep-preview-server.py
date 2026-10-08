import os
import sys
from pathlib import Path

os.environ["JOBPILOT_DATA_DIR"] = str(Path(__file__).parent / "interview-prep-test-data")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "JobPilot"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from jobpilot.interview_prep import register_routes
import uvicorn

app = FastAPI()
register_routes(app)
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parents[1] / "JobPilot/jobpilot/static"))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=18765)

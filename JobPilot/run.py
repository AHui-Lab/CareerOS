import os
from pathlib import Path

from dotenv import load_dotenv
import uvicorn

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

if __name__ == "__main__":
    uvicorn.run(
        "jobpilot.main:app",
        host=os.getenv("JOBPILOT_HOST", "127.0.0.1"),
        port=int(os.getenv("JOBPILOT_PORT", "8765")),
        reload=False,
    )

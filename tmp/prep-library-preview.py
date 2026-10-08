import os
import sys
import tempfile
from pathlib import Path

os.environ["JOBPILOT_DATA_DIR"] = tempfile.mkdtemp(prefix="careeros-prep-check-")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "JobPilot"))

import uvicorn
from jobpilot.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=18765)

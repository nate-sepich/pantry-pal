from datetime import datetime
import os
from pathlib import Path

WORKING_DIRECTORY = Path(os.path.join(Path(os.getcwd()), 'doc_writing', datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))

def prelude(state):
    written_files = []
    if not WORKING_DIRECTORY.exists():
        WORKING_DIRECTORY.mkdir(parents=True, exist_ok=True)
    try:
        written_files = [
            f.relative_to(WORKING_DIRECTORY) for f in WORKING_DIRECTORY.rglob("*")
        ]
    except Exception:
        pass
    if not written_files:
        return {**state, "current_files": "No files written."}
    return {
        **state,
        "current_files": "\nBelow are files your team has written to the directory:\n"
        + "\n".join([f" - {f}" for f in written_files]),
    }
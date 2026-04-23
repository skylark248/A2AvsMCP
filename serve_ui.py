from pathlib import Path
import sys

import uvicorn

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


if __name__ == "__main__":
    uvicorn.run("a2a_vs_mcp.web:app", host="127.0.0.1", port=8008, reload=False)

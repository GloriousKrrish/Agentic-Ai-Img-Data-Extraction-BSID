import sys
import os
import traceback
from pathlib import Path

# Add project root directory to sys.path so backend modules can be imported
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

os.environ["VERCEL"] = "1"

try:
    from backend.main import app
except Exception as err:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="Vercel Serverless Error Handler")

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    def error_handler(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Vercel Serverless Import Error",
                "message": str(err),
                "traceback": traceback.format_exc()
            }
        )

"""
FastAPI entrypoint for Returns Management System (RMS).
Re-exports the unified FastAPI app from run_app.py.
"""

from run_app import app, get_db

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

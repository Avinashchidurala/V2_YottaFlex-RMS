#!/usr/bin/env python3
"""
Returns Management System (RMS) - Entry Point
Delegates to run_app.py to run the FastAPI app and embedded web UI.
"""
import sys
import uvicorn
from run_app import app

if __name__ == "__main__":
    port = 8000
    print(f"[*] Starting Returns Management System on http://localhost:{port}")
    uvicorn.run("run_app:app", host="0.0.0.0", port=port, reload=False)

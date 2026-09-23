"""
AI Lab Dashboard — FastAPI application entry point.

Start with:
    uvicorn backend.main:app
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="AI Lab Dashboard")

_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the static frontend page."""
    html = (_FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)

"""
AI Lab Dashboard — FastAPI application entry point.

Start with:
    uvicorn backend.main:app
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .routers import balance, broadcast, cost, health, history, models, request

app = FastAPI(title="AI Lab Dashboard")

# ---------------------------------------------------------------------------
# Security middleware
# ---------------------------------------------------------------------------

# CORS: only allow requests that originate from the dashboard itself
# (both the 127.0.0.1 and localhost spellings).  Blocks cross-origin
# requests from arbitrary web pages — prevents DNS-rebinding and CSRF
# against the locally-running API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    """Attach security headers to every response."""
    response = await call_next(request)
    # Content-Security-Policy: allow resources only from self.
    # Chart.js is served locally under /static, so no external script src needed.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


app.include_router(health.router)
app.include_router(models.router)
app.include_router(request.router)
app.include_router(balance.router)
app.include_router(history.router)
app.include_router(cost.router)
app.include_router(broadcast.router)

_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the static frontend page."""
    html = (_FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)

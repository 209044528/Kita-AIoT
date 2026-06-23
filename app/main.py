from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os

from app.core.config import settings
from app.api.main import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="AIoT device operations tool API with visual dashboard.",
    version="0.2.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}

# Mount Frontend Static Files
# Define the path to the web directory
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")

# Create web dir if it doesn't exist during startup just in case
os.makedirs(WEB_DIR, exist_ok=True)

# Mount the web directory
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

@app.get("/")
def serve_frontend():
    """Redirect root to the static frontend."""
    return RedirectResponse(url="/static/index.html")

from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.api.main import api_router
from app.models import CallLog


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    consumer = None
    if settings.MQTT_ENABLED:
        from app.mqtt.consumer import AlarmConsumer

        consumer = AlarmConsumer()
        consumer.start()
        app.state.mqtt_consumer = consumer
    yield
    if consumer:
        consumer.stop()

app = FastAPI(
    title=settings.APP_NAME,
    description="AIoT device operations Agent tools, workflow tracking, MQTT and MinIO integration.",
    version="0.3.0",
    lifespan=lifespan,
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


@app.middleware("http")
async def persist_call_log(request, call_next):
    request_id = request.headers.get("x-request-id", uuid4().hex)
    started = perf_counter()
    status_code = 500
    error_message = None
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["x-request-id"] = request_id
        return response
    except Exception as exc:
        error_message = str(exc)
        raise
    finally:
        if request.url.path.startswith("/api/") or request.url.path == "/health":
            try:
                with SessionLocal() as db:
                    db.add(
                        CallLog(
                            request_id=request_id,
                            method=request.method,
                            path=request.url.path,
                            status_code=status_code,
                            duration_ms=round((perf_counter() - started) * 1000, 2),
                            client_host=request.client.host if request.client else None,
                            error_message=error_message,
                        )
                    )
                    db.commit()
            except Exception:
                # Logging must not break the business request during startup or DB outages.
                pass


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME, "version": "0.3.0"}

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
os.makedirs(WEB_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

@app.get("/")
def serve_frontend():
    """Redirect root to the static frontend."""
    return RedirectResponse(url="/static/index.html")

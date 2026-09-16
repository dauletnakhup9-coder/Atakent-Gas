import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import admins, application_types, applications, auth, bot_internal, dashboard, reports, settings, ws
from app.config import get_settings
from app.core.rate_limit import limiter
from app.services.realtime import redis_listener

logging.basicConfig(level=logging.INFO)
settings_obj = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings_obj.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    listener_task = asyncio.create_task(redis_listener())
    yield
    listener_task.cancel()


app = FastAPI(title="Gas Service Requests API", version="1.0.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_obj.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})


Path(settings_obj.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings_obj.UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(admins.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(application_types.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(bot_internal.router, prefix="/api")
app.include_router(ws.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}

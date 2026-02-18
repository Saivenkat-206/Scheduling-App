from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

from app import auth, schedules, import_export
from app.config import settings


app = FastAPI(title="Scheduling App API - Dynamic Tables")

# configure logging
logging.basicConfig(filename=settings.LOG_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# CORS: restrict to configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or [],
    allow_methods=["*"],
    allow_headers=["*"],
)


class MaxUploadSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_size:
                    return JSONResponse({"detail": "Request body too large"}, status_code=413)
            except ValueError:
                pass
        return await call_next(request)


class FreezeWritesMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allow_write: bool):
        super().__init__(app)
        self.allow_write = allow_write

    async def dispatch(self, request: Request, call_next):
        if not self.allow_write and request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return JSONResponse({"detail": "Modifications temporarily disabled for security review"}, status_code=403)
        return await call_next(request)


# Add middlewares
app.add_middleware(MaxUploadSizeMiddleware, max_size=settings.MAX_UPLOAD_SIZE)
app.add_middleware(FreezeWritesMiddleware, allow_write=settings.ALLOW_WRITE)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled exception: %s", exc)
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


app.include_router(auth.router, prefix="/auth")
app.include_router(schedules.router, prefix="/schedules")
app.include_router(import_export.router, prefix="/files")

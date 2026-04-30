"""
FocuseMate Backend – Main Application Entry Point
====================================================
Run with:  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Docs at :  http://localhost:8000/docs
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import decode_token_safe
from app.db.session import close_db, init_db

# ── Route imports ────────────────────────────────────────────────
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.friends import router as friends_router
from app.routes.rooms import router as rooms_router
from app.routes.members import router as members_router
from app.routes.messages import router as messages_router
from app.routes.resources import router as resources_router
from app.routes.invitations import router as invitations_router
from app.routes.notifications import router as notifications_router
from app.routes.settings import router as settings_router
from app.routes.support import router as support_router
from app.routes.analytics import router as analytics_router

# ── WebSocket imports ────────────────────────────────────────────
from app.websocket.handlers import handle_websocket

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("focusemate")


# ── Lifespan (startup / shutdown) ────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting FocuseMate backend …")
    await init_db()
    logger.info("✅ Database tables ensured.")
    yield
    logger.info("🛑 Shutting down …")
    await close_db()


# ── Application factory ─────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FocuseMate – Collaborative Productivity Platform API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging / timing middleware ──────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.debug(
        f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.1f}ms)"
    )
    return response


# ── Global exception handler ────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ── Rate limiting middleware (simple in-memory) ──────────────────
_rate_limit_store: dict[str, list[float]] = {}


@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60.0  # 1 minute

    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []

    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if now - t < window
    ]

    if len(_rate_limit_store[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
        )

    _rate_limit_store[client_ip].append(now)
    return await call_next(request)


# ── Register REST routers ───────────────────────────────────────
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(friends_router)
app.include_router(rooms_router)
app.include_router(members_router)
app.include_router(messages_router)
app.include_router(resources_router)
app.include_router(invitations_router)
app.include_router(notifications_router)
app.include_router(settings_router)
app.include_router(support_router)
app.include_router(analytics_router)


# ── WebSocket endpoint ──────────────────────────────────────────
@app.websocket("/ws/rooms/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(None),
):
    """
    WebSocket endpoint for real-time room communication.
    Connect with: ws://host:8000/ws/rooms/{room_id}?token=<jwt_access_token>

    Supported message types:
    - chat_message: {type, content, message_type}
    - webrtc_offer: {type, target_user_id, sdp}
    - webrtc_answer: {type, target_user_id, sdp}
    - webrtc_ice: {type, target_user_id, candidate}
    - join_webrtc: {type}
    - typing: {type, is_typing}
    - ping: {type}
    """
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    payload = decode_token_safe(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    user_id = int(payload["sub"])

    from app.db.session import async_session_factory as ws_session_factory

    async with ws_session_factory() as db:
        try:
            await handle_websocket(websocket, room_id, user_id, db)
        finally:
            await db.close()


# ── Health check ─────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


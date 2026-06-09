from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.apps.demo.routes import router as demo_router
from src.apps.health.routes import router as health_router
from src.apps.users import config as users_config
from src.apps.users.routes import router as auth_router
from src.config import CORS_ALLOW_ORIGINS

app = FastAPI(title="Micro-SaaS API", version="0.1.0")
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(demo_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# authlib Starlette OAuth stores state in request.session during redirect/callback.
app.add_middleware(
    SessionMiddleware,
    secret_key=users_config.JWT_SECRET or "dev-insecure-session-secret",
)

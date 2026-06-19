from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from src.apps.demo.routes import router as demo_router
from src.apps.health.routes import router as health_router
from src.apps.users import config as users_config
from src.apps.users.routes import router as auth_router
from src.config import CORS_ALLOW_ORIGINS
from src.utils.api_errors import ApiErrorDetail, CommonApiErrorCode

app = FastAPI(title="Micro-SaaS API", version="0.1.0")
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(demo_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    detail = ApiErrorDetail(
        code=CommonApiErrorCode.request_validation_error,
        message="Request validation failed",
        params={"errors": jsonable_encoder(exc.errors())},
    )
    return JSONResponse(status_code=422, content={"detail": detail.model_dump()})


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

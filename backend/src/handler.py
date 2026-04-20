"""AWS Lambda entrypoint (API Gateway HTTP API -> ASGI)."""

from mangum import Mangum

from src.main import app

handler = Mangum(app, lifespan="off")

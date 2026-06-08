from src.config import CORS_ALLOW_ORIGINS
from src.utils.env import env_bool, env_int, env_str

AUTH_PASSWORD_ENABLED = env_bool("AUTH_PASSWORD_ENABLED", default=True)
AUTH_GOOGLE_ENABLED = env_bool("AUTH_GOOGLE_ENABLED", default=False)
AUTH_FACEBOOK_ENABLED = env_bool("AUTH_FACEBOOK_ENABLED", default=False)

AUTH_GOOGLE_CLIENT_ID = env_str("AUTH_GOOGLE_CLIENT_ID") if AUTH_GOOGLE_ENABLED else None
AUTH_GOOGLE_CLIENT_SECRET = (
    env_str("AUTH_GOOGLE_CLIENT_SECRET") if AUTH_GOOGLE_ENABLED else None
)
AUTH_FACEBOOK_APP_ID = env_str("AUTH_FACEBOOK_APP_ID") if AUTH_FACEBOOK_ENABLED else None
AUTH_FACEBOOK_APP_SECRET = (
    env_str("AUTH_FACEBOOK_APP_SECRET") if AUTH_FACEBOOK_ENABLED else None
)

JWT_SECRET = env_str("JWT_SECRET", default=None)
JWT_EXPIRE_MINUTES = env_int("JWT_EXPIRE_MINUTES", default=60 * 24 * 7)

_explicit_frontend = env_str("AUTH_FRONTEND_URL", default=None)
if _explicit_frontend:
    AUTH_FRONTEND_URL = _explicit_frontend.rstrip("/")
elif CORS_ALLOW_ORIGINS and CORS_ALLOW_ORIGINS != ["*"]:
    AUTH_FRONTEND_URL = CORS_ALLOW_ORIGINS[0].rstrip("/")
else:
    AUTH_FRONTEND_URL = "http://localhost:5173"

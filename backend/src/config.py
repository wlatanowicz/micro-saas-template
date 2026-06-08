from src.utils.env import env_list, env_str

DATABASE_URL = env_str("DATABASE_URL", default=None)
CORS_ALLOW_ORIGINS = env_list("CORS_ALLOW_ORIGINS", default=["*"])

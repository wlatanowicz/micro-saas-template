from __future__ import annotations

from pathlib import Path

from src.utils.env import env_str

BACKEND_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

NOTIFICATIONS_TRANSPORT = env_str("NOTIFICATIONS_TRANSPORT", default="local")
NOTIFICATIONS_FROM_EMAIL = env_str("NOTIFICATIONS_FROM_EMAIL", default="")
NOTIFICATIONS_EML_DIR = env_str(
    "NOTIFICATIONS_EML_DIR",
    default=str(BACKEND_ROOT / "var" / "emails"),
)

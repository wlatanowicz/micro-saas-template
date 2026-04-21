"""Lambda entrypoint: run Alembic migrations to head (invoked after deploy)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _alembic_ini_path() -> Path:
    # Lambda task root: /var/task with backend layout preserved (alembic.ini next to src/)
    return Path(__file__).resolve().parent.parent / "alembic.ini"


def handler(event: object, context: object) -> dict[str, object]:
    del event, context
    if not os.environ.get("DATABASE_URL", "").strip():
        msg = "DATABASE_URL is not set"
        logger.error(msg)
        raise RuntimeError(msg)

    ini_path = _alembic_ini_path()
    if not ini_path.is_file():
        msg = f"alembic.ini not found at {ini_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    alembic_dir = ini_path.parent / "alembic"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(alembic_dir))

    logger.info("Running Alembic upgrade to head")
    command.upgrade(cfg, "head")
    logger.info("Alembic upgrade finished")
    return {"ok": True, "revision": "head"}

from __future__ import annotations

from string import Template

from src.apps.notifications.config import TEMPLATES_DIR


def load_template(name: str, *, kind: str) -> Template:
    path = TEMPLATES_DIR / f"{name}.{kind}.tpl"
    if not path.is_file():
        msg = f"template not found: {path.name}"
        raise FileNotFoundError(msg)
    return Template(path.read_text(encoding="utf-8"))


def render_template(name: str, *, kind: str, context: dict[str, str]) -> str:
    return load_template(name, kind=kind).substitute(context)

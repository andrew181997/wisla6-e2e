from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

E2E_DIR = Path(__file__).resolve().parent
load_dotenv(E2E_DIR / ".env.local")
load_dotenv(E2E_DIR / ".env")


def base_url() -> str:
    return os.getenv("E2E_BASE_URL", "http://localhost:4300").rstrip("/")


def api_url() -> str:
    return os.getenv("E2E_API_URL", "http://localhost:8088").rstrip("/")


def creds(role: str) -> tuple[str, str]:
    key = role.upper()
    return (
        (os.getenv(f"E2E_{key}_USER") or "").strip(),
        os.getenv(f"E2E_{key}_PASS") or "",
    )


def set_creds(role: str, username: str, password: str) -> None:
    key = role.upper()
    os.environ[f"E2E_{key}_USER"] = username
    os.environ[f"E2E_{key}_PASS"] = password

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    api_key: str = os.getenv("ARK_API_KEY", "").strip()
    base_url: str = os.getenv(
        "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
    ).rstrip("/")
    model: str = os.getenv("ARK_MODEL", "doubao-seedance-2-5-260628").strip()
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))
    task_timeout_seconds: int = int(os.getenv("TASK_TIMEOUT_SECONDS", "3600"))

    @property
    def outputs_dir(self) -> Path:
        path = ROOT_DIR / "outputs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def data_dir(self) -> Path:
        path = ROOT_DIR / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def validate(self) -> None:
        if not self.api_key:
            raise RuntimeError(
                "ARK_API_KEY is empty. Copy .env.example to .env and add your Volcengine Ark API key."
            )
        if not self.model:
            raise RuntimeError("ARK_MODEL is empty.")


settings = Settings()

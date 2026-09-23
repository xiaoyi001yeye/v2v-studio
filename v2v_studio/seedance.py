from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Callable

import requests

from .config import settings


class SeedanceError(RuntimeError):
    pass


class SeedanceClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (api_key or settings.api_key or "").strip()
        if not self.api_key:
            raise SeedanceError("ARK API Key is required.")
        if not settings.model:
            raise SeedanceError("ARK model is not configured.")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    @staticmethod
    def _validate_remote_uri(value: str | None, label: str) -> str:
        value = (value or "").strip()
        if not value:
            raise SeedanceError(f"{label} is required.")
        if not (value.startswith("https://") or value.startswith("asset://")):
            raise SeedanceError(
                f"{label} must be a public HTTPS URL or an Ark asset:// URI."
            )
        return value

    def create_task(
        self,
        *,
        prompt: str,
        mode: str = "text",
        video_uri: str | None = None,
        image_uri: str | None = None,
        ratio: str = "16:9",
        duration: int = 10,
        generate_audio: bool = True,
        watermark: bool = False,
    ) -> str:
        prompt = (prompt or "").strip()
        if not prompt:
            raise SeedanceError("Prompt is required.")

        if mode not in {"text", "image", "edit", "reference"}:
            raise SeedanceError(f"Unsupported generation mode: {mode}")

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]

        if mode == "image":
            image_uri = self._validate_remote_uri(image_uri, "Image URI")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": image_uri},
                    "role": "reference_image",
                }
            )

        elif mode == "edit":
            video_uri = self._validate_remote_uri(video_uri, "Video URI")
            content.append(
                {
                    "type": "video_url",
                    "video_url": {"url": video_uri},
                    "role": "reference_video",
                }
            )

        elif mode == "reference":
            video_uri = self._validate_remote_uri(video_uri, "Video URI")
            if image_uri and image_uri.strip():
                image_uri = self._validate_remote_uri(image_uri, "Reference image URI")
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": image_uri},
                        "role": "reference_image",
                    }
                )
            content.append(
                {
                    "type": "video_url",
                    "video_url": {"url": video_uri},
                    "role": "reference_video",
                }
            )

        payload: dict[str, Any] = {
            "model": settings.model,
            "content": content,
            "generate_audio": generate_audio,
            "watermark": watermark,
        }

        if mode == "edit":
            payload["ratio"] = "adaptive"
            payload["duration"] = -1
        else:
            payload["ratio"] = ratio
            payload["duration"] = int(duration)

        response = self.session.post(
            f"{settings.base_url}/contents/generations/tasks",
            json=payload,
            timeout=60,
        )
        self._raise_for_api_error(response)
        data = response.json()
        task_id = data.get("id") or data.get("task_id")
        if not task_id:
            raise SeedanceError(f"Task was created but no task id was returned: {data}")
        return str(task_id)

    def get_task(self, task_id: str) -> dict[str, Any]:
        response = self.session.get(
            f"{settings.base_url}/contents/generations/tasks/{task_id}", timeout=60
        )
        self._raise_for_api_error(response)
        return response.json()

    def wait_for_task(
        self,
        task_id: str,
        on_status: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        started_at = time.monotonic()
        last_status = ""

        while True:
            data = self.get_task(task_id)
            status = str(data.get("status", "unknown")).lower()

            if on_status and status != last_status:
                on_status(status, data)
                last_status = status

            if status in {"succeeded", "success", "completed"}:
                return data
            if status in {"failed", "cancelled", "canceled"}:
                error = data.get("error") or data.get("message") or data
                raise SeedanceError(f"Generation failed: {error}")
            if time.monotonic() - started_at > settings.task_timeout_seconds:
                raise SeedanceError(
                    f"Timed out after {settings.task_timeout_seconds} seconds. Task id: {task_id}"
                )

            time.sleep(settings.poll_interval_seconds)

    @staticmethod
    def find_video_url(data: Any) -> str | None:
        if isinstance(data, dict):
            for key, value in data.items():
                if key in {"video_url", "url"} and isinstance(value, str):
                    lower = value.lower()
                    if value.startswith("http") and (
                        ".mp4" in lower or ".mov" in lower or "video" in lower
                    ):
                        return value
            for value in data.values():
                found = SeedanceClient.find_video_url(value)
                if found:
                    return found
        elif isinstance(data, list):
            for item in data:
                found = SeedanceClient.find_video_url(item)
                if found:
                    return found
        return None

    def download_video(self, url: str, task_id: str) -> Path:
        suffix = ".mov" if ".mov" in url.lower() else ".mp4"
        target = settings.outputs_dir / f"{task_id}-{uuid.uuid4().hex[:8]}{suffix}"
        with requests.get(url, stream=True, timeout=120) as response:
            response.raise_for_status()
            with target.open("wb") as fp:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        fp.write(chunk)
        return target

    @staticmethod
    def dump_response(data: dict[str, Any], task_id: str) -> Path:
        path = settings.data_dir / f"{task_id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    @staticmethod
    def _raise_for_api_error(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise SeedanceError(
            f"Volcengine Ark API returned HTTP {response.status_code}: {detail}"
        )

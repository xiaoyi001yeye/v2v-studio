from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from v2v_studio.seedance import SeedanceClient, SeedanceError

app = FastAPI(title="V2V Studio API")


class CreateTaskRequest(BaseModel):
    mode: Literal["edit", "reference"] = "edit"
    video_uri: str = Field(min_length=1)
    image_uri: str | None = None
    prompt: str = Field(min_length=1)
    ratio: str = "16:9"
    duration: int = 10
    generate_audio: bool = True
    watermark: bool = False


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/create")
def create_task(body: CreateTaskRequest):
    try:
        client = SeedanceClient()
        task_id = client.create_task(
            prompt=body.prompt,
            video_uri=body.video_uri,
            image_uri=body.image_uri,
            mode=body.mode,
            ratio=body.ratio,
            duration=body.duration,
            generate_audio=body.generate_audio,
            watermark=body.watermark,
        )
        return {"task_id": task_id}
    except SeedanceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}") from exc


@app.get("/api/status/{task_id}")
def get_status(task_id: str):
    try:
        client = SeedanceClient()
        data = client.get_task(task_id)
        status = str(data.get("status", "unknown")).lower()
        video_url = client.find_video_url(data) if status in {"succeeded", "success", "completed"} else None
        return {
            "task_id": task_id,
            "status": status,
            "video_url": video_url,
            "error": data.get("error"),
        }
    except SeedanceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}") from exc

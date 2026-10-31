from __future__ import annotations
import os, secrets, shutil, tempfile, threading, uuid
from pathlib import Path
from typing import Any
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from split_text import split_text
from generate_audio import generate
import asyncio
import subprocess

app = FastAPI(title="Vietnamese Long Audio TTS", version="1.0.0")
ROOT = Path(os.getenv("TTS_DATA_DIR", "/tmp/vn-long-tts"))
ROOT.mkdir(parents=True, exist_ok=True)
API_KEY = os.getenv("TTS_API_KEY", "")
JOBS: dict[str, dict[str, Any]] = {}
LOCK = threading.Lock()

class SynthesisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1_000_000)
    voice: str = "Nam Minh"
    rate: float = Field(default=1.0, ge=0.5, le=2.0)
    chunk_chars: int = Field(default=2800, ge=500, le=5000)
    attempts: int = Field(default=3, ge=1, le=5)

def authorize(value: str | None) -> None:
    if not API_KEY:
        raise HTTPException(503, "Server chưa cấu hình TTS_API_KEY.")
    if not value or not secrets.compare_digest(value, API_KEY):
        raise HTTPException(401, "API key không hợp lệ.")

def run_job(job_id: str, req: SynthesisRequest) -> None:
    folder = ROOT / job_id
    try:
        folder.mkdir(parents=True, exist_ok=True)
        chunks = split_text(req.text, req.chunk_chars)
        JOBS[job_id].update(status="processing", total=len(chunks), completed=0)
        parts=[]
        for i, chunk in enumerate(chunks, 1):
            source=folder / f"part_{i:05d}.txt"
            output=folder / f"part_{i:05d}.mp3"
            source.write_text(chunk, encoding="utf-8")
            asyncio.run(generate(chunk, req.voice, str(req.rate), output, req.attempts))
            parts.append(output)
            JOBS[job_id]["completed"]=i
        # Concatenate MP3 streams in order. Each part is encoded with identical settings.
        final=folder / "audio.mp3"
        with final.open("wb") as dst:
            for part in parts:
                with part.open("rb") as src:
                    shutil.copyfileobj(src, dst)
        JOBS[job_id].update(status="completed", filename=str(final), size=final.stat().st_size)
    except Exception as exc:
        JOBS[job_id].update(status="failed", error=f"{type(exc).__name__}: {exc}")

@app.get("/health")
def health():
    return {"ok": True, "service": "Vietnamese Long Audio TTS"}

@app.post("/v1/jobs", status_code=202)
def create_job(req: SynthesisRequest, x_api_key: str | None = Header(default=None)):
    authorize(x_api_key)
    if req.voice not in ("Nam Minh", "Hoài My", "vi-VN-NamMinhNeural", "vi-VN-HoaiMyNeural"):
        raise HTTPException(422, "voice phải là Nam Minh hoặc Hoài My.")
    job_id=uuid.uuid4().hex
    JOBS[job_id]={"id":job_id, "status":"queued", "completed":0, "total":0}
    threading.Thread(target=run_job, args=(job_id, req), daemon=True).start()
    return {"job_id":job_id, "status":"queued", "status_url":f"/v1/jobs/{job_id}", "audio_url":f"/v1/jobs/{job_id}/audio"}

@app.get("/v1/jobs/{job_id}")
def job_status(job_id: str, x_api_key: str | None = Header(default=None)):
    authorize(x_api_key)
    job=JOBS.get(job_id)
    if not job: raise HTTPException(404, "Không tìm thấy job.")
    return {k:v for k,v in job.items() if k not in ("filename",)}

@app.get("/v1/jobs/{job_id}/audio")
def download_audio(job_id: str, x_api_key: str | None = Header(default=None)):
    authorize(x_api_key)
    job=JOBS.get(job_id)
    if not job: raise HTTPException(404, "Không tìm thấy job.")
    if job["status"] != "completed": raise HTTPException(409, f"Job chưa hoàn tất: {job['status']}")
    path=Path(job["filename"])
    return FileResponse(path, media_type="audio/mpeg", filename=f"{job_id}.mp3")

"""HTTP backend for the WattWise frontend.

Run from the repo root:
    uvicorn api.server:app --port 8000

Endpoints:
    GET    /api/health                 Ollama reachable and model available?
    POST   /api/chat                   form fields: message, session_id (optional), image (optional file)
                                       -> {session_id, answer, trace, seconds, error}
    DELETE /api/sessions/{session_id}  forget a conversation and delete its uploaded photos

A bill check takes a few minutes on CPU, so the frontend should show a loading state and
not time out early. Questions are answered one at a time (one model, limited RAM).
"""

import asyncio
import json
import os
import shutil
import urllib.request
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from api.session import ROOT, Session

load_dotenv(ROOT / ".env")
MODEL = os.getenv("MAIN_MODEL")
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
UPLOAD_DIR = ROOT / "runs" / "uploads"  # runs/ is gitignored; bill photos hold personal data
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
# Comma-separated list of frontend origins, e.g. "http://localhost:3000,https://wattwise.vercel.app"
ORIGINS = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if o.strip()]

app = FastAPI(title="WattWise API")
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["*"], allow_headers=["*"])

sessions: dict[str, Session] = {}
model_lock = asyncio.Lock()


def new_session() -> Session:
    return Session(model=MODEL)


def ollama_models() -> list[str]:
    with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as response:
        return [m["name"] for m in json.loads(response.read())["models"]]


@app.get("/api/health")
def health() -> dict:
    try:
        models = ollama_models()
    except Exception as exc:
        return {"ok": False, "model": MODEL, "error": f"Ollama not reachable at {OLLAMA_URL}: {exc}"}
    available = MODEL in models or f"{MODEL}:latest" in models
    return {"ok": available, "model": MODEL, "error": None if available else f"Model {MODEL} not found in Ollama."}


async def save_upload(image: UploadFile, session_id: str) -> Path:
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Bill photo must be a JPEG, PNG or WebP image.")
    data = await image.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Bill photo is larger than 15 MB.")
    folder = UPLOAD_DIR / session_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex}{ALLOWED_TYPES[image.content_type]}"
    path.write_bytes(data)
    try:
        with Image.open(path) as img:
            img.verify()
    except Exception:
        path.unlink(missing_ok=True)
        raise HTTPException(400, "The uploaded file is not a readable image.")
    return path


@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    session_id: str | None = Form(None),
    image: UploadFile | None = File(None),
) -> dict:
    message = message.strip()
    if not message:
        raise HTTPException(400, "Message is empty.")
    if session_id and session_id not in sessions:
        raise HTTPException(404, "Unknown session_id. Start a new conversation without one.")
    session_id = session_id or uuid.uuid4().hex
    session = sessions.setdefault(session_id, new_session())
    path = await save_upload(image, session_id) if image is not None and image.filename else None

    async with model_lock:
        result = await session.ask(message, path)
    return {"session_id": session_id, **result}


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str) -> dict:
    if sessions.pop(session_id, None) is None:
        raise HTTPException(404, "Unknown session_id.")
    shutil.rmtree(UPLOAD_DIR / session_id, ignore_errors=True)
    return {"deleted": session_id}

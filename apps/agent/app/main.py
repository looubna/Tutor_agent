import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

from app.agent import respond  # noqa: E402  (must load env before importing agent)

app = FastAPI(title="Learnora Tutor Agent")

web_origin = os.environ.get("WEB_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[web_origin],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class Turn(BaseModel):
    role: Literal["student", "tutor"]
    content: str


class RespondRequest(BaseModel):
    subject: str = "Math"
    history: list[Turn]


class RespondResponse(BaseModel):
    reply: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/agent/respond", response_model=RespondResponse)
async def agent_respond(body: RespondRequest):
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured on the server.")
    if not body.history or body.history[-1].role != "student":
        raise HTTPException(status_code=400, detail="history must end with a student turn.")

    history = [turn.model_dump() for turn in body.history]
    try:
        reply = await respond(body.subject, history)
    except Exception as exc:  # surfaced to the caller as a 502, not silently swallowed
        raise HTTPException(status_code=502, detail=f"Agent failed to respond: {exc}") from exc

    if not reply:
        raise HTTPException(status_code=502, detail="Agent returned an empty reply.")

    return RespondResponse(reply=reply)

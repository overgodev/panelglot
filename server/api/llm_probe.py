"""Probe/warm-up/unload helpers for user-configured custom_openai endpoints
(LM Studio, headless Ollama, or any other OpenAI-compatible local server).

These exist because the browser can't reliably reach an arbitrary LAN host
itself (mixed content / CORS on servers that don't set permissive headers),
so the frontend asks this server to do it instead. None of this talks to
the translation pipeline - it only talks to the LLM server the user pointed
their endpoint at, to answer "does this exist", "what models does it have",
"warm this model up", and (Ollama only) "unload this model".
"""
import time
from typing import List, Optional

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


def _headers(api_key: Optional[str]) -> dict:
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def _native_root(base_url: str) -> str:
    base = base_url.rstrip("/")
    return base[: -len("/v1")] if base.endswith("/v1") else base


def _openai_base(base_url: str) -> str:
    base = base_url.rstrip("/")
    return base if base.endswith("/v1") else f"{base}/v1"


class ProbeRequest(BaseModel):
    base_url: str
    api_key: Optional[str] = None


class ProbeResponse(BaseModel):
    ok: bool
    server_type: str = "unknown"  # "ollama" | "openai-compatible" | "unknown"
    models: List[str] = []
    error: Optional[str] = None


@router.post("/api/llm/probe", response_model=ProbeResponse, tags=["api", "llm"])
async def probe_endpoint(data: ProbeRequest) -> ProbeResponse:
    headers = _headers(data.api_key)
    async with httpx.AsyncClient(timeout=8.0) as client:
        # Only Ollama exposes /api/tags - try it first so we can offer unload later.
        try:
            r = await client.get(f"{_native_root(data.base_url)}/api/tags", headers=headers)
            if r.status_code == 200:
                models = [m.get("name") for m in r.json().get("models", []) if m.get("name")]
                if models:
                    return ProbeResponse(ok=True, server_type="ollama", models=models)
        except httpx.HTTPError:
            pass

        # Fall back to the OpenAI-compatible /models listing (LM Studio, Ollama's own
        # compat layer, or anything else speaking the same API).
        try:
            r = await client.get(f"{_openai_base(data.base_url)}/models", headers=headers)
            r.raise_for_status()
            models = [m.get("id") for m in r.json().get("data", []) if m.get("id")]
            return ProbeResponse(ok=True, server_type="openai-compatible", models=models)
        except httpx.HTTPError as e:
            return ProbeResponse(ok=False, error=str(e))


class WarmupRequest(BaseModel):
    base_url: str
    api_key: Optional[str] = None
    model: str


class WarmupResponse(BaseModel):
    ok: bool
    latency_ms: Optional[int] = None
    error: Optional[str] = None


@router.post("/api/llm/warmup", response_model=WarmupResponse, tags=["api", "llm"])
async def warmup_endpoint(data: WarmupRequest) -> WarmupResponse:
    headers = {**_headers(data.api_key), "Content-Type": "application/json"}
    body = {"model": data.model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}
    started = time.monotonic()
    # A cold model load (first request after switching) can genuinely take a while on a big
    # model that has to page in from disk - give it much longer than a normal request timeout.
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            r = await client.post(f"{_openai_base(data.base_url)}/chat/completions", headers=headers, json=body)
            r.raise_for_status()
            return WarmupResponse(ok=True, latency_ms=int((time.monotonic() - started) * 1000))
        except httpx.HTTPError as e:
            return WarmupResponse(ok=False, error=str(e))


class UnloadRequest(BaseModel):
    base_url: str
    model: str
    server_type: str


class UnloadResponse(BaseModel):
    ok: bool
    message: Optional[str] = None


@router.post("/api/llm/unload", response_model=UnloadResponse, tags=["api", "llm"])
async def unload_endpoint(data: UnloadRequest) -> UnloadResponse:
    if data.server_type != "ollama":
        # LM Studio and other bare OpenAI-compatible servers have no standard remote-unload
        # API; the old model just sits until the server evicts it itself. Say so rather than
        # pretending this did something.
        return UnloadResponse(
            ok=False,
            message="This server type has no remote unload API - the previous model stays "
            "loaded until the server evicts it itself.",
        )
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            r = await client.post(
                f"{_native_root(data.base_url)}/api/generate",
                json={"model": data.model, "keep_alive": 0},
            )
            r.raise_for_status()
            return UnloadResponse(ok=True)
        except httpx.HTTPError as e:
            return UnloadResponse(ok=False, message=str(e))

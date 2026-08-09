from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from backend.app.providers.base import ProviderError
from backend.app.providers.soniox_provider import SonioxProvider


def _make_provider(handler, **kwargs) -> SonioxProvider:
    return SonioxProvider(
        api_key="test-key",
        base_url="https://api.soniox.com",
        model="stt-async-v5",
        timeout_seconds=5,
        poll_interval_seconds=0.0,
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


def test_transcribe_audio_happy_path() -> None:
    calls: list[str] = []
    poll_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        key = f"{request.method} {request.url.path}"
        calls.append(key)
        assert request.headers["Authorization"] == "Bearer test-key"
        if key == "POST /v1/files":
            return httpx.Response(200, json={"id": "file-1"})
        if key == "POST /v1/transcriptions":
            body = json.loads(request.content)
            assert body == {"model": "stt-async-v5", "file_id": "file-1"}
            return httpx.Response(200, json={"id": "tr-1", "status": "queued"})
        if key == "GET /v1/transcriptions/tr-1":
            poll_count["n"] += 1
            status = "processing" if poll_count["n"] == 1 else "completed"
            return httpx.Response(200, json={"id": "tr-1", "status": status})
        if key == "GET /v1/transcriptions/tr-1/transcript":
            return httpx.Response(
                200,
                json={"id": "tr-1", "tokens": [{"text": "hello "}, {"text": "world"}]},
            )
        if request.method == "DELETE":
            return httpx.Response(200, json={})
        return httpx.Response(404, json={"error": f"unexpected {key}"})

    provider = _make_provider(handler)
    result = asyncio.run(provider.transcribe_audio("audio/m4a", b"fake-audio"))

    assert result == "hello world"
    assert calls[0] == "POST /v1/files"
    assert calls[1] == "POST /v1/transcriptions"
    assert "GET /v1/transcriptions/tr-1/transcript" in calls
    # best-effort cleanup was attempted
    assert "DELETE /v1/transcriptions/tr-1" in calls
    assert "DELETE /v1/files/file-1" in calls


def test_transcribe_audio_error_status_raises_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        key = f"{request.method} {request.url.path}"
        if key == "POST /v1/files":
            return httpx.Response(200, json={"id": "file-1"})
        if key == "POST /v1/transcriptions":
            return httpx.Response(200, json={"id": "tr-1", "status": "queued"})
        if key == "GET /v1/transcriptions/tr-1":
            return httpx.Response(200, json={"id": "tr-1", "status": "error", "error_message": "bad audio"})
        if request.method == "DELETE":
            return httpx.Response(200, json={})
        return httpx.Response(404, json={})

    provider = _make_provider(handler)
    with pytest.raises(ProviderError, match="bad audio"):
        asyncio.run(provider.transcribe_audio("audio/m4a", b"fake-audio"))


def test_transcribe_audio_upload_http_error_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            return httpx.Response(200, json={})
        return httpx.Response(500, text="boom")

    provider = _make_provider(handler)
    with pytest.raises(ProviderError, match="file upload failed"):
        asyncio.run(provider.transcribe_audio("audio/m4a", b"fake-audio"))


def test_missing_api_key_raises_auth_failed() -> None:
    provider = SonioxProvider(api_key="")
    with pytest.raises(ProviderError) as exc_info:
        asyncio.run(provider.transcribe_audio("audio/m4a", b"x"))
    assert exc_info.value.code == "AUTH_FAILED"


def test_soniox_is_asr_only() -> None:
    provider = SonioxProvider(api_key="test-key")
    with pytest.raises(ProviderError):
        asyncio.run(provider.analyze_text("p", "t"))
    with pytest.raises(ProviderError):
        asyncio.run(provider.analyze_multimodal("p", "image/png", b"x"))

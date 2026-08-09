from __future__ import annotations

import asyncio
import json
from datetime import datetime

import httpx

from backend.app.sync.transcribe_hub_adapter import forward_to_transcribe_hub


def test_no_call_without_transcribe_hub_url(monkeypatch) -> None:
    monkeypatch.delenv("TRANSCRIBE_HUB_URL", raising=False)

    def _fail_client(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("httpx.AsyncClient must not be created when hub is disabled")

    monkeypatch.setattr(httpx, "AsyncClient", _fail_client)

    result = asyncio.run(
        forward_to_transcribe_hub(
            capture_id="abc123",
            media_type="audio",
            mime_type="audio/m4a",
            transcript="hello world",
            locale="en-US",
            captured_at=datetime(2026, 8, 10, 9, 30),
        )
    )
    assert result is None


def test_forward_posts_expected_payload_when_enabled() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True})

    result = asyncio.run(
        forward_to_transcribe_hub(
            capture_id="abc123",
            media_type="audio",
            mime_type="audio/m4a",
            transcript="hello world",
            locale="en-US",
            captured_at=datetime(2026, 8, 10, 9, 30),
            hub_url="http://hub.test/ingest",
            transport=httpx.MockTransport(handler),
        )
    )

    assert result is not None
    assert result.success is True
    assert result.channel == "transcribe_hub"
    assert seen["url"] == "http://hub.test/ingest"
    assert seen["payload"] == {
        "source": "auracap",
        "capture_id": "abc123",
        "media_type": "audio",
        "mime_type": "audio/m4a",
        "transcript": "hello world",
        "locale": "en-US",
        "captured_at": "2026-08-10T09:30:00",
    }

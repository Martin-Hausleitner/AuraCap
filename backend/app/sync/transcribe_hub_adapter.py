from __future__ import annotations

import logging
import os
from datetime import datetime

import httpx

from backend.app.models.schemas import DeliveryResult

logger = logging.getLogger(__name__)

CHANNEL = "transcribe_hub"


def transcribe_hub_url() -> str:
    """Hub endpoint from env; empty string means the hook is disabled (default)."""
    return os.environ.get("TRANSCRIBE_HUB_URL", "").strip()


async def forward_to_transcribe_hub(
    *,
    capture_id: str,
    media_type: str,
    mime_type: str,
    transcript: str,
    locale: str,
    captured_at: datetime | None,
    hub_url: str | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> DeliveryResult | None:
    """Stub hook towards the vcvm diarization pipeline (transcribe-hub).

    Disabled by default: when TRANSCRIBE_HUB_URL is not set, NO external call is
    made and None is returned. Failures never raise — the capture pipeline must
    not break because of this optional fan-out. Payload schema is documented in
    docs/TRANSCRIBE_HUB.md.
    """
    url = hub_url if hub_url is not None else transcribe_hub_url()
    if not url:
        return None

    payload = {
        "source": "auracap",
        "capture_id": capture_id,
        "media_type": media_type,
        "mime_type": mime_type,
        "transcript": transcript,
        "locale": locale,
        "captured_at": captured_at.isoformat() if captured_at else None,
    }
    try:
        client_kwargs: dict = {"timeout": 20}
        if transport is not None:
            client_kwargs["transport"] = transport
        async with httpx.AsyncClient(**client_kwargs) as client:
            resp = await client.post(url, json=payload)
        ok = resp.status_code < 400
        return DeliveryResult(channel=CHANNEL, success=ok, detail=f"status={resp.status_code}")
    except httpx.HTTPError as exc:
        logger.warning("transcribe_hub_forward_failed", extra={"extra": {"detail": str(exc)}})
        return DeliveryResult(channel=CHANNEL, success=False, detail=str(exc))

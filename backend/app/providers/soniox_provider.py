from __future__ import annotations

import asyncio
import time

import httpx

from backend.app.providers.base import BaseProvider, ProviderError

# Soniox async STT REST API (verified 2026-08-10 via
# https://soniox.com/docs/stt/async/async-transcription):
#   POST   /v1/files                          multipart field "file"            -> {"id": ...}
#   POST   /v1/transcriptions                 {"model": ..., "file_id": ...}    -> {"id": ...}
#   GET    /v1/transcriptions/{id}            -> {"status": "queued"|"processing"|"completed"|"error", ...}
#   GET    /v1/transcriptions/{id}/transcript -> {"text": ..., "tokens": [{"text": ...}, ...]}
#   DELETE /v1/transcriptions/{id} and DELETE /v1/files/{id} (cleanup)
# Auth: "Authorization: Bearer <SONIOX_API_KEY>"

_MIME_EXT = {
    "audio/m4a": "m4a",
    "audio/mp4": "m4a",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
}

_TERMINAL_ERROR_STATUSES = {"error", "failed"}


class SonioxProvider(BaseProvider):
    """ASR-only provider using the Soniox async REST API.

    analyze_text / analyze_multimodal are intentionally unsupported (route those
    to a text/mm provider); only transcribe_audio is implemented.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.soniox.com",
        model: str = "stt-async-v5",
        timeout_seconds: int = 120,
        poll_interval_seconds: float = 2.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ProviderError("Soniox API key not configured", "AUTH_FAILED")
        return {"Authorization": f"Bearer {self.api_key}"}

    async def analyze_text(self, prompt: str, text: str) -> str:
        raise ProviderError("Soniox is ASR-only, switch text_provider", "PROVIDER_UNAVAILABLE")

    async def analyze_multimodal(self, prompt: str, mime_type: str, payload: bytes) -> str:
        raise ProviderError("Soniox is ASR-only, switch mm_provider", "PROVIDER_UNAVAILABLE")

    async def transcribe_audio(self, mime_type: str, payload: bytes) -> str:
        headers = self._headers()
        client_kwargs: dict = {
            "base_url": self.base_url,
            "headers": headers,
            "timeout": self.timeout_seconds,
        }
        if self.transport is not None:
            client_kwargs["transport"] = self.transport

        file_id: str | None = None
        transcription_id: str | None = None
        async with httpx.AsyncClient(**client_kwargs) as client:
            try:
                file_id = await self._upload_file(client, mime_type, payload)
                transcription_id = await self._create_transcription(client, file_id)
                await self._wait_for_completion(client, transcription_id)
                return await self._fetch_transcript(client, transcription_id)
            finally:
                await self._cleanup(client, transcription_id, file_id)

    async def _request(self, client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response:
        """Single defensive retry on transient transport errors."""
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                return await client.request(method, url, **kwargs)
            except httpx.TransportError as exc:  # network hiccup: retry once
                last_exc = exc
                if attempt == 0:
                    await asyncio.sleep(0.5)
        raise ProviderError(f"Soniox request failed: {last_exc}", "PROVIDER_UNAVAILABLE")

    async def _upload_file(self, client: httpx.AsyncClient, mime_type: str, payload: bytes) -> str:
        ext = _MIME_EXT.get(mime_type.lower(), "bin")
        r = await self._request(
            client,
            "POST",
            "/v1/files",
            files={"file": (f"audio.{ext}", payload, mime_type)},
        )
        if r.status_code >= 400:
            raise ProviderError(f"Soniox file upload failed: status={r.status_code} {r.text}")
        file_id = r.json().get("id")
        if not file_id:
            raise ProviderError("Soniox file upload returned no id")
        return str(file_id)

    async def _create_transcription(self, client: httpx.AsyncClient, file_id: str) -> str:
        r = await self._request(
            client,
            "POST",
            "/v1/transcriptions",
            json={"model": self.model, "file_id": file_id},
        )
        if r.status_code >= 400:
            raise ProviderError(f"Soniox create transcription failed: status={r.status_code} {r.text}")
        transcription_id = r.json().get("id")
        if not transcription_id:
            raise ProviderError("Soniox create transcription returned no id")
        return str(transcription_id)

    async def _wait_for_completion(self, client: httpx.AsyncClient, transcription_id: str) -> None:
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            r = await self._request(client, "GET", f"/v1/transcriptions/{transcription_id}")
            if r.status_code >= 400:
                raise ProviderError(f"Soniox poll failed: status={r.status_code} {r.text}")
            data = r.json()
            status = str(data.get("status", "")).lower()
            if status == "completed":
                return
            if status in _TERMINAL_ERROR_STATUSES:
                detail = data.get("error_message") or data.get("error") or "unknown error"
                raise ProviderError(f"Soniox transcription failed: {detail}")
            if time.monotonic() >= deadline:
                raise ProviderError(
                    f"Soniox transcription timed out after {self.timeout_seconds}s", "PROVIDER_TIMEOUT"
                )
            await asyncio.sleep(self.poll_interval_seconds)

    async def _fetch_transcript(self, client: httpx.AsyncClient, transcription_id: str) -> str:
        r = await self._request(client, "GET", f"/v1/transcriptions/{transcription_id}/transcript")
        if r.status_code >= 400:
            raise ProviderError(f"Soniox transcript fetch failed: status={r.status_code} {r.text}")
        data = r.json()
        text = data.get("text")
        if text:
            return str(text)
        tokens = data.get("tokens") or []
        return "".join(str(tok.get("text", "")) for tok in tokens).strip()

    async def _cleanup(
        self, client: httpx.AsyncClient, transcription_id: str | None, file_id: str | None
    ) -> None:
        """Best-effort cleanup of remote resources; never raises."""
        for method, url in (
            ("DELETE", f"/v1/transcriptions/{transcription_id}") if transcription_id else (None, None),
            ("DELETE", f"/v1/files/{file_id}") if file_id else (None, None),
        ):
            if not method:
                continue
            try:
                await client.request(method, url)
            except httpx.HTTPError:
                pass

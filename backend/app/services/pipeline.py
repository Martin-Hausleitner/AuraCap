from __future__ import annotations

import logging
from datetime import datetime

from backend.app.core.config import Settings
from backend.app.core.i18n import t
from backend.app.models.schemas import AudioMode, CaptureRequest, MediaType, ProcessResult, SyncEvent
from backend.app.providers.base import ProviderError
from backend.app.providers.factory import ProviderBundle
from backend.app.services.common import load_prompt
from backend.app.services.custom_operation import run_custom_operation
from backend.app.services.prompt_router import (
    detect_lang_from_screenshot,
    detect_lang_from_transcript,
    locale_to_lang,
    resolve_timeline_prompt,
)
from backend.app.services.sync_queue import enqueue as sync_enqueue
from backend.app.services.timeline import append_timeline
from backend.app.sync.transcribe_hub_adapter import forward_to_transcribe_hub

logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.providers = ProviderBundle(settings)

    async def _extract_content(self, request: CaptureRequest) -> tuple[str, str | None]:
        """Returns (extracted_content, transcript). transcript is only set on the ASR path."""
        fallback_prompt = "Extract concise structured facts, actions, and context from the input."

        if request.media_type == MediaType.SCREENSHOT:
            if self.settings.timeline_lang_mode == "content_detect":
                lang = await detect_lang_from_screenshot(
                    self.providers.mm,
                    request.mime_type,
                    request.payload_bytes,
                )
                if lang is None:
                    lang = locale_to_lang(request.locale)
            else:
                lang = locale_to_lang(request.locale)
            prompt_path = resolve_timeline_prompt(MediaType.SCREENSHOT, lang, self.settings)
            timeline_prompt = load_prompt(prompt_path, fallback_prompt)
            extracted = await self.providers.mm.analyze_multimodal(
                prompt=timeline_prompt,
                mime_type=request.mime_type,
                payload=request.payload_bytes,
            )
            return extracted, None

        audio_mode = AudioMode(self.settings.audio_mode)
        if audio_mode == AudioMode.TRANSCRIBE_THEN_ANALYZE:
            transcript = await self.providers.asr.transcribe_audio(request.mime_type, request.payload_bytes)
            if self.settings.timeline_lang_mode == "content_detect":
                lang = detect_lang_from_transcript(transcript)
            else:
                lang = locale_to_lang(request.locale)
            prompt_path = resolve_timeline_prompt(MediaType.AUDIO, lang, self.settings)
            timeline_prompt = load_prompt(prompt_path, fallback_prompt)
            extracted = await self.providers.text.analyze_text(prompt=timeline_prompt, text=transcript)
            return extracted, transcript

        # DIRECT_MULTIMODAL: always use request_locale
        lang = locale_to_lang(request.locale)
        prompt_path = resolve_timeline_prompt(MediaType.AUDIO, lang, self.settings)
        timeline_prompt = load_prompt(prompt_path, fallback_prompt)
        extracted = await self.providers.mm.analyze_multimodal(
            prompt=timeline_prompt,
            mime_type=request.mime_type,
            payload=request.payload_bytes,
        )
        return extracted, None

    async def process_capture(self, request: CaptureRequest) -> ProcessResult:
        request_id = datetime.now().astimezone().strftime("%Y%m%d%H%M%S%f")
        try:
            extracted, transcript = await self._extract_content(request)
            trace = {
                "transport_mode": request.transport_mode,
                "mime_type": request.mime_type,
                "payload_ref": request.payload_ref,
                "request_id": request_id,
            }
            if transcript is not None:
                trace["transcript"] = transcript
            entry = append_timeline(
                settings=self.settings,
                source=request.source,
                input_type=request.media_type,
                extracted_content=extracted,
                locale=request.locale,
                timezone=request.timezone,
                metadata=request.metadata,
                trace=trace,
                timestamp=request.captured_at,
            )

            customized_path = None
            if self.settings.enable_custom_operation and self.settings.custom_operation_mode == "ON_EACH_TRIGGER":
                customized_path = await run_custom_operation(
                    settings=self.settings,
                    provider=self.providers.text,
                    input_text=extracted,
                    suffix=entry.id,
                )

            sync_results = await sync_enqueue(
                self.settings,
                SyncEvent(
                    event_type="timeline",
                    title=f"{t('timeline_title', self.settings.output_locale)} {entry.timestamp_display}",
                    body=entry.extracted_content,
                    artifact_path=str(self.settings.timeline_file),
                ),
            )

            if transcript is not None:
                # Env-gated stub towards the vcvm diarization pipeline (transcribe-hub);
                # no-op unless TRANSCRIBE_HUB_URL is set. See docs/TRANSCRIBE_HUB.md.
                hub_result = await forward_to_transcribe_hub(
                    capture_id=entry.id,
                    media_type=request.media_type.value,
                    mime_type=request.mime_type,
                    transcript=transcript,
                    locale=request.locale,
                    captured_at=request.captured_at,
                )
                if hub_result is not None:
                    sync_results.append(hub_result.model_dump())

            return ProcessResult(
                request_id=request_id,
                timeline_path=str(self.settings.timeline_file),
                extracted_content=extracted,
                customized_path=customized_path,
                sync_results=sync_results,
                status="success",
            )
        except ProviderError as exc:
            logger.error("provider_error", extra={"extra": {"code": exc.code, "detail": str(exc)}})
            print(f"PROVIDER_ERROR: code={exc.code} detail={exc}")
            return ProcessResult(
                request_id=request_id,
                timeline_path=str(self.settings.timeline_file),
                extracted_content="",
                status="failed",
                error_code=exc.code,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("process_capture_failed")
            return ProcessResult(
                request_id=request_id,
                timeline_path=str(self.settings.timeline_file),
                extracted_content="",
                status="failed",
                error_code=str(exc),
            )

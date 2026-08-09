from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.providers.anthropic_provider import AnthropicProvider
from backend.app.providers.base import BaseProvider, MockProvider
from backend.app.providers.google_provider import GoogleProvider
from backend.app.providers.groq_provider import GroqProvider
from backend.app.providers.mistral_provider import MistralProvider
from backend.app.providers.openai_provider import OpenAIProvider
from backend.app.providers.soniox_provider import SonioxProvider


def build_provider(kind: str, settings: Settings) -> BaseProvider:
    if kind == "mock":
        return MockProvider()
    if kind == "openai":
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            text_model=settings.openai_text_model,
            mm_model=settings.openai_mm_model,
            asr_model=settings.openai_asr_model,
            timeout_seconds=settings.provider_timeout_seconds,
        )
    if kind == "anthropic":
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
            text_model=settings.anthropic_text_model,
            mm_model=settings.anthropic_mm_model,
            timeout_seconds=settings.provider_timeout_seconds,
        )
    if kind == "google":
        return GoogleProvider(
            api_key=settings.google_api_key,
            base_url=settings.google_base_url,
            text_model=settings.google_text_model,
            mm_model=settings.google_mm_model,
            asr_model=settings.google_asr_model,
            timeout_seconds=settings.provider_timeout_seconds,
        )
    if kind == "groq":
        return GroqProvider(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            text_model=settings.groq_text_model,
            mm_model=settings.groq_mm_model,
            asr_model=settings.groq_asr_model,
            timeout_seconds=settings.provider_timeout_seconds,
        )
    if kind == "mistral":
        return MistralProvider(
            api_key=settings.mistral_api_key,
            base_url=settings.mistral_base_url,
            text_model=settings.mistral_text_model,
            mm_model=settings.mistral_mm_model,
            asr_model=settings.mistral_asr_model,
            timeout_seconds=settings.provider_timeout_seconds,
        )
    if kind == "soniox":
        return SonioxProvider(
            api_key=settings.soniox_api_key,
            base_url=settings.soniox_base_url,
            model=settings.soniox_model,
            timeout_seconds=settings.provider_timeout_seconds,
        )
    return MockProvider()


class ProviderBundle:
    def __init__(self, settings: Settings) -> None:
        if settings.unified_provider:
            p = build_provider(settings.unified_provider, settings)
            self.text = self.mm = self.asr = p
        else:
            self.text = build_provider(settings.text_provider, settings)
            self.mm = build_provider(settings.mm_provider, settings)
            self.asr = build_provider(settings.asr_provider, settings)

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    app_name: str = "AuraCap"
    app_env: Literal["development", "staging", "production"] = "development"
    output_locale: str = "zh-CN"

    default_timezone: str = "local"
    timestamp_format: str = "%Y-%m-%d %H:%M:%S %Z"

    storage_root: Path = Path("storage")
    timeline_file: Path = Path("storage/timeline.md")
    insights_dir: Path = Path("storage/insights")
    summary_dir: Path = Path("storage/summary")
    customized_dir: Path = Path("storage/customized")

    prompts_dir: Path = Path("prompts")
    timeline_prompt_file: Path = Path("prompts/timeline_prompts.md")
    insights_prompt_file: Path = Path("prompts/insights_prompts.md")
    summary_prompt_file: Path = Path("prompts/summary_prompts.md")
    customized_prompt_file: Path = Path("prompts/customized_prompts.md")
    tagging_prompt_file: Path = Path("prompts/tagging_prompts.md")

    task_index_dir: Path = Path("storage/task_index")
    entry_tags_file: Path = Path("storage/entry_tags.json")
    task_index_top_n: int = 3

    extract_only: bool = False
    enable_scheduler: bool = True
    force_scheduled_tasks: bool = False
    enable_insights: bool = True
    enable_summary: bool = True
    enable_task_index: bool = True
    enable_custom_operation: bool = False

    audio_mode: Literal["TRANSCRIBE_THEN_ANALYZE", "DIRECT_MULTIMODAL"] = "TRANSCRIBE_THEN_ANALYZE"

    timeline_lang_mode: Literal["content_detect", "request_locale"] = "request_locale"

    text_provider: Literal["openai", "anthropic", "google", "groq", "mistral", "mock"] = "mock"
    mm_provider: Literal["openai", "anthropic", "google", "groq", "mistral", "mock"] = "mock"
    asr_provider: Literal["openai", "google", "groq", "mistral", "soniox", "mock"] = "mock"
    unified_provider: Literal["", "openai", "google", "groq", "mistral", "mock"] = ""

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_text_model: str = "gpt-4.1-mini"
    openai_mm_model: str = "gpt-4.1-mini"
    openai_asr_model: str = "gpt-4o-mini-transcribe"

    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_text_model: str = "claude-3-7-sonnet-latest"
    anthropic_mm_model: str = "claude-3-7-sonnet-latest"

    google_api_key: str = ""
    google_base_url: str = "https://generativelanguage.googleapis.com"
    google_text_model: str = "gemini-2.0-flash"
    google_mm_model: str = "gemini-2.0-flash"
    google_asr_model: str = "gemini-2.0-flash"

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_text_model: str = "llama-3.3-70b-versatile"
    groq_mm_model: str = "llama-3.2-90b-vision-preview"
    groq_asr_model: str = "whisper-large-v3"

    mistral_api_key: str = ""
    mistral_base_url: str = "https://api.mistral.ai/v1"
    mistral_text_model: str = "mistral-large-latest"
    mistral_mm_model: str = "pixtral-large-latest"
    mistral_asr_model: str = "voxtral-mini-latest"

    soniox_api_key: str = ""
    soniox_base_url: str = "https://api.soniox.com"
    soniox_model: str = "stt-async-v5"

    provider_timeout_seconds: int = 120

    max_base64_chars: int = 2_000_000
    max_upload_mb: int = 25
    allowed_image_mime: str = "image/png,image/jpeg,image/heic"
    allowed_audio_mime: str = "audio/m4a,audio/mp4,audio/mpeg,audio/wav,audio/x-wav"

    insights_cron: str = "0 1 * * *"
    insights_target_day_offset: int = 1
    summary_cron: str = "0 2 * * 0"
    summary_window_days: int = 7

    custom_operation_mode: Literal["ON_EACH_TRIGGER", "CRON"] = "ON_EACH_TRIGGER"
    custom_operation_cron: str = "0 */6 * * *"

    sync_enable: bool = False
    sync_default_frequency: Literal["ON_EVENT", "DAILY", "CRON"] = "ON_EVENT"
    sync_default_cron: str = "0 9 * * *"

    sync_send_timeline: bool = True
    sync_send_insight: bool = False
    sync_send_summary: bool = True
    sync_send_customized: bool = False
    sync_send_errors: bool = True

    feishu_enabled: bool = False
    feishu_webhook_url: str = ""

    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    discord_enabled: bool = False
    discord_webhook_url: str = ""

    whatsapp_enabled: bool = False
    whatsapp_gateway_url: str = ""
    whatsapp_token: str = ""

    request_signature_secret: str = ""
    skip_signature_verification: bool = True

    github_dispatch_event_type: str = "auracap_ingest"
    github_release_inbox_tag: str = "auracap-inbox"
    github_release_delete_after_process: bool = True

    @field_validator("output_locale")
    @classmethod
    def validate_output_locale(cls, v: str) -> str:
        if v not in {"zh-CN", "en-US"}:
            raise ValueError("output_locale must be zh-CN or en-US")
        return v

    @field_validator("max_upload_mb")
    @classmethod
    def validate_upload_limit(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_upload_mb must be >= 1")
        return v

    @field_validator("insights_target_day_offset")
    @classmethod
    def validate_insights_target_day_offset(cls, v: int) -> int:
        if v < 0:
            raise ValueError("insights_target_day_offset must be >= 0")
        return v

    @field_validator("task_index_top_n")
    @classmethod
    def validate_task_index_top_n(cls, v: int) -> int:
        if v < 1:
            raise ValueError("task_index_top_n must be >= 1")
        return v


def _parse_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _env_to_fields(env: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in env.items():
        out[key.lower()] = value
    return out


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    dotenv = _parse_dotenv(Path(".env"))
    combined = dict(dotenv)
    combined.update({k: v for k, v in os.environ.items() if v is not None})
    settings = Settings(**_env_to_fields(combined))

    settings.storage_root.mkdir(parents=True, exist_ok=True)
    settings.insights_dir.mkdir(parents=True, exist_ok=True)
    settings.summary_dir.mkdir(parents=True, exist_ok=True)
    settings.customized_dir.mkdir(parents=True, exist_ok=True)
    settings.task_index_dir.mkdir(parents=True, exist_ok=True)
    settings.timeline_file.parent.mkdir(parents=True, exist_ok=True)
    settings.timeline_file.touch(exist_ok=True)
    return settings

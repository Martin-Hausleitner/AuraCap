# transcribe-hub Hook (vcvm Diarization Pipeline)

Env-gated stub that forwards finished audio transcripts from the AuraCap capture
pipeline to the **transcribe-hub** diarization pipeline on the vcvm
orchestration host ("Hans", Tailnet `100.120.120.120`).

## Status

**Stub.** Disabled by default. When `TRANSCRIBE_HUB_URL` is **not** set, no
external call is made and the pipeline behaves exactly as before.

## Activation

Set the env variable (locally in `.env`, or as an Actions variable/secret):

```
TRANSCRIBE_HUB_URL=http://100.120.120.120:<port>/ingest
```

When set, the pipeline POSTs one JSON payload per processed audio capture
(only on the `TRANSCRIBE_THEN_ANALYZE` ASR path, after the timeline entry is
written). Failures are logged and never break the capture pipeline.

## Code

- Adapter: `backend/app/sync/transcribe_hub_adapter.py`
  (`forward_to_transcribe_hub`)
- Fan-out call site: `backend/app/services/pipeline.py` (after sync enqueue,
  gated on a non-`None` transcript)

## Payload Schema

```json
{
  "source": "auracap",
  "capture_id": "<timeline entry id (32-hex)>",
  "media_type": "audio",
  "mime_type": "audio/m4a",
  "transcript": "<full ASR transcript text>",
  "locale": "en-US",
  "captured_at": "2026-08-10T09:30:00+02:00"
}
```

- `captured_at` is ISO-8601 or `null`.
- `transcript` is the raw ASR output (e.g. from the Soniox stage,
  `backend/app/providers/soniox_provider.py`), not the analyzed timeline text.

## TODO

- Real diarization integration on the vcvm side (transcribe-hub service):
  accept payload, run speaker diarization, write results back (webhook or
  repo commit) — endpoint contract to be finalized.
- Optional: forward the original audio asset URL alongside the transcript.
- Auth (bearer token) once the hub endpoint is exposed beyond the tailnet.

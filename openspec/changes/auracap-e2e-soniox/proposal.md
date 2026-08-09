# Proposal: AuraCap E2E auf Fork + Soniox-STT-Stufe + vcvm-Pipeline-Hook

## Why
AuraCap (iOS-Shortcuts → GitHub-Release-Assets → GitHub-Actions-AI → Timeline) soll auf Martins Fork produktiv laufen: echter E2E-Test vom iPhone 17 Pro, Audio-Transkription über eigenes Soniox-Konto (statt/zusätzlich zur Upstream-AI-Stufe), und ein dokumentierter Hook Richtung vcvm-Diarization-Pipeline (transcribe-hub).

## What Changes
- Fork `Martin-Hausleitner/AuraCap` mit aktivierten Actions + nötigen Secrets.
- Shortcut auf iPhone 17 Pro installiert (iPhone-Mirroring), E2E: echte Audio-Aufnahme → Release-Asset → Action → Timeline-Eintrag.
- Neue Soniox-STT-Stufe in der Action-Pipeline: Audio → Soniox-Transkript → Timeline (Key nur als GitHub-Secret `SONIOX_API_KEY`).
- Stub + Doku für Weiterleitung der Audio/Transkript-Ergebnisse an die vcvm-Diarization-Pipeline.
- Report `AURACAP-E2E-REPORT.md` mit Inline-Proofs in `.proof/`.

## Impact
- Affected specs: `capture-pipeline` (neu)
- Affected code: `scripts/process_github_dispatch.py` bzw. Workflow-Verarbeitungsstufe, `.github/workflows/*`, neues `backend/`/`scripts/`-Modul für Soniox, Doku.
- Keine Secrets im Repo; nur eigener Fork wird beschrieben.

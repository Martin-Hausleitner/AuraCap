# 📱 AuraCap E2E — iPhone-Shortcut + Soniox-STT + Pipeline-Andocken (Fable 5, Mac)
**Operator (2026-08-10, ~30-Min-Ziel):** AuraCap am iPhone starten, E2E testen, mit Soniox-STT ausstatten, an unsere Pipeline andocken.

## WAS AURACAP IST (F1-verifiziert aus README)
KEINE App! iOS-**Shortcuts** laden Screenshot/Audio in **GitHub-Release-Assets** hoch → **GitHub Actions** ziehen, AI-verarbeiten, schreiben Timeline. Fork = Deploy, 0 Kosten. Repo liegt lokal: ~/orca/workspaces/auracap

## ABLAUF
1. OpenSpec-first: openspec/changes/auracap-e2e-soniox/ (proposal+tasks+AK).
2. **Setup:** Fork nach Martin-Hausleitner (gh repo fork), Actions aktivieren, nötige Secrets/Token prüfen (README/docs lesen; shortcuts/-Ordner!). ⚠️ Actions-AI-Stufe: welche AI nutzt es? Auf OSS/eigene Keys umstellen wenn closed.
3. **iPhone:** Shortcut aufs iPhone 17 Pro bringen (iPhone-Mirroring.app am Mac + shortcuts-Datei via iCloud-Link/AirDrop). E2E: echte Audio-Aufnahme via Shortcut → Release → Action läuft → Timeline-Eintrag. Screenshot-Proofs in .proof/.
4. **Soniox-STT-Stufe:** in die Action-Pipeline (backend/) Soniox-STT einbauen (unsere route-lab-Erkenntnisse, eigener Key, read-only API-Muster) — Audio → Soniox-Transkript in Timeline.
5. **Pipeline andocken:** Ergebnis-Hook Richtung unserer vcvm-Diarization-Pipeline (transcribe-hub) dokumentieren + Stub bauen.
6. Report AURACAP-E2E-REPORT.md (Variant-A, Proofs inline) + committen.

## GUARDRAILS
⛔ Nichts senden/löschen extern außer eigenem Fork. Keine Secrets committen. Kein CAPTCHA/Bot-Bypass. Nur eigenes Soniox-Konto. F1: „fertig" nur mit echten Proof-Screenshots (Shortcut am iPhone + Timeline-Eintrag). iPhone-Aktionen via iPhone-Mirroring; wenn Interaktion nötig die nur Martin kann (iCloud-Login etc.) → als FRAGE stoppen.

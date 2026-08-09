# Tasks

## 1. Setup Fork
- [ ] 1.1 Fork nach Martin-Hausleitner, Actions aktiviert
- [ ] 1.2 Nötige Secrets/Variablen identifiziert (README/.env.example/Workflows) und im Fork gesetzt
- [ ] 1.3 Release-Inbox vorhanden (ensure_release_inbox)

## 2. iPhone E2E
- [ ] 2.1 Shortcut auf iPhone 17 Pro installiert (iPhone-Mirroring), konfiguriert (Repo/Token)
- [ ] 2.2 Echte Audio-Aufnahme via Shortcut hochgeladen → Release-Asset sichtbar
- [ ] 2.3 Action verarbeitet Asset → Timeline-Eintrag im Fork
- [ ] 2.4 Proof-Screenshots in `.proof/` (Shortcut am iPhone + Timeline-Eintrag)

## 3. Soniox-STT-Stufe
- [x] 3.1 Soniox-Client (async REST, route-lab-Muster) als Pipeline-Stufe
- [x] 3.2 Workflow nutzt `SONIOX_API_KEY`-Secret; Audio → Transkript → Timeline (Code fertig; Workflow-Env via `apply-workflow-soniox-env.sh` — direkte .github/workflows-Edits vom CI-Kill-Switch geblockt)
- [ ] 3.3 Lokaler Test der Stufe mit echter Audio-Datei

## 4. vcvm-Pipeline-Hook
- [x] 4.1 Hook Richtung transcribe-hub (vcvm-Diarization) dokumentiert
- [x] 4.2 Stub implementiert (deaktiviert per Default, env-gated)

## 5. Report
- [ ] 5.1 AURACAP-E2E-REPORT.md (Variant-A, Inline-Proofs) committed + gepusht

# Spec Delta: capture-pipeline

## ADDED Requirements

### Requirement: E2E-Aufnahme vom iPhone landet als Timeline-Eintrag im Fork
Eine mit dem AuraCap-Shortcut am iPhone erstellte echte Audio-Aufnahme MUST als GitHub-Release-Asset im Fork ankommen und von der GitHub-Action zu einem Timeline-Eintrag verarbeitet werden.

#### Scenario: Echte Aufnahme wird verarbeitet
- **WHEN** der Operator am iPhone 17 Pro den AuraCap-Shortcut mit einer echten Audio-Aufnahme ausführt
- **THEN** erscheint das Audio als Asset im Release-Inbox-Release des Forks
- **AND** der Actions-Workflow läuft grün durch und schreibt einen neuen Timeline-Eintrag
- **AND** Screenshots (Shortcut am iPhone, Timeline-Eintrag) liegen als Proof in `.proof/`

### Requirement: Soniox-STT-Stufe transkribiert Audio
Die Pipeline MUST Audio-Assets über die Soniox-API (eigener Key, nur als GitHub-Secret `SONIOX_API_KEY`) transkribieren und das Transkript in den Timeline-Eintrag aufnehmen.

#### Scenario: Audio wird mit Soniox transkribiert
- **WHEN** ein Audio-Asset verarbeitet wird und `SONIOX_API_KEY` gesetzt ist
- **THEN** wird das Audio an die Soniox-STT-API übergeben und das Transkript im Timeline-Eintrag gespeichert
- **AND** der Key erscheint nirgends im Repo/Log

#### Scenario: Kein Soniox-Key gesetzt
- **WHEN** `SONIOX_API_KEY` fehlt
- **THEN** läuft die Pipeline wie bisher (Fallback auf bestehende Verarbeitung) ohne Fehler

### Requirement: Ergebnis-Hook Richtung vcvm-Diarization-Pipeline
Die Pipeline MUST einen dokumentierten, per Env-Variable aktivierbaren Stub besitzen, der Audio/Transkript-Ergebnisse an die vcvm-Diarization-Pipeline (transcribe-hub) weiterreichen kann.

#### Scenario: Hook deaktiviert per Default
- **WHEN** `TRANSCRIBE_HUB_URL` nicht gesetzt ist
- **THEN** wird kein externer Call gemacht und die Pipeline verhält sich unverändert

#### Scenario: Hook aktiviert
- **WHEN** `TRANSCRIBE_HUB_URL` gesetzt ist
- **THEN** wird ein JSON-Payload (Asset-URL, Transkript, Metadaten) an den Hub-Endpoint gesendet (Stub: dokumentiertes Schema)

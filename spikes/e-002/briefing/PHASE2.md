# Phase 2: Zusatzaufgabe N-1

Ergänze die Operation **`appointment.reschedule`** nach `common/V-1-aufgabenbeschreibung.md` §11.

- Parameter: `appointment_id`, `starts_at`, `ends_at`. Schreibend, Vorschau-fähig. Verlaufseintrag `appointment.reschedule`. Ereignis `appointment.rescheduled` mit denselben Empfängern wie bei `appointment.create`. Rückgängig über `history.undo` muss funktionieren.
- **Es dürfen keine weiteren Änderungen von Hand nötig sein**, damit die Operation in `GET /api/v1/operations`, in `GET /api/v1/ai/tools` und in den Typen der Frontend-Brücke erscheint (nach `make bridge`). Wenn doch, hat die Operationsbeschreibung aus Phase 1 eine Lücke; beschreibe sie im Protokoll.
- Prüfe mit `python3 common/acceptance/run_acceptance.py --phase 2` und führe Phase 1 weiter fehlerfrei aus (`--phase 1`).
- Committe, schreibe `PHASE-2-FERTIG` mit Zeit ins Protokoll, höre auf.

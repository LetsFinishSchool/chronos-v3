//! Adapter für die Nachbarsysteme von Chronos, ein Modul je Nachbarsystem.
//!
//! Zuständig für Identität (Keycloak: OIDC-Anmeldung, Token- und
//! Sitzungsprüfung, Heartbeat, Back-Channel-Logout; ADR-008), das KI-Gateway
//! (Client hinter `AiProvider`, Adapter „OpenAI-kompatibel“, Kostenerfassung;
//! ADR-006), die Ferien-Quelle (Abruf der Schulferien) und das Backup
//! (S3-kompatibler Objektspeicher, clientseitige Verschlüsselung). Je Adapter
//! gibt es eine Schnittstelle (Trait), damit Web, Worker und Tests ihn
//! austauschen können. Die Module kommen mit den jeweiligen Features.
//!
//! Nicht zuständig für Zustellkanäle (`chronos-channels`), Fachlogik und die
//! Entscheidung, wann ein Aufruf nötig ist (`chronos-domain`, `chronos-web`,
//! `chronos-worker`). Aufrufe aus `chronos-domain` gibt es nicht, und
//! `chronos-adapters` hängt weder von `chronos-channels`, `chronos-web`,
//! `chronos-worker` noch von `chronos-domain` ab.
//!
//! Crate-Zuschnitt: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

// Erlaubte Kanten aus dem Crate-Zuschnitt. Bis der erste Code sie nutzt, sind
// sie hier eingebunden, damit Cargo sie nicht als ungenutzt meldet.
use chronos_core as _;

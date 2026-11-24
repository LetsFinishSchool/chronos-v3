//! Zustellkanäle von Chronos.
//!
//! Zuständig für die Adapter der Zustellkanäle (Web Push, E-Mail über SMTP,
//! später Messenger) mit einer gemeinsamen Kanalschnittstelle und
//! kanalspezifischen Formaten und Grenzen, für die Rückmeldung des Ergebnisses
//! je Zustellversuch (zugestellt, vorübergehend oder dauerhaft fehlgeschlagen)
//! und für das Melden kostenverursachender Aufrufe über die Kostenerfassung aus
//! `chronos-core`.
//!
//! Nicht zuständig für die Entscheidung, wer wann über welchen Kanal
//! benachrichtigt wird, für Bündelung, Budget, Wiederholung und Protokoll
//! (`chronos-worker`), für das Erzeugen oder Lesen von Ereignissen, Fachlogik
//! und Datenbankzugriff am Rahmen vorbei sowie für andere Nachbarsysteme
//! (`chronos-adapters`).
//!
//! Crate-Zuschnitt: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

// Erlaubte Kanten aus dem Crate-Zuschnitt. Bis der erste Code sie nutzt, sind
// sie hier eingebunden, damit Cargo sie nicht als ungenutzt meldet.
use chronos_core as _;

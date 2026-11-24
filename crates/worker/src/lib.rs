//! Worker-Prozess von Chronos.
//!
//! Zuständig für das Abarbeiten der Outbox (`FOR UPDATE SKIP LOCKED`) mit
//! Verbrauchern je Ereignisart (K-003), für die Benachrichtigung (Empfänger,
//! Kanalwahl nach Einstellungen und Matrix, Bündelung, Budget beim Planen,
//! Wiederholung, Zustellprotokoll mit Auslöser, Erinnerungsplanung) und für
//! Zeitauslöser und Wartung (z. B. Sitzungs-Heartbeat, Bereinigung gelöschter
//! Objekte). Änderungen an Fachdaten laufen nur über Operationen mit der
//! Akteur-Art Regel, nie am Rahmen vorbei.
//!
//! Nicht zuständig für HTTP, Oberfläche und Sitzungen von Anfragen
//! (`chronos-web`), für kanalspezifischen Versandcode (`chronos-channels`) und
//! Code für Nachbarsysteme (`chronos-adapters`), deren Schnittstellen der
//! Worker nur aufruft, und für Fachregeln (`chronos-domain`): Der Worker
//! entscheidet, wann etwas geschieht, die Fachlogik, was.
//!
//! Crate-Zuschnitt: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

// Erlaubte Kanten aus dem Crate-Zuschnitt. Bis der erste Code sie nutzt, sind
// sie hier eingebunden, damit Cargo sie nicht als ungenutzt meldet.
use chronos_adapters as _;
use chronos_channels as _;
use chronos_core as _;

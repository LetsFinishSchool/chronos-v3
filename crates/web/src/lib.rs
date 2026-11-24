//! Web-Prozess von Chronos.
//!
//! Zuständig für den HTTP-Server (`POST /api/v1/operations/{name}`,
//! Stapelendpunkt, Operationsliste für Oberfläche und Frontend-Typen,
//! Abbildung von Fehlercodes auf HTTP, Korrelations-ID je Anfrage), die
//! Auslieferung der SPA und der Gastseite (ADR-007), die Sitzung als BFF mit
//! Back-Channel-Logout-Endpunkt und Gast-Cookie, den Kalender-Feed und den
//! KI-Assistenten, der ausschließlich Operationen aufruft und den KI-Adapter
//! aus `chronos-adapters` nutzt.
//!
//! Nicht zuständig für Fachlogik, Berechtigungsprüfung und direkten Zugriff
//! auf Fachdaten: `chronos-web` kennt `chronos-domain` nicht und ruft nur über
//! die Registrierung in `chronos-core`. Ebenfalls nicht zuständig für
//! Zustellkanäle und Zustellung (`chronos-channels`, `chronos-worker`) und
//! für Hintergrundarbeit ohne Anfrage (`chronos-worker`).
//!
//! Crate-Zuschnitt: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

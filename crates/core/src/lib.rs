//! Operationsschicht und gemeinsamer Rahmen von Chronos.
//!
//! Zuständig für die Operationsschicht (ADR-005): Operation-Trait, Registrierung
//! über `inventory`, Rahmen mit Transaktion, Geltungsbereich und
//! Berechtigungsprüfung, Verlauf, Outbox, Probelauf, Freigabe-Beleg und Stapel;
//! außerdem den geprüften Kontext, Akteur-Arten, Fehlercodes, gemeinsame Typen
//! für Ereignisse und Verlauf, Zeittypen (ADR-012), die Schnittstelle der
//! Kostenerfassung (K-005) und den Datenbankzugang für den Rahmen.
//!
//! Nicht zuständig für konkrete Fachlogik, Fachtabellen und Fachereignisse
//! (`chronos-domain`), HTTP, Sitzungen und Oberfläche (`chronos-web`),
//! Zustellkanäle (`chronos-channels`), Nachbarsysteme (`chronos-adapters`),
//! Zustellung und Zeitauslöser (`chronos-worker`). `chronos-core` hängt von
//! keinem anderen Workspace-Crate ab.
//!
//! Crate-Zuschnitt: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

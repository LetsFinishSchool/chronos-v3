//! Fachbereiche von Chronos.
//!
//! Zuständig für die Fachbereiche aus der Bausteinsicht (Teams und Mitglieder,
//! Termine, Serien und Veranstaltungen, Rückmeldung, Terminfindung, Labels,
//! Terminnachrichten, Zeitraumsregeln): Operationen als reine Fachlogik im
//! Rahmen aus `chronos-core`, einschließlich der Ableitung des Geltungsbereichs
//! und der zugehörigen SQL-Abfragen, Fachtabellen als Migrationen,
//! Anzeige-Operationen und das Erzeugen von Fachereignissen. Die
//! RRULE-Auswertung liegt isoliert in einem eigenen Modul (ADR-004).
//!
//! Nicht zuständig für die Berechtigungsprüfung selbst, die Steuerung der
//! Transaktion und das Schreiben von Verlauf oder Outbox (Rahmen in
//! `chronos-core`), für Zustellkanäle und Nachbarsysteme (`chronos-channels`,
//! `chronos-adapters`), HTTP und Zeitauslöser sowie für Verzweigungen nach
//! Terminart in Rückmeldung und Benachrichtigung (QA-003 b). Brauchen
//! Fachbereiche Daten aus einem Nachbarsystem, liegen sie in der Datenbank.
//!
//! Crate-Zuschnitt: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

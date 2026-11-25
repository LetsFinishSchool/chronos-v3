//! Operationsschicht und gemeinsamer Rahmen (Transaktion, Berechtigung, Verlauf, Outbox).
//!
//! Zuschnitt und erlaubte Abhängigkeiten: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

use sqlx as _;
use tokio as _;

---
title: Outbox-Abarbeitung liegt in core, nicht in worker
datum: 2026-11-27
betrifft: docs/arc42/05-bausteine/02-crate-zuschnitt.md
art: widerspruch
status: offen   # Mensch setzt: angenommen | abgelehnt | zurückgestellt
---

## Beobachtung
Kapitel 5 führt unter `chronos-worker` als zuständig: „Outbox abarbeiten (`FOR UPDATE SKIP LOCKED`), Verbraucher je Ereignisart“. Gleichzeitig erlaubt `deny.toml` (ADR-009, ADR-013) `sqlx` nur in `chronos-core`, `chronos-domain` und `chronos`; ein Worker mit eigenem SQL scheitert an `cargo deny check bans`. Beim Umsetzen von #102 liegen deshalb die SQL-Abarbeitung, das Trait `Consumer` und die Registry in `chronos-core` (`outbox.rs`, `consumer.rs`). Der Worker hält Schleife, Taktung, Stopp und die Verbraucher. Siehe `wiki/code/worker-und-outbox.md`.

## Vorschlag
In Kapitel 5 unter `chronos-core` zuständig ergänzen: „Zugriff auf die Outbox für den Worker (Lesen mit `FOR UPDATE SKIP LOCKED`, Markieren), Trait der Verbraucher.“ Unter `chronos-worker` die Zeile ändern in: „Outbox abarbeiten über den Zugriff aus `core`: Schleife, Taktung, geordneter Stopp, Verbraucher je Ereignisart.“

## Wirkung
Nur Text; Code und `deny.toml` stimmen bereits. Verbraucher bekommen keine Datenbankverbindung, Datenänderungen laufen über Operationen. Braucht #23 Schreibzugriffe in der Transaktion der Abarbeitung, ist das eine eigene Entscheidung.

## Entscheidung (Mensch)

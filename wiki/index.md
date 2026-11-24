# Wiki-Index

Agenten: zuerst hier lesen. Eine Zeile pro Seite, nach Typ gruppiert. Pflichtpflege bei jedem Ingest.

## Konzepte
- [Projektkontext chronos-v3](concepts/projektkontext-chronos-v3.md): Fork von chronos-root, Neuanfang, Datenübernahme als Hauptrandbedingung
- [arc42-Entwurf, Stand 2026-11-20](concepts/arc42-entwurf-stand.md): Was in arc42 steht, was offen ist, nächste Schritte
- [E-002 Spike-Ergebnisse](concepts/e-002-spike-ergebnisse.md): Messung und Bewertung TypeScript/Go/Rust, Lehren für Agentenläufe, Entwurf ADR-004 (Rust vorgeschlagen)
- [Folgeentscheidungen bei Rust](concepts/e-002-folgeentscheidungen-rust.md): E-004, E-005, E-008, E-009, E-016, Migration, K-007, Zeitbibliothek, Build: Optionen mit Vor-/Nachteilen und Rust-Folgen
- [Fluent-Prüfung](concepts/fluent-pflegestand-und-datetime.md): Pflegestand fluent-rs/@fluent/bundle, DATETIME (Server fehlt, Browser eingebaut), Weblate, Empfehlung zu ADR-010
- [Key Learnings und Eckpunkte](concepts/key-learnings-chronos-root.md): Warum Neuanfang, Zielgruppe Leitungsteams, Team-Modell, Ressourcenbudget

## Code
- *(noch leer)*

## Lektionen
- [Wissen nur im Wiki](lessons/wissen-nur-im-wiki.md): Kein Agenten-Gedächtnis, alles projektgebunden im Wiki

## Vorschläge an `docs/`
- [RA-008 Runde 6](proposals/2026-11-20-ra-008-offene-fragen-runde-6.md): angenommen und in docs/req42 übernommen
- [SC-001 ergänzen](proposals/2026-11-20-sc-001-kontext-ergaenzen.md): KI-Anbieter und Ferien-API fehlen im Kontext; QA-008 abgebrochener Satz (angenommen und übernommen)
- [FA-017 Verlauf überprüfen](proposals/2026-11-20-fa-017-verlauf-rueckgaengig.md): Offene Entscheidung, ob allgemeines Rückgängig nötig ist oder Soft-Delete genügt
- [Glossar occasion](proposals/2026-11-20-glossar-occasion.md): Veranstaltung = occasion (E-015)
- [M-005 Rollen/Einstellungen](proposals/2026-11-20-m-005-rollen-einstellungen-verwerfen.md): Migration verwirft Rollen und Einstellungen, Termine je Team dupliziert
- [RB-003 Limits je Umgebung](proposals/2026-11-20-rb-003-limits-je-umgebung.md): Budget je Umgebung statt gesamt, offen
- [Rückgängig Folgeänderungen](proposals/2026-11-20-rueckgaengig-folgeaenderungen.md): Alt/Neu-Texte in req42 und arc42 nach FA-017-Reduzierung, offen
- [KI-Anbieter nur EU](proposals/2026-11-23-ki-anbieter-eu.md): F-015 und SC-001 „Start mit Claude“ widerspricht ADR-006 (nur EU-Datenstandort, Gateway), angenommen und übernommen
- [DoD WCAG 2.2 AA](proposals/2026-11-24-dod-wcag-2-2-aa.md): Maßstab der Definition of Done (Task- und Feature-DoD), angenommen und übernommen

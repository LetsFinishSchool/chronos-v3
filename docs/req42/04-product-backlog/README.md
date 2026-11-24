---
title: Product Backlog
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
---

# Product Backlog

Der Product Backlog liegt in **GitHub-Issues** und nicht mehr in Dateien. Die Reihenfolge legt der Product Owner fest ([Roadmap](../11-roadmaps/README.md)). Details je Story entstehen just-in-time im Ticket (agile Vorgehensweise: nur so viel Detail, wie für Architektur und technische Entscheidungen nötig ist).

- [Ticket-Typen](ticket-typen.md): Epic, Feature, Story, Task, Struktur und Definition of Done.
- Alle Tickets nach Typ (Label, Hierarchie über Sub-Issues):
  [Epics](https://github.com/LetsFinishSchool/chronos-v3/issues?q=is%3Aissue+label%3Aepic),
  [Features](https://github.com/LetsFinishSchool/chronos-v3/issues?q=is%3Aissue+label%3Afeature),
  [Stories](https://github.com/LetsFinishSchool/chronos-v3/issues?q=is%3Aissue+label%3Astory),
  [Tasks](https://github.com/LetsFinishSchool/chronos-v3/issues?q=is%3Aissue+label%3Atask),
  [Optionen](https://github.com/LetsFinishSchool/chronos-v3/issues?q=is%3Aissue+label%3Aoption).
- Akzeptanzkriterien stehen in den Stories. Qualitäts- und Randbedingungen, die nur einzelne Stories betreffen, sind dort als Kriterium aufgeführt; die übrigen gelten über die Definition of Done.

## Zuordnung früherer Kennungen

Bis 2026-11-24 standen Features (`F-nnn`) und Anforderungen (`FA-nnn`, Akzeptanzkriterien) in Dateien in diesem Kapitel. Sie sind in Tickets überführt; die Dateien stehen in der Git-Historie. Kennungen in anderen Kapiteln (`F-nnn`, `FA-nnn`) lösen sich über diese Tabellen auf. Jede Story nennt ihre Herkunft („ehemals FA-nnn, Kriterium n“). **Ab hier ist GitHub maßgeblich**, die Tabellen werden nicht fortgeschrieben.

### Epics (Roadmap)

| Roadmap | Titel | Epic |
|---|---|---|
| RM-001 | Fundament mit Datenübernahme | [#1](https://github.com/LetsFinishSchool/chronos-v3/issues/1) |
| RM-002 | Zugang ohne Konto | [#2](https://github.com/LetsFinishSchool/chronos-v3/issues/2) |
| RM-003 | Terminfindung | [#3](https://github.com/LetsFinishSchool/chronos-v3/issues/3) |
| RM-004 | Veranstaltungen und Labels | [#4](https://github.com/LetsFinishSchool/chronos-v3/issues/4) |
| RM-005 | Kalender-Feed und Terminnachrichten | [#5](https://github.com/LetsFinishSchool/chronos-v3/issues/5) |
| RM-007 | Serientermine | [#6](https://github.com/LetsFinishSchool/chronos-v3/issues/6) |
| RM-008 | KI-Assistent und Zeitraumsregeln | [#7](https://github.com/LetsFinishSchool/chronos-v3/issues/7) |
| RM-006 | Messenger-Kanäle (Option, Feature ohne Epic) | [#91](https://github.com/LetsFinishSchool/chronos-v3/issues/91) |

### Features und Anforderungen

| Früher | Titel | Feature | Stories und Tasks |
|---|---|---|---|
| F-001 / FA-001 | Teams und Unter-Teams | [#8](https://github.com/LetsFinishSchool/chronos-v3/issues/8) | [#9](https://github.com/LetsFinishSchool/chronos-v3/issues/9), [#10](https://github.com/LetsFinishSchool/chronos-v3/issues/10), [#11](https://github.com/LetsFinishSchool/chronos-v3/issues/11), [#12](https://github.com/LetsFinishSchool/chronos-v3/issues/12) |
| F-002 / FA-002 | Mitglieder und Einladungslink | [#49](https://github.com/LetsFinishSchool/chronos-v3/issues/49) | [#50](https://github.com/LetsFinishSchool/chronos-v3/issues/50), [#51](https://github.com/LetsFinishSchool/chronos-v3/issues/51), [#52](https://github.com/LetsFinishSchool/chronos-v3/issues/52), [#53](https://github.com/LetsFinishSchool/chronos-v3/issues/53), [#54](https://github.com/LetsFinishSchool/chronos-v3/issues/54) |
| F-003 / FA-003 | Termine | [#13](https://github.com/LetsFinishSchool/chronos-v3/issues/13) | [#14](https://github.com/LetsFinishSchool/chronos-v3/issues/14), [#15](https://github.com/LetsFinishSchool/chronos-v3/issues/15), [#16](https://github.com/LetsFinishSchool/chronos-v3/issues/16) |
| F-004 / FA-004 | Veranstaltungen | [#62](https://github.com/LetsFinishSchool/chronos-v3/issues/62) | [#63](https://github.com/LetsFinishSchool/chronos-v3/issues/63), [#64](https://github.com/LetsFinishSchool/chronos-v3/issues/64), [#65](https://github.com/LetsFinishSchool/chronos-v3/issues/65) |
| F-005 / FA-005 | Rückmeldung (Zusage und Absage) | [#17](https://github.com/LetsFinishSchool/chronos-v3/issues/17) | [#18](https://github.com/LetsFinishSchool/chronos-v3/issues/18), [#19](https://github.com/LetsFinishSchool/chronos-v3/issues/19), [#20](https://github.com/LetsFinishSchool/chronos-v3/issues/20), [#21](https://github.com/LetsFinishSchool/chronos-v3/issues/21) |
| F-005 / FA-005 | Rückmeldung „zeitweise“ | [#55](https://github.com/LetsFinishSchool/chronos-v3/issues/55) | [#56](https://github.com/LetsFinishSchool/chronos-v3/issues/56) |
| F-006 / FA-006 | Terminfindung per Abstimmung | [#57](https://github.com/LetsFinishSchool/chronos-v3/issues/57) | [#58](https://github.com/LetsFinishSchool/chronos-v3/issues/58), [#59](https://github.com/LetsFinishSchool/chronos-v3/issues/59), [#60](https://github.com/LetsFinishSchool/chronos-v3/issues/60), [#61](https://github.com/LetsFinishSchool/chronos-v3/issues/61) |
| F-007 / FA-007 | Labels für Rollen und Aufgaben | [#66](https://github.com/LetsFinishSchool/chronos-v3/issues/66) | [#67](https://github.com/LetsFinishSchool/chronos-v3/issues/67), [#68](https://github.com/LetsFinishSchool/chronos-v3/issues/68) |
| F-008 / FA-008 | Benachrichtigungen (Web Push und E-Mail) | [#22](https://github.com/LetsFinishSchool/chronos-v3/issues/22) | [#23](https://github.com/LetsFinishSchool/chronos-v3/issues/23), [#24](https://github.com/LetsFinishSchool/chronos-v3/issues/24), [#25](https://github.com/LetsFinishSchool/chronos-v3/issues/25), [#26](https://github.com/LetsFinishSchool/chronos-v3/issues/26), [#27](https://github.com/LetsFinishSchool/chronos-v3/issues/27) |
| F-009 / FA-009 | Kalender-Feed (webcal) | [#69](https://github.com/LetsFinishSchool/chronos-v3/issues/69) | [#70](https://github.com/LetsFinishSchool/chronos-v3/issues/70), [#71](https://github.com/LetsFinishSchool/chronos-v3/issues/71) |
| F-010 / FA-010 | Terminnachrichten | [#72](https://github.com/LetsFinishSchool/chronos-v3/issues/72) | [#73](https://github.com/LetsFinishSchool/chronos-v3/issues/73), [#74](https://github.com/LetsFinishSchool/chronos-v3/issues/74) |
| F-011 / FA-011 | Anmeldung und Konto | [#28](https://github.com/LetsFinishSchool/chronos-v3/issues/28) | [#29](https://github.com/LetsFinishSchool/chronos-v3/issues/29), [#30](https://github.com/LetsFinishSchool/chronos-v3/issues/30) |
| F-014 / FA-014 | Serientermine | [#75](https://github.com/LetsFinishSchool/chronos-v3/issues/75) | [#76](https://github.com/LetsFinishSchool/chronos-v3/issues/76), [#77](https://github.com/LetsFinishSchool/chronos-v3/issues/77), [#78](https://github.com/LetsFinishSchool/chronos-v3/issues/78), [#79](https://github.com/LetsFinishSchool/chronos-v3/issues/79) |
| F-015 / FA-015 | KI-Assistent | [#80](https://github.com/LetsFinishSchool/chronos-v3/issues/80) | [#81](https://github.com/LetsFinishSchool/chronos-v3/issues/81), [#82](https://github.com/LetsFinishSchool/chronos-v3/issues/82), [#83](https://github.com/LetsFinishSchool/chronos-v3/issues/83), [#84](https://github.com/LetsFinishSchool/chronos-v3/issues/84), [#85](https://github.com/LetsFinishSchool/chronos-v3/issues/85), [#86](https://github.com/LetsFinishSchool/chronos-v3/issues/86), [#87](https://github.com/LetsFinishSchool/chronos-v3/issues/87) |
| F-016 / FA-016 | Dauerhafte Zeitraumsregeln (Bulk) | [#88](https://github.com/LetsFinishSchool/chronos-v3/issues/88) | [#89](https://github.com/LetsFinishSchool/chronos-v3/issues/89), [#90](https://github.com/LetsFinishSchool/chronos-v3/issues/90) |
| F-017 / FA-017 | Gelöschtes wiederherstellen und Änderungsverlauf | [#32](https://github.com/LetsFinishSchool/chronos-v3/issues/32) | [#33](https://github.com/LetsFinishSchool/chronos-v3/issues/33), [#34](https://github.com/LetsFinishSchool/chronos-v3/issues/34), [#35](https://github.com/LetsFinishSchool/chronos-v3/issues/35), [#36](https://github.com/LetsFinishSchool/chronos-v3/issues/36), [#37](https://github.com/LetsFinishSchool/chronos-v3/issues/37), [#38](https://github.com/LetsFinishSchool/chronos-v3/issues/38) |
| F-018 / FA-018 | Kostenerfassung | [#39](https://github.com/LetsFinishSchool/chronos-v3/issues/39) | [#40](https://github.com/LetsFinishSchool/chronos-v3/issues/40), [#41](https://github.com/LetsFinishSchool/chronos-v3/issues/41) |
| F-012 / FA-012 | Datenübernahme aus chronos-root (Tasks unter Epic RM-001) | [#1](https://github.com/LetsFinishSchool/chronos-v3/issues/1) | [#42](https://github.com/LetsFinishSchool/chronos-v3/issues/42), [#43](https://github.com/LetsFinishSchool/chronos-v3/issues/43), [#44](https://github.com/LetsFinishSchool/chronos-v3/issues/44), [#45](https://github.com/LetsFinishSchool/chronos-v3/issues/45), [#46](https://github.com/LetsFinishSchool/chronos-v3/issues/46) |
| F-013 / FA-013 | Rechtliche Seiten (einzelne Story unter Epic RM-001) | [#31](https://github.com/LetsFinishSchool/chronos-v3/issues/31) | [#31](https://github.com/LetsFinishSchool/chronos-v3/issues/31) |

Ein früheres Feature kann auf zwei Epics verteilt sein (F-005: Zusage/Absage in RM-001, „zeitweise“ in RM-003; F-008: Web Push/E-Mail in RM-001, Messenger als Option RM-006), weil ein Ticket genau ein Elternticket hat.

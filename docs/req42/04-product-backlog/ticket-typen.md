---
title: Ticket-Typen
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
---

# Ticket-Typen: Epic, Feature, User-Story, Task

Definition der Granularitätsstufen des Product Backlogs. Der Stand steht in den GitHub-Issues ([Referenz](README.md)); neue Arbeit entsteht als GitHub-Ticket des jeweiligen Typs (Label `epic`, `feature`, `story`, `task`). Rang und Priorität legt der Product Owner fest ([RA-008](../12-risiken-annahmen/RA-008-offene-fragen.md)). Rollen und Ablauf: [TS-001](../10-teamstruktur/TS-001-rollen-und-zusammenarbeit.md).

## 1. Überblick und Abgrenzung

| Typ | Frage, die er beantwortet | Zuschnitt | Abgeschlossen durch | Ablage |
|---|---|---|---|---|
| **Epic** | Welches Ziel erreichen wir? | Mehrere Features, mehrere Wochen bis Monate; entspricht einem Roadmap-Eintrag (`RM-nnn`), ausgenommen Optionen ohne Termin | Alle Kind-Tickets erledigt, Ziel überprüft | GitHub-Ticket, Label `epic`; Roadmap `docs/req42/11-roadmaps/` |
| **Feature** | Welche Fähigkeit bekommt der Nutzer? | Zusammenhängender Funktionsumfang, ein Sprint bis wenige Wochen, besteht aus mehreren Stories | Alle Stories erledigt, Feature im Produkt nutzbar | GitHub-Ticket, Label `feature` |
| **User-Story** | Was will wer damit erreichen, und woran erkennen wir das? | Ein Nutzerwert, einzeln auslieferbar und abnehmbar, in einem Sprint fertig; beschreibt das **Was**, nicht das **Wie** | Alle Akzeptanzkriterien nachweislich erfüllt, Produkt-Owner-Abnahme | GitHub-Ticket, Label `story` |
| **Task** | Welche technische Arbeit setzt das um? | Ein Arbeitspaket für **einen** Bearbeiter (Mensch oder Agent) und **einen** PR, möglichst unter einem Tag | PR gemergt, Prüfungen grün | GitHub-Ticket, Label `task` (+ `ready-for-agent`) |

Trennlinien:

- **Epic ↔ Feature:** Ein Epic ist an einem Ziel (`Z-nnn`) gemessen, ein Feature an einer Nutzerfähigkeit. Ein Epic kann ohne Neuentwicklung nicht abgeschlossen werden, liefert aber selbst keinen Code.
- **Feature ↔ Story:** Ein Feature wird erst durch das Zusammenspiel mehrerer Stories sichtbar; eine Story ist allein abnehmbar. Lässt sich ein Feature in einem Stück abnehmen, ist es eine Story.
- **Story ↔ Task:** Die Story hat einen Nutzer und eine Abnahme, der Task hat nur einen Bearbeiter und einen PR. Der Nutzer kennt Tasks nicht. Fachlich prüfbar = Story, technisch prüfbar = Task.
- **Task ↔ Bug:** Fehler bleiben Label `bug`; sie sind weder Story noch Task und brauchen keine Akzeptanzkriterien, sondern Reproduktion und erwartetes Verhalten.
- **Technische Arbeit ohne Nutzerwert** (Refactoring, CI, Deployment, Datenübernahme) ist ein Task direkt unter einem Feature oder Epic, keine Story mit erfundenem Nutzer.
- **Option:** Ein Roadmap-Eintrag ohne Termin und ohne Einplanung (z. B. Messenger-Kanäle) ist ein Feature mit Label `option` und ohne Elternticket; er wird erst zum Teil eines Epics, wenn der Product Owner ihn einplant.
- **Einzelne Story:** Würde ein Feature nur eine Story enthalten, entfällt das Feature; die Story hängt direkt am Epic.

Hierarchie: Epic 1 : n Feature 1 : n Story 1 : n Task. Ein Ticket hat höchstens ein Elternticket (Ausnahme: Option); die Verknüpfung steht im Ticketkopf („Teil von #…“) und über GitHub-Sub-Issues bzw. Task-Liste im Elternticket.

## 2. Struktur je Typ

Alle Tickets: deutscher Titel, ein Typ-Label, Verweis auf Elternticket.

**Epic**

```markdown
## Ziel
Welches Ziel (Z-nnn) und welchen Mehrwert bringt das Epic? Für wen (SH-nnn)?

## Erfolgskriterien
Messbare Aussagen, an denen sich das Erreichen zeigt (nicht Aufgabenliste).

## Abgrenzung
Was gehört ausdrücklich nicht dazu?

## Features
- [ ] #…  (Task-Liste, Reihenfolge = Rang)

## Offene Entscheidungen / Risiken
Verweise auf Risiken und Annahmen (`RA-nnn`) und offene Fragen an den Product Owner.
```

**Feature**

```markdown
## Als … möchte ich … damit …
Eine Zeile Nutzernutzen auf Fähigkeitsebene.

## Umfang
Was kann der Nutzer danach, was er vorher nicht konnte? Nicht-Ziele.

## Stories
- [ ] #…

## Abhängigkeiten
Andere Features, Dienste (Keycloak, Push …), Betriebsfolgen.
```

**User-Story**

```markdown
## Story
Als <Rolle/Stakeholder> möchte ich <Fähigkeit>, damit <Nutzen>.

## Akzeptanzkriterien
Prüfbare Aussagen, getrennt nach Verhalten und Oberfläche (Gegeben/Wenn/Dann oder Aufzählung), inkl. Fehlerfälle, Berechtigungen, leere/Lade-/Fehlerzustände.

## Nicht Teil dieser Story
Abgrenzung, Folge-Stories.

## Tasks
- [ ] #…

## Hinweise
Betroffene Modelle, Randbedingungen und Qualitätsszenarien (M-, RB-, QA-nnn), Wireframe (Pfad in `designs/wireframes/`), offene Fragen.
```

**Task**

```markdown
## Ziel
Ein Satz: Was ist nach dem PR anders?

## Umsetzung
Betroffene Module/Dateien, vorgesehener Ansatz, Randbedingungen (RB-/RA-nnn). Genug, dass ein Agent ohne Rückfrage starten kann.

## Fertig, wenn
Prüfbare Liste (Verhalten, Tests, Prüfbefehle).

## Nicht Teil dieses Tasks
Abgrenzung.

## Prüfung
Prüfbefehle des betroffenen Bausteins (legt die Entwicklung fest, siehe ADR-009 und ADR-013).
```

Ein Task trägt `ready-for-agent` erst, wenn Ziel, Umsetzung und „Fertig, wenn“ ausgefüllt sind und keine Rückfrage offen ist.

## 3. Definition of Done

Gilt jeweils **zusätzlich** zu den Kriterien der darunterliegenden Ebene (bottom-up).

**Task – DoD**
- Umsetzung entspricht „Fertig, wenn“ und dem Ziel; nichts außerhalb des Umfangs geändert.
- Tests geschrieben bzw. angepasst; Qualitätsprüfungen des Bereichs grün (Prüfungen werden in der Entwicklung festgelegt).
- PR `Resolve #<Ticket>: <Titel>`, Body beginnt mit `Closes #<Ticket>`, gegen `main`/`develop`; CI grün.
- Review erfolgt, Konflikte gelöst, PR gemergt (Mensch).
- Keine Geheimnisse im Diff ([RB-008](../07-randbedingungen/RB-008-keine-geheimnisse-im-repository.md)); Datenbankmigrationen nur vorwärts; Oberflächentexte übersetzbar, Deutsch und Englisch ([RB-001](../07-randbedingungen/RB-001-mehrsprachigkeit.md)).
- Oberflächenänderungen erfüllen WCAG 2.2 Stufe AA: automatische Prüfung (axe-core) ohne Verstöße in Deutsch und Englisch, Bedienung per Tastatur, Oberfläche in Tests über Rollen und Beschriftungen ansprechbar.
- `docs/` nicht verändert; Widersprüche zu `docs/` als Vorschlag gemeldet (Ablauf für Agenten: [AGENTS.md](../../../AGENTS.md)).

**User-Story – DoD**
- Alle Tasks erledigt (Task-DoD).
- Jedes Akzeptanzkriterium ist nachweislich erfüllt: automatisierter Test oder dokumentierte manuelle Prüfung, inklusive Fehler-, Berechtigungs- und Leerzustände.
- Die Story läuft zusammen mit dem Rest des Produkts (Integration auf `main`, kein Feature-Flag-Rest ohne Plan).
- Querschnittsanforderungen sind erfüllt, soweit die Story sie betrifft:
  - Berechtigungen nach [M-002](../05-modelle/M-002-berechtigungen.md) umgesetzt und getestet (Mitglied, Gast, Nichtmitglied).
  - Jede schreibende Operation steht im Änderungsverlauf (Akteur, Zeitpunkt, bei Assistentenläufen „im Auftrag von …“).
  - Jede Fachfunktion ist als Operation für den Assistenten aufrufbar, ohne Sonderweg der Weboberfläche ([RB-011](../07-randbedingungen/RB-011-einfache-weboberflaeche-vollstaendige-funktionen-ueber-assistent.md), [QA-003](../06-qualitaet/QA-003-aenderbarkeit.md)).
  - Ausgelöste Benachrichtigungen entsprechen [M-004](../05-modelle/M-004-benachrichtigungsmatrix.md); jede kostenpflichtige Zustellung erzeugt einen Kostenposten ([RB-010](../07-randbedingungen/RB-010-kostenzuordnung.md), [QA-009](../06-qualitaet/QA-009-kostentransparenz.md)).
  - Die Oberfläche ist ab 320 px Breite bedienbar, mobil zuerst ([QA-005](../06-qualitaet/QA-005-bedienbarkeit-mobil.md)).
  - Es werden nur nötige personenbezogene Daten gespeichert; ändert die Story eine Verarbeitung, ist die Datenschutzerklärung angepasst ([QA-007](../06-qualitaet/QA-007-sicherheit-und-datenschutz.md), [RB-006](../07-randbedingungen/RB-006-datenschutz-und-impressum.md)).
  - Logs und Ereignisse tragen die Korrelations-ID ([QA-002](../06-qualitaet/QA-002-nachvollziehbarkeit.md)).
  - Zeiten tragen eine Zeitzone (Termin, Team, Person).
- Product Owner hat abgenommen (Ticket kommentiert/geschlossen).

**Feature – DoD**
- Alle Stories erledigt (Story-DoD).
- Der Funktionsumfang ist Ende-zu-Ende aus Nutzersicht verwendbar (Frontend + Backend + ggf. Push/Keycloak), auf Mobil und Desktop.
- Nichtfunktionale Anforderungen berührter Qualitätsziele geprüft (Datenschutz, Leistung, Benachrichtigungen), Betrieb berücksichtigt (Helm-Werte, Migrationen, Monitoring). Barrierefreiheit nach WCAG 2.2 Stufe AA: manueller Durchlauf mit Tastatur und Screenreader je Feature.
- Seitenaufruf auf `staging` unter 1 s im Rahmen des Ressourcenbudgets (Stichprobe, [QA-008](../06-qualitaet/QA-008-leistung.md)); Speicher und CPU liegen im Budget ([QA-001](../06-qualitaet/QA-001-ressourceneffizienz.md), [RB-003](../07-randbedingungen/RB-003-ressourcenbudget.md)).
- Berührt das Feature Benachrichtigungen: Test mit Neustart während des Versands ([QA-004](../06-qualitaet/QA-004-zuverlaessige-benachrichtigung.md)); Benachrichtigungsbudget in der Standardeinstellung eingehalten ([QA-010](../06-qualitaet/QA-010-benachrichtigungsbudget.md)).
- Architekturtests (Abhängigkeitsregeln) grün ([QA-003](../06-qualitaet/QA-003-aenderbarkeit.md), [ADR-009](../../arc42/09-entscheidungen/ADR-009-teststrategie-und-architekturregeln.md)).
- In `staging`/Testumgebung verifiziert; Rollback-Pfad bekannt.
- Nutzer-Doku/„Neuigkeiten“ geklärt.

**Epic – DoD**
- Alle Features erledigt oder bewusst gestrichen (jeweils begründet im Epic).
- Erfolgskriterien geprüft und Ergebnis im Epic festgehalten; Ziel (Z-nnn) erreicht oder Abweichung benannt; Zielmetrik gemessen.
- Lasttest mit 500 Nutzern: Antwortzeit und Ressourcen gemessen ([QA-001](../06-qualitaet/QA-001-ressourceneffizienz.md), [QA-008](../06-qualitaet/QA-008-leistung.md)).
- Betrifft das Epic Daten: Wiederherstellungstest bestanden, RPO 24 h und RTO 8 h ([QA-006](../06-qualitaet/QA-006-datensicherung.md)).
- Datenschutzprüfung: keine Abweichung zwischen Datenschutzerklärung und System ([Z-007](../01-ziele/Z-007-datensparsam-und-datenschutzkonform-betreiben.md)).
- Produktiv ausgerollt ([RB-005](../07-randbedingungen/RB-005-betrieb-auf-geteiltem-k3s-cluster.md)), Bestandsdaten migriert, Altlasten entfernt.
- Roadmap-Eintrag (`RM-nnn`) aktualisiert, offene `follow-up`-Tickets abgearbeitet oder verschoben, Rückblick (was gelernt?) festgehalten.
- Product Owner schließt das Epic.

**Definition of Ready**

Eine Story ist bereit, wenn:
1. Rolle, Fähigkeit und Nutzen im Format „Als … möchte ich … damit …“ stehen und ein Nutzer benannt ist (ohne Nutzer ist es ein Task).
2. Die Akzeptanzkriterien prüfbar sind und Fehler-, Berechtigungs- sowie leere, Lade- und Fehlerzustände enthalten.
3. „Nicht Teil dieser Story“ ausgefüllt und Folge-Stories verlinkt sind.
4. **Oberfläche:** Hat die Story sichtbare UI, liegt **immer** ein Wireframe für **Mobil (320 px), Tablet (768 px) und Desktop (1280 px)** vor: eine Excalidraw-Datei `designs/wireframes/S<Nr>-<kurzname>.excalidraw` mit drei beschrifteten Rahmen und SVG-Export gleichen Namens, im Ticket unter „Hinweise“ verlinkt. Jeder Rahmen zeigt alle Zustände aus Punkt 2 (normal, leer, laden, Fehler, ohne Berechtigung) und nennt Farben und Abstände nur über Token-Namen aus `designs/tokens/tokens.json` (z. B. `bg.surface`, `space.4`), nie Hex-Werte. Das gilt auch für Screens aus dem bisherigen Design; eine bloße Skizze im Ticket genügt nicht. Fehlt ein Token oder eine Komponente, ist das ein eigener Task (Design-System), der zuerst erledigt wird.
5. Abhängigkeiten (Stories, Tasks, Dienste, Entscheidungen) benannt sind und jedes Ticket, von dem die Story abhängt, in GitHub als „blocked by“ eingetragen ist.
6. Berührte Modelle und Qualitätsszenarien (M-, RB-, QA-nnn) genannt sind; es gibt keine offene Frage an den Product Owner.
7. Die Story in einem Sprint fertigzustellen ist, sonst wird sie geteilt.
8. Der Product Owner sie bestätigt hat (Kommentar oder Label `ready`).

Ein Task ist bereit, wenn:
1. „Ziel“, „Umsetzung“ und „Fertig, wenn“ ausgefüllt sind und der Agent ohne Rückfrage starten kann.
2. Die Eltern-Story bereit ist und jedes Ticket, von dem der Task abhängt, in GitHub als „blocked by“ eingetragen ist.
3. Prüfbefehle benannt und lauffähig sind; benötigte Zugänge und Testdaten sind vorhanden.
4. Bei UI auf den Wireframe der Story (alle drei Breiten, Pfad in `designs/wireframes/`) und die verwendeten Tokens und Komponenten verwiesen wird.
5. Der Umfang höchstens ein PR ist, möglichst unter einem Tag.

`ready-for-agent` wird nur vergeben, wenn alle Punkte der Task-Definition gelten.

## 4. Beispiel (Terminfindung, RM-003 / #3)

- **Epic** #3 „RM-003 Terminfindung“ (Ziel: Gruppen finden ohne Chat einen Termin).
- **Feature** #57 „F-006 Terminfindung per Abstimmung“; **Feature** #55 „F-005 Rückmeldung ‚zeitweise‘“.
- **Story** #58 „Terminfindung mit Vorschlägen anlegen“: „Als Leitungsteam-Mitglied möchte ich mehrere Zeitpunkte vorschlagen und einen Link teilen, damit die Gruppe abstimmen kann.“
- **Tasks** (Beispiel für die Einplanung der Story) Datenmodell + Migration, REST-Endpunkt, Abstimmungs-Dialog.

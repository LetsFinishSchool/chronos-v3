# Briefing: Spike E-002, Kandidat typescript

Du bist ein Agent und setzt in diesem Verzeichnis einen **technischen Vergleichs-Spike** um. Es entsteht Wegwerfcode zur Bewertung der Sprache **typescript**. Zwei weitere Agenten lösen dieselbe Aufgabe in anderen Sprachen; du siehst ihre Arbeit nicht und sollst sie nicht suchen. Nach deiner Arbeit wird **unabhängig von dir** gemessen und abgenommen.

## 1. Rahmen

- **Zeitbox: 8 Stunden Wall-Clock.** Trage in `typescript/PROTOKOLL.md` den **Startzeitpunkt** ein (UTC, `date -u`) und danach bei jeder Aufgabe S-1 bis S-10 Beginn und Ende. Was nach 8 Stunden nicht fertig ist, gilt als nicht erreicht. Mach nicht mehr, als verlangt ist.
- Stelle keine Rückfragen an Menschen: Triff bei Unklarem die einfachste Entscheidung, die zur Beschreibung passt, und notiere sie in `typescript/README.md` (Abschnitt „Annahmen“).
- Arbeitsverzeichnis ist dieses Verzeichnis. Ändere nichts außerhalb davon.

## 2. Was du zu lesen hast

1. `common/V-1-aufgabenbeschreibung.md`: **verbindliche Aufgabe und HTTP-Verträge.** Lies sie vollständig und zuerst.
2. `common/acceptance/README.md` und die Tests dort: Die Abnahmesuite prüft deine Umsetzung. **Du darfst und sollst sie zum Selbsttest ausführen.** Die Verträge in V-1 gelten vor den Tests; Widersprüche meldest du in `typescript/README.md`.
3. `common/env/`: Container-Umgebung (PostgreSQL, Keycloak, Mailpit, Mock-Kanal).

## 3. Vorgaben für typescript

- Sprache und Laufzeit: **TypeScript auf Node.js 22 (LTS)**, `strict`. Frameworks: **Fastify, Kysely, Zod oder TypeBox**. Container-Build mehrstufig, Laufzeitabbild schlank.

- Die Frameworks oben sind **festgelegt**; wechsle sie nicht. Alle anderen Bibliotheken (RRULE, Web Push, OIDC, Aufträge, E-Mail, KI-SDK, Schema-Erzeugung) wählst du selbst: **bevorzuge gepflegte, verbreitete Bibliotheken** und trage Name und Version in `typescript/README.md` ein.
- **Eigenbau ist teuer.** Alles, was du statt einer Bibliothek selbst schreibst (z. B. RRULE-Ausdehnung, Kryptografie, Token-Prüfung), umschließe mit den Kommentarzeilen `EIGENBAU:BEGIN` und `EIGENBAU:END` (in der Kommentarsyntax der Sprache). Das wird gezählt.
- Ein Image, zwei Startarten (`web`, `worker`) nach V-1 §1. Quelltext, `Dockerfile`, `Makefile` (Ziele `build`, `test`, `arch-check`, `bridge`) liegen in `typescript/`.

## 4. Umgebung starten und testen

```sh
cd typescript && make build                                 # baut Image chronos-spike-typescript
cd ../common/env && ./stack.sh up typescript 0 chronos-spike-typescript
eval "$(./stack.sh env typescript 0)"              # setzt BASE_URL usw.
export CANDIDATE_DIR=$PWD/../../typescript
python3 ../acceptance/run_acceptance.py                   # Phase 1
cd ../env && ./stack.sh restart-app typescript 0 chronos-spike-typescript   # nach neuem Image: Web und Worker neu erstellen
```
Ports (alle auf `localhost`): Web 8080, Worker-Gesundheit 8081, Keycloak 8180, Mailpit-Oberfläche 8025, Mock-Kanal 8090. Web und Worker laufen im Host-Netz des Containers mit den Umgebungsvariablen aus `.stack/typescript/app.env` (siehe V-1 §2). **Zugangsdaten stehen nur in dieser Umgebung, nie in Dateien, die du anlegst oder committest.** Die KI erreichst du **nur** über `ANTHROPIC_BASE_URL` (ein Schutz-Proxy mit hartem Budget); der echte Schlüssel ist dir unbekannt und soll es bleiben. Der Proxy erlaubt nur `POST /v1/messages`, nur das Modell aus `ANTHROPIC_MODEL`, kein Streaming, `max_tokens` höchstens 1024, insgesamt höchstens 150 Anfragen. Antwortet er mit 429 (Budget aufgebraucht), nutze K6 nicht weiter und vermerke es im Protokoll; **versuche nicht, die Grenzen zu umgehen**. Rufe die KI sparsam auf (K6 braucht nur wenige Aufrufe).

Der Web-Push-Test (K3) ist manuell (`common/acceptance/manual/K3-webpush.md`) und nicht Teil deiner Aufgabe; sorge nur dafür, dass `/static/` ausgeliefert wird und die VAPID-Variablen genutzt werden.

## 5. Arbeitsregeln

1. **Keine Geheimnisse ins Repository** (Schlüssel, Tokens, Passwörter außer den vorgegebenen Test-Zugängen in `common/`).
2. Halte dich an die Verträge in V-1 genau (Feldnamen, Statuscodes, Fehlercodes). Alles andere ist deine Wahl.
3. **Eine Beschreibung je Operation** (V-1 §4): Es darf keine zweite, von Hand gepflegte Liste von Operationen, Werkzeugen oder Typen geben.
4. **Korrekturschleife** = ein Zyklus aus Fehlerausgabe (Übersetzer, Test, Laufzeit) und anschließender Änderung. Zähle sie fortlaufend in `typescript/PROTOKOLL.md` (eine Zeile je Schleife mit Kurzgrund).
5. Committe in diesem Repository (`git`) in sinnvollen Schritten. Wenn Phase 1 (S-1 bis S-10) fertig ist, committe mit der Nachricht **`PHASE-1-FERTIG`** und schreibe `PHASE-1-FERTIG` samt Zeit in das Protokoll. **Dann hör auf und warte**: Die Zusatzaufgabe (Phase 2) wird dir danach als Datei `PHASE2.md` im Arbeitsverzeichnis bereitgestellt.
6. Bei Phase 2 gilt dasselbe: committe, schreibe `PHASE-2-FERTIG` ins Protokoll, stopp.
7. Abschlussbericht: `typescript/README.md` mit verwendeten Bibliotheken samt Versionen, Eigenbau-Stellen (Datei, Zweck), Annahmen, nicht erreichten Aufgaben und Auffälligkeiten (insbesondere zu Bibliotheken für RRULE, Web Push, OIDC, Aufträge, KI-SDK: Reifegrad, Probleme).

## 6. Reihenfolge-Empfehlung (du darfst abweichen)

S-1 Operationsbeschreibung und Aufruf → S-2/S-3 Datenmodell, Transaktion, Verlauf, Rückgängig → S-4 Worker und Kanäle → S-5 RRULE → S-6 Anmeldung → S-7 KI → S-9 Architekturregel → S-10 Brücke → S-8 Lastlauf (nur zur Selbstkontrolle der Stabilität). Prüfe nach jedem Block mit der Abnahmesuite (`--only` nach Kennzeichen, siehe `common/acceptance/README.md`).

## 7. Bei Fertigstellung

Schreibe `FERTIG` mit Zeit in `typescript/PROTOKOLL.md`, committe und höre auf.

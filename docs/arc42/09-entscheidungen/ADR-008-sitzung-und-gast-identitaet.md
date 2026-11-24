---
id: ADR-008
title: Sitzung als BFF mit Refresh-Heartbeat und Back-Channel-Logout, Gast-Identität
status: freigegeben   # entwurf | freigegeben | ersetzt
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-008]
quellen: [E-004-E-008-frontend-und-zugang-analyse, FA-002, FA-005, FA-011, F-002, F-011, QA-005, QA-007, RB-002, RA-009, SH-006, K-002, ADR-005, ADR-007, Entscheidung des Product Owners 2026-11-24 (Gespräch)]
---

# ADR-008: Sitzung als BFF mit Refresh-Heartbeat und Back-Channel-Logout, Gast-Identität

**Hinweis:** Der Product Owner hat Sitzungsmodell, Intervall 6 Stunden, Betrieb von Keycloak und WCAG 2.2 AA am 2026-11-24 im Gespräch entschieden. Dieser Text wurde vom Product Owner am 2026-11-24 freigegeben. Die Gast-Identität (Abschnitt 4), T6 (Abschnitt 5) und die Sitzungsdauern (Abschnitt 1) hat der Product Owner am 2026-11-24 nachträglich entschieden. Es bleiben keine offenen Punkte.

## Kontext
Anmeldung nur über den geteilten Keycloak, keine Passwörter in Chronos ([RB-002](../../req42/), [FA-011](../../req42/)). Die Sitzung soll für aktive Personen nicht sichtbar ablaufen (FA-011 AK 2), Zugangstoken dürfen für Skripte der Seite nicht lesbar sein ([QA-007](../../req42/), [K-002](../08-konzepte/)). Keycloak-Ausfall darf Gäste und bestehende Sitzungen nicht lahmlegen ([RA-009](../../req42/12-risiken-annahmen/RA-009-budget-und-abhaengigkeit-von-keycloak.md)). Oberfläche als SPA unter derselben Herkunft ([ADR-007](ADR-007-frontend-spa-svelte.md)). Der Product Owner betreibt Keycloak selbst und kann Client, Back-Channel-Logout und Sitzungsdauern einstellen; damit entfällt der Hauptgrund für eine vom Keycloak vollständig entkoppelte Sitzung (T1-A der [Analyse](E-004-E-008-frontend-und-zugang-analyse.md)).

## Optionen
Ausführlich in der Analyse (T1 bis T3). Für die Sitzung: **T1-A** eigene Sitzung, nur bei der Anmeldung an Keycloak gebunden, mit Back-Channel-Logout; **T1-B** BFF mit Refresh-Token; **T1-C** Token im Browser (ausgeschlossen durch C9); sowie Keycloaks Sitzung direkt zu verwenden (Prüfung bei jeder Anfrage, Ausfall meldet alle ab, nicht gewählt). Die Anforderung, dass Chronos selbst Ressourcen-Server ist und das Access-Token nie benutzt, macht aus T1-B einen **BFF mit Refresh-Heartbeat**: Das Refresh-Token dient nur als Lebenszeichen der Keycloak-Sitzung.

## Entscheidung (PO, 2026-11-24)

### 1. Sitzung: BFF mit Refresh-Heartbeat und Back-Channel-Logout
- **Eigene Sitzung** in Chronos (Tabelle `sessions`), Browser-Cookie `__Host-`-Präfix, `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/`. Zufall mindestens 128 Bit; in der Datenbank **nur der Hash**. Schreibende Anfragen prüfen `Origin` (CSRF). Keycloak-Tokens verlassen den Server nie (C9).
- **Gleitende Sitzung:** **30 Tage Leerlauf** in Chronos (PO, nachträglich entschieden 2026-11-24). Eine **eigene Höchstdauer in Chronos entfällt**; die Höchstdauer setzt der Betreiber in Keycloak: **180 Tage** (SSO Session Max). Der **Leerlauf in Keycloak** (SSO Session Idle) beträgt **7 Tage**: Er bestimmt, wie lange ein Ausfall von Keycloak dauern darf, ohne dass der Heartbeat scheitert und alle abgemeldet werden (er muss mindestens das Heartbeat-Intervall plus Reserve betragen). Die Werte sind reine Konfiguration und ohne Codeänderung anpassbar.
- **Refresh-Token** wird serverseitig gespeichert, **verschlüsselt** (AEAD, z. B. AES-256-GCM, Schlüssel aus dem Kubernetes-Secret, Schlüsselkennung je Zeile für Rotation).
- **Heartbeat alle 6 Stunden:** Der Worker erneuert je Sitzung das Token bei Keycloak (Refresh-Grant). Das hält die Keycloak-Sitzung am Leben, und eine Sperrung, Löschung oder Rechteänderung in Keycloak wirkt dadurch spätestens nach 6 Stunden. Sitzungen, die in Chronos abgelaufen sind, werden nicht mehr erneuert; die Keycloak-Sitzung läuft dann nach ihrem eigenen Leerlauf ab.
- **Weicher Ausfall:** Zeitüberschreitung, Netzfehler und 5xx beenden die Sitzung **nicht**; der Versuch wird wiederholt (zunehmende Abstände, innerhalb des Intervalls). Nur eine eindeutige Ablehnung (`invalid_grant`) beendet die Sitzung. So gilt C16/RA-009: Ein Keycloak-Ausfall meldet niemanden ab.
- **Back-Channel-Logout:** Endpunkt für den `logout_token` von Keycloak (Prüfung von Signatur über JWKS, `iss`, `aud`, `events`, `iat`, kein `nonce`; Zuordnung über `sid` oder `sub`); löscht die betroffenen Sitzungen sofort. Er ist **best effort** ▲ (keine zugesicherte Wiederholung bei Ausfall von Chronos); der Heartbeat ist das Sicherheitsnetz. Der Endpunkt ist idempotent.
- **Refresh-Token-Rotation** in Keycloak aktiviert. Je Sitzung höchstens **ein** Refresh gleichzeitig (Sperre in der Datenbank, z. B. `SELECT … FOR UPDATE SKIP LOCKED`), damit Chronos mit mehreren Instanzen nicht selbst eine Wiederverwendung auslöst. Meldet Keycloak eine Wiederverwendung als Angriff, wird die Sitzung sofort beendet.
- **Abmeldung** löscht die Sitzung in Chronos und leitet zum Keycloak-Logout weiter.
- **Betrieb von Keycloak (PO):** vertraulicher Client mit Authorization-Code-Flow und PKCE, Back-Channel-Logout-URL, Selbstregistrierung, Sitzungsdauern. Weil der Keycloak geteilt ist, sollen Leerlauf und Höchstdauer **am Client** (Client Session Idle/Max, ▲ je nach Version) gesetzt werden, damit andere Anwendungen im Realm nicht beeinflusst werden.

### 2. Link-Token
Wie in [ADR-007](ADR-007-frontend-spa-svelte.md): im **Fragment** der Adresse, Austausch per Skript gegen das Gast-Cookie, in der Datenbank nur der Hash, `Referrer-Policy: no-referrer` auf Gastseiten, Widerruf und Ablauf über den Geltungsbereich „Gastlink“ ([ADR-005](ADR-005-operationsschicht.md)). Ein Token im Pfad ist nicht zulässig.

### 3. Barrierefreiheit
**WCAG 2.2 Stufe AA** ist der Prüfmaßstab der Definition of Done (PO). Die Konkretisierung steht in T8 der Analyse und in den Vorgaben V-5 und G-3 von ADR-007. Die Anpassung des DoD-Textes in `docs/req42/04-product-backlog/ticket-typen.md` ist eine Änderung an `docs/` und braucht einen eigenen Vorschlag.

### 4. Gast-Identität (PO, 2026-11-24, nachträglich entschieden)
- **T2-B (entschieden):** Die erste Antwort legt eine Gast-Person an und setzt ein Cookie, beschränkt auf den Link und gültig bis zu dessen Ablauf (Terminende + 30 Tage). Danach zeigt Chronos einen **persönlichen Rückkehr-Link** („Antwort später ändern“), der in der Datenbank ebenfalls nur als Hash liegt.
- **T2-C** (freiwillige E-Mail-Bestätigung, ermöglicht Erinnerungen an Gäste) bleibt ein möglicher späterer, freiwilliger Zusatz und ist nicht entschieden.
- **Übernahme ins Konto:** Operation `guest.claim` (Akteur-Art Gast → Person, mit Verlaufseintrag) überträgt Antworten, Stimmen und Nachrichten.
- **Nicht zulässig:** Auswahl „Das bin ich“ aus der Liste (T2-D), weil jeder mit dem Link fremde Antworten ändern könnte (FA-005 AK 6).

### 5. PWA, Service Worker und Push (PO, 2026-11-24, nachträglich entschieden)
- **T6-C:** Eigener schlanker Service Worker als **Plain-JS-Datei ohne Framework-Bezug** (kein `$service-worker` von SvelteKit, ADR-007 V-2): Push-Empfang, Klick auf die Benachrichtigung öffnet die richtige Seite, Manifest für die Installation, **kein Cache** von Seiten oder Daten. Dazu eine kleine statische **Offline-Rückfallseite**, die nur bei fehlendem Netz angezeigt wird. Die Gastseite (eingebettete Termindaten) wird nie zwischengespeichert.
- **Abo-Lebenszyklus:** Das Push-Abonnement wird nur auf Klick der Person angelegt (iOS verlangt eine Benutzeraktion), `pushsubscriptionchange` erneuert es, und ein 404 oder 410 vom Push-Dienst löscht es auf dem Server.
- **VAPID-Schlüssel:** Der öffentliche Schlüssel wird als lesende Operation ohne Anmeldung bereitgestellt (schließt ADR-004, offener Punkt 5).
- **Ungeprüft ▲:** Push auf iOS nur in der installierten PWA; Weiterleitung zu Keycloak und zurück aus der installierten PWA auf iOS.

## Folgen
**Leichter:** Browser sieht nur ein eigenes Cookie; keine Tokens in Skripten; Sperrung in Keycloak wirkt sofort (Back-Channel) oder nach höchstens 6 Stunden (Heartbeat); Keycloak-Ausfall meldet niemanden ab; Höchstdauer an einer Stelle.

**Schwerer / Risiken (für Kapitel 11):**
- Refresh-Tokens liegen verschlüsselt in der Datenbank; ein Leck von Datenbank **und** Schlüssel gäbe Zugriff auf Keycloak-Sitzungen. Schlüsselverwaltung und Rotation sind Pflicht (QA-007).
- Während eines Keycloak-Ausfalls bleiben auch **gesperrte** Konten angemeldet, bis Keycloak wieder antwortet. Das ist bewusst; eine Obergrenze für die Dauer des Ausfalls ist offen.
- Erneuerungsjob und Sperre je Sitzung sind zusätzlicher Code im Worker; Fehlerzweige sind zu testen (Wiederverwendung, `invalid_grant`, Ausfall, mehrere Instanzen).
- Back-Channel-Logout ist nicht zugesichert; das Intervall von 6 Stunden ist die Obergrenze der Verzögerung einer Sperre. Ein kürzeres Intervall (z. B. 15 Minuten) wäre ohne große Kosten möglich.
- Der Spike hatte Sitzungs-Token im Klartext ohne Ablauf und ohne `Secure`; das ist vor der Umsetzung zu ersetzen.

**Bindet / gibt frei:** Die Operationsschicht kennt die Akteur-Arten Person, Gast, Assistent und Import ([ADR-005](ADR-005-operationsschicht.md)); `guest.claim` ist als Operation zu beschreiben. T6 (PWA und Push) ist in Abschnitt 5 entschieden. T7 (Übersetzungen) ist in [ADR-010](ADR-010-uebersetzungen-fluent.md) entschieden (Fluent). Der Test des iOS-Anmeldeablaufs aus der installierten PWA ▲ ist vor der Umsetzung nötig.

## Festgelegte Werte (PO, 2026-11-24)
- **Keycloak-Ausfall:** keine eigene Obergrenze (der Leerlauf in Keycloak von 7 Tagen begrenzt ihn natürlich); **Alarm an den Betreiber**, wenn Heartbeats eine Stunde lang fehlschlagen.
- **Wiederholung bei Fehlschlag des Heartbeats:** nach 5, 15 und 30 Minuten, danach stündlich bis zum nächsten Zyklus.

## Wann überprüfen?
- Keycloak wird nicht mehr vom Product Owner betrieben, oder ein anderer Identitätsdienst ersetzt ihn.
- Eine Anforderung verlangt sofortiges Wirksamwerden jeder Sperre (dann kürzeres Intervall oder Prüfung bei jeder Anfrage).
- Die Verschlüsselung der Refresh-Tokens oder deren Speicherung in der Datenbank wird als zu riskant bewertet (dann T1-A ohne Refresh-Token).
- Gäste brauchen eine gerätübergreifende Wiedererkennung über den Rückkehr-Link hinaus.

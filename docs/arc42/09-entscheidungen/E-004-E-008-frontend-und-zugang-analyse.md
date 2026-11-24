---
title: E-004 Frontend-Ansatz und E-008 Keycloak, Sitzung, Gast, Analyse
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [Produktvision, Z-004, F-002, FA-002, FA-005, FA-006, FA-008, FA-009, F-011, FA-011, FA-013, QA-005, QA-007, QA-008, RB-001, RB-002, RA-006, RA-007, SH-003, SH-006, K-002, K-007, ADR-002, ADR-004, ADR-005, ADR-006, Rust-Spike E-002 (src/auth/mod.rs, migrations/0001_init.sql)]
---

# E-004 und E-008: Frontend und Zugang, Analyse

Entscheidungsvorlage für [E-004](01-offene-entscheidungen.md) (Frontend-Ansatz) und [E-008](01-offene-entscheidungen.md) (Keycloak, Sitzung, Gast-Identität). Beide werden **gemeinsam** betrachtet, weil sich Sitzungsmodell, Ablage der Link-Token und Auslieferung der Oberfläche gegenseitig binden. Grundlagen: Rust mit axum ([ADR-004](ADR-004-sprache-und-laufzeit.md)), Operationsschicht mit Akteur-Arten und Geltungsbereichen ([ADR-005](ADR-005-operationsschicht.md)), Assistent im Web-Prozess ([ADR-006](ADR-006-ki-anbindung.md)). Mit ▲ markierte Aussagen sind nicht geprüft und sollten vor der Umsetzung getestet werden.

## Anforderungen

| Nr. | Anforderung | Quelle |
|---|---|---|
| C1 | Mobil zuerst, ab 320 px, flexibel bis Desktop; Kernabläufe ohne Einarbeitung | QA-005 |
| C2 | Gast antwortet über Link in höchstens **drei Interaktionen**, Ziel ≤ 30 s vom Öffnen bis zur gespeicherten Antwort | QA-005, Z-004 |
| C3 | Seite lädt in < 1 s (< 500 aktive Nutzer, im Budget) | QA-008 |
| C4 | Als installierbare Web-App (PWA) nutzbar; Web Push als Kanal | Produktvision, FA-008 |
| C5 | Oberfläche einfach, bildet bewusst nicht alle Operationen ab; Assistent-Dialog daneben | RB-011, F-015 |
| C6 | Deutsch und Englisch, weitere Sprachen ohne Umbau; Gäste: Browsersprache, Rückfall Deutsch; Texte nicht im Code verstreut; Format JSON oder PO (K-007) | RB-001, K-007 |
| C7 | Anmeldung nur über den geteilten Keycloak; keine Passwörter; Registrierung über Keycloak | RB-002, FA-011, F-011 |
| C8 | Sitzung läuft für aktive Personen **nicht sichtbar** ab | FA-011 AK 2, K-002 |
| C9 | Zugangstoken sind für Skripte der Seite **nicht lesbar** | QA-007, K-002 |
| C10 | Link-Token nicht erratbar, widerrufbar; Gastlink gilt bis Terminende + 30 Tage; Gast sieht nur, wofür der Link gilt | FA-002, F-002, QA-007 |
| C11 | Ein Termin-Gastlink wird **geteilt** (z. B. in eine Gruppe); viele Gäste je Link; jeder Gast ändert nur die eigene Antwort, bis Terminbeginn | FA-002 AK 2, FA-005 AK 1, 6 |
| C12 | Gast kann sein bisheriges Handeln bei der Registrierung über denselben Link ins Konto übernehmen | F-011 |
| C13 | Team-Beitritt per Link setzt ein Konto voraus; Abstimmung (Terminfindung) auch per Link | FA-002 AK 4, FA-006 AK 1 |
| C14 | Impressum und Datenschutzerklärung ohne Anmeldung | FA-013 |
| C15 | Barrierefreiheit ist Teil der Definition of Done | ticket-typen.md |
| C16 | Ausfall von Keycloak: Gäste mit Link bleiben arbeitsfähig | RA-009 |

## Befund aus dem Spike

- **Brücke:** Aus `/api/v1/operations` werden TypeScript-Typen erzeugt; `call(name, params)` ist abhängig vom Operationsnamen typisiert (Q-5, bestes Ergebnis bei Rust).
- **Anmeldung:** Code-Flow mit PKCE, `state` und `nonce` über `openidconnect`. Nach der Anmeldung legt Chronos eine **eigene** Sitzung in PostgreSQL an und verwirft die Keycloak-Tokens. Das Sitzungs-Token liegt **im Klartext** in der Tabelle `sessions`, ohne Ablauf; das Cookie hat ohne TLS kein `Secure`.
- **Bearer-Prüfung** (JWKS, `iss`, `exp`) ist zusätzlich vorhanden; sie war für Tests nötig, nicht für den Browser.
- **Web Push** (K3) funktionierte in Firefox und Chrome mit einer statischen Testseite und Service Worker. Der Endpunkt für den öffentlichen VAPID-Schlüssel fehlte in V-1 (ADR-004, offener Punkt 5).
- Keine Oberfläche, keine Gäste, keine Mehrsprachigkeit (Nicht-Ziele von V-1).

## Teilentscheidungen zu E-008 (Zugang)

### T1 Sitzungsmodell für Konten

Keycloak-Sitzungen sind in der Standardeinstellung kurz (Leerlauf- und Höchstdauer je Realm, vom Betreiber des Keycloak gesetzt ▲). „Nicht sichtbar ablaufen“ (C8) hängt deshalb davon ab, ob Chronos die Keycloak-Sitzung braucht.

| Option | Vorteile | Nachteile |
|---|---|---|
| **T1-A** Eigene Sitzung, von Keycloak entkoppelt (wie Spike): Keycloak nur bei der Anmeldung; Sitzung gleitend (z. B. 30 Tage ab letzter Aktivität, Höchstdauer z. B. 180 Tage); dazu **Back-Channel-Logout**: Keycloak meldet Abmeldung oder Sperrung, Chronos löscht die Sitzungen der Person | C8 erfüllt, ohne Realm-Einstellungen zu ändern; keine Keycloak-Tokens in Chronos gespeichert; ein Keycloak-Ausfall stört angemeldete Personen nicht | Eine Sperrung in Keycloak wirkt nur sofort, wenn der Back-Channel-Logout eingerichtet ist (Konfiguration des Clients durch den Keycloak-Betreiber, SH-006); ohne ihn erst beim Ablauf |
| **T1-B** Sitzung mit Refresh-Token (klassisches BFF): Chronos speichert das Refresh-Token verschlüsselt und erneuert regelmäßig | Sperrungen in Keycloak wirken bei der nächsten Erneuerung | C8 nur mit langen Refresh- oder Offline-Tokens im Realm (Betreiber des Keycloak muss mitspielen); Token-Speicherung und Verschlüsselung; Keycloak-Ausfall meldet Personen ab |
| **T1-C** Token im Browser (SPA als öffentlicher Client, `keycloak-js`) | Server zustandslos | Verstößt gegen C9 (XSS kann Tokens lesen); ausgeschlossen |

Festlegungen in jeder Option: Sitzungs-Token mit mindestens 128 Bit Zufall, in der Datenbank nur als Hash; Cookie `__Host-`-Präfix, `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/`; Prüfung von `Origin` bei schreibenden Anfragen (CSRF); Abmeldung löscht die Sitzung in Chronos und leitet zum Keycloak-Logout weiter.

### T2 Gast-Identität

Ein Termin-Gastlink wird geteilt (C11). Der Link ist also **keine** Person; der Gast entsteht erst mit der ersten Antwort. Offen ist, wie Chronos ihn beim nächsten Besuch wiedererkennt, auch auf einem anderen Gerät (K-002).

| Option | Vorteile | Nachteile |
|---|---|---|
| **T2-A** Gast-Cookie: Die erste Antwort legt eine Gast-Person an und setzt ein Cookie (wie die Sitzung, aber auf den Link beschränkt, gültig bis Ablauf des Links) | Null zusätzliche Interaktion (C2) | Nur dieses Gerät und dieser Browser; auf einem zweiten Gerät entsteht ein zweiter Gast mit gleichem Namen |
| **T2-B** A + persönlicher Rückkehr-Link: Nach der Antwort zeigt Chronos einen eigenen Link des Gastes („Antwort später ändern“), zum Speichern oder Teilen mit sich selbst | Mehrere Geräte ohne Konto und ohne E-Mail; datensparsam | Der Gast muss den Link aufheben; wer ihn bekommt, kann die Antwort ändern |
| **T2-C** A + optionale E-Mail-Bestätigung (Link per Mail) | Robuste Wiedererkennung; ermöglicht Erinnerungen an Gäste (FA-008 AK 4) | E-Mail-Adresse gespeichert (Datensparsamkeit), Mailkosten (RB-010), mehr Schritte, nur als freiwilliger Zusatz mit C2 vereinbar |
| **T2-D** Namensauswahl („Das bin ich“ aus der Liste der Antwortenden) | Einfach für die Person | Jeder mit dem Link kann fremde Antworten ändern; verstößt gegen FA-005 AK 6 |

Übernahme ins Konto (C12) in jeder Option: Registriert oder meldet sich eine Person an, während ein Gast-Cookie oder Rückkehr-Link vorliegt, bietet Chronos die Übernahme an; eine Operation (z. B. `guest.claim`) überträgt Antworten, Stimmen und Nachrichten auf das Konto, mit Verlaufseintrag (ADR-005, Akteur-Art Gast → Person).

### T3 Ablage und Übertragung der Link-Token

| Option | Vorteile | Nachteile |
|---|---|---|
| **T3-A** Token im **Fragment** der Adresse (`/g#<token>`); die Oberfläche tauscht ihn per `POST` gegen das Gast-Cookie und entfernt ihn aus der Adresse | Fragment wird nicht an den Server gesendet: kein Token in Zugriffsprotokollen, Proxys oder `Referer` | Setzt Skript im Browser voraus (passt nur zu einer SPA oder einer kleinen Skriptseite) |
| **T3-B** Token im Pfad (`/g/<token>`), serverseitig gegen Cookie getauscht und weitergeleitet | Funktioniert ohne Skript (passt zu Server-Rendering) | Token in Zugriffsprotokollen von Ingress und Proxys; dort Maskierung nötig |

In beiden Fällen: In der Datenbank nur der Hash des Tokens; `Referrer-Policy: no-referrer` auf Gastseiten; Widerruf und Ablauf prüft der Geltungsbereich „Gastlink“ im Rahmen der Operationsschicht (ADR-005).

## Teilentscheidungen zu E-004 (Oberfläche)

### T4 Rendering-Ansatz

| Option | Vorteile | Nachteile |
|---|---|---|
| **T4-A** SPA in TypeScript als PWA, statisch gebaut und vom Web-Prozess (axum) unter **derselben Herkunft** ausgeliefert | Nutzt die generierten Typen der Brücke (Q-5); Cookie-Sitzung ohne CORS; Service Worker, Installation und Push ohne Sonderweg; Fragment-Token (T3-A) möglich; Assistent-Dialog mit Zwischenständen gut umsetzbar; Agenten kennen den Stack gut | Zweite Werkzeugkette (npm) und Lieferkette; Bundle-Größe begrenzen (C3, Gastseite als eigener kleiner Einstieg per Code-Splitting); Barrierefreiheit bei Seitenwechseln selbst lösen (siehe T8) |
| **T4-B** Serverseitig gerendert in Rust (askama oder maud) + htmx, Service Worker als kleines Skript | Kleinster Client, schnellste erste Seite; semantisches HTML und echte Navigation bringen Fokus- und Zurück-Verhalten des Browsers mit; eine Sprache | Brücke und Q-5-Vorteil ungenutzt; jede UI-Änderung kostet einen Rust-Build; interaktive Teile (Terminfindung, Assistent-Dialog, Vorschau von Stapeln) mühsam; Link-Token im Pfad (T3-B) |
| **T4-C** Rust/WASM (Leptos, Dioxus) | Eine Sprache, Typen ohne Generator | WASM-Bundle groß für mobil zuerst; Frameworks vor 1.0; wenig barrierefreie Komponenten; Service Worker trotzdem JS |
| **T4-D** Meta-Framework mit Node-Server (Nuxt, SvelteKit SSR) | Bestes SSR- und SPA-Erlebnis | Dritter Prozess mit Node-Grundspeicher; widerspricht ADR-002 und RB-003; ausgeschlossen |

### T5 Framework (nur bei T4-A)

**Überholt:** Die Bewertung nach Vertrautheit ist fachfremd. Die technische Auswahlliste über alle Stile und der Spike-Plan stehen in [E-004-frontend-auswahl](E-004-frontend-auswahl.md).

| Option | Vorteile | Nachteile |
|---|---|---|
| **T5-A** Vue 3 + Vite (ohne Nuxt-Server), Vue Router, vue-i18n | Dem Product Owner vertraut; großes Ökosystem; Laufzeit in der Größenordnung von wenigen Dutzend KB komprimiert ▲ | Größer als Svelte; Zustandsverwaltung und Formulare selbst zusammenstellen |
| **T5-B** Svelte 5 / SvelteKit mit statischem Adapter (ohne Node zur Laufzeit) | Kleinste Bundles; wenig Boilerplate | Dem Product Owner nicht vertraut; kleineres Ökosystem für i18n und Komponenten |
| **T5-C** Angular | Dem Product Owner vertraut; alles aus einer Hand (Router, Formulare, i18n) | Für eine einfache, mobile Oberfläche schwergewichtig; größere Bundles |
| **T5-D** Preact oder Solid | Sehr klein | Weder vertraut noch so verbreitet; weniger Vorbild-Code für Agenten |

### T6 PWA, Service Worker und Push

| Option | Vorteile | Nachteile |
|---|---|---|
| **T6-A** Eigener schlanker Service Worker: Push-Empfang, Benachrichtigungsklick, Installierbarkeit (Manifest); kein Offline-Betrieb | Klein, vollständig verstanden; kein veralteter Cache | Keine Offline-Anzeige |
| **T6-B** Werkzeug für PWA (z. B. `vite-plugin-pwa` mit Workbox), App-Shell im Cache, Push-Code eingebunden | Offline-Start der Oberfläche, Update-Handling fertig | Mehr Abhängigkeiten; Cache-Fehler („alte Version bleibt hängen“) sind schwer zu finden |

Zu beachten: Auf iPhone und iPad funktioniert Web Push nur, wenn die PWA auf dem Home-Bildschirm installiert ist ▲; Gäste installieren in der Regel nicht und bekommen deshalb keinen Push (RA-006, FA-008 AK 4). Die Anmeldung aus einer installierten PWA heraus (Weiterleitung zu Keycloak und zurück) ist auf iOS zu testen ▲. Der öffentliche VAPID-Schlüssel wird als lesende Operation ohne Anmeldung bereitgestellt (schließt ADR-004, offener Punkt 5).

### T7 Übersetzungen (K-007: JSON oder PO, Plural- und Datumsformate)

**Überholt (2026-11-24):** Entschieden ist Fluent auf beiden Seiten ([ADR-010](ADR-010-uebersetzungen-fluent.md)); die Vorgabe „JSON oder PO“ entfällt.

Oberflächentexte braucht nur der Client; Benachrichtigungstexte nur der Server (Worker, je Empfänger). Fehler kommen als Codes (ADR-005) und werden im Client übersetzt. Es gibt also kaum gemeinsame Texte.

| Option | Vorteile | Nachteile |
|---|---|---|
| **T7-A** JSON je Sprache auf beiden Seiten, getrennte Kataloge (`ui/`, `notifications/`); Client mit der i18n-Bibliothek des Frameworks, Server mit eigenem kleinen Nachschlagen; Plural-, Datums- und Zahlformate im Server über ICU4X, im Browser über `Intl` | Passt zu K-007; je Seite das übliche Werkzeug | Zwei Pluralschreibweisen (Client-Bibliothek, Server-Konvention) |
| **T7-B** Fluent (`.ftl`) auf beiden Seiten (`fluent-rs`, `@fluent/bundle`) | Ein Format mit Plural und Geschlecht in der Nachricht | Weder JSON noch PO: K-007 müsste geändert werden; kleineres Ökosystem |
| **T7-C** gettext PO auf beiden Seiten | Ausgereifte Übersetzungswerkzeuge | Im Frontend unüblich; Rust-Crates teils mit C-Bindung |

### T8 Barrierefreiheit (Festlegung, keine echte Alternative)

Vorschlag: **WCAG 2.2 Stufe AA** als Prüfmaßstab der Definition of Done. Bei einer SPA (T4-A) bedeutet das konkret:
- **Seitenwechsel:** Der Fokus geht auf die Hauptüberschrift der neuen Seite, und eine `aria-live="polite"`-Region sagt den Seitentitel an. Der Browser macht das bei einer SPA nicht selbst (WCAG 2.4.3 Fokusreihenfolge, 4.1.3 Statusmeldungen).
- **Ergebnisse ohne Seitenwechsel** (Antwort gespeichert, Assistent antwortet, Vorschau bereit) als Statusmeldung in einer Live-Region, ohne den Fokus zu verschieben (4.1.3).
- **Berührungsflächen** mindestens 24 × 24 CSS-Pixel (2.5.8), wichtig für die Antwort-Knöpfe der Gastseite.
- **Antwortauswahl** (Ja/Vielleicht/Nein) als echte Radiogruppe (`fieldset`/`legend`, `input type="radio"`), nicht als Knöpfe mit Farbe: so erfährt ein Screenreader Gruppe, Wahl und Zustand ohne zusätzliches ARIA (4.1.2, 1.4.1 Farbe nicht allein).
- **Automatisch prüfen:** axe-core in den Oberflächentests; ein manueller Durchlauf mit Tastatur und Screenreader je Feature.

## Wie E-004 und E-008 sich binden

| Wenn … | dann … |
|---|---|
| Cookie-Sitzung (T1-A/B) | Oberfläche und API unter **derselben Herkunft** (Auslieferung durch axum oder gemeinsamer Ingress); sonst CORS und `SameSite=None` |
| Fragment-Token (T3-A) | Skript im Browser nötig: SPA (T4-A) oder eine kleine Skript-Gastseite |
| Server-Rendering (T4-B) | Link-Token im Pfad (T3-B), Maskierung in Protokollen |
| Gäste ohne Installation | kein Push für Gäste auf iOS; Erinnerung nur mit freiwilliger E-Mail (T2-C) |
| Keycloak fällt aus (C16) | Gastseite und bestehende Sitzungen (T1-A) laufen weiter; nur Neuanmeldungen scheitern |

## Gesamtvarianten

| | V1 SPA mit eigener Sitzung | V2 Server-Rendering | V3 SPA mit Refresh-Token |
|---|---|---|---|
| T1 Sitzung | **A** entkoppelt + Back-Channel-Logout | A | B Refresh-Token |
| T2 Gast | **B** Cookie + Rückkehr-Link (C optional später) | B | B |
| T3 Link-Token | **A** Fragment | B Pfad | A |
| T4 Rendering | **A** SPA/PWA aus axum | B askama/maud + htmx | A |
| T5 Framework | **A** Vue 3 (oder B Svelte) | – | A |
| T6 PWA | **A** eigener Service Worker | A | A |
| T7 Texte | **A** JSON, getrennte Kataloge | A (nur Server) | A |

**Bewertung** (`++` sehr gut, `+` gut, `o` mittel, `-` schwach; Einschätzung):

| Kriterium (ADR-001-Rang) | V1 | V2 | V3 |
|---|---|---|---|
| Änderbarkeit: UI-Änderungen, Agenten, Brücke (1) | ++ | o | ++ |
| Bedienbarkeit mobil, Gast in ≤ 3 Interaktionen, Assistent-Dialog (2) | + | + (Gast) / o (Dialog) | + |
| Ressourcen, erste Seite < 1 s (3) | + | ++ | + |
| Sicherheit: C9, Token nicht in Protokollen | ++ | + | ++ |
| Unabhängigkeit vom Keycloak-Betreiber | + (nur Back-Channel-Logout) | + | - (Realm-Einstellungen) |
| Barrierefreiheit „von selbst“ | o (Fokus selbst lösen) | ++ | o |
| Eigenbau und Lieferkette | o (npm dazu) | + | o |

**Einschätzung:** V1 nutzt die Ergebnisse von ADR-004 bis ADR-006 am besten: Die typisierte Brücke, die Vorschau von Stapeln und der Assistent-Dialog sind in einer SPA natürlich. Die eigene Sitzung erfüllt „nicht sichtbar ablaufen“, ohne vom Keycloak-Betreiber Realm-Änderungen zu verlangen. V2 ist für die Gastseite allein am besten (kleinste Seite, Barrierefreiheit durch den Browser), wird aber beim Assistenten und bei der Terminfindung mühsam. Eine Mischform (Gastseite serverseitig, Rest als SPA) ist möglich, verdoppelt aber Vorlagen und Übersetzungen. Bei V1 erreicht ein eigener, kleiner Einstiegspunkt der SPA für die Gastseite (Code-Splitting) einen ähnlichen Effekt.

## Nachteile von V1 (zusammengestellt auf Wunsch des Product Owners, 2026-11-24)

Der Product Owner favorisiert V1. Damit die Entscheidung mit offenen Nachteilen fällt, steht hier alles Nachteilige gesammelt; die Herleitung je Punkt steht in [E-004-frontend-auswahl](E-004-frontend-auswahl.md), Abschnitt 1.

### Echte Nachteile von V1

| Nr. | Nachteil | Gegenmaßnahme (Vorschlag) |
|---|---|---|
| N1 | **Gastseite:** Erst Hülle, dann JavaScript, dann Daten. Der Termin steht nicht in der ersten Antwort (G1, QA-008, Z-004: kalter Cache, Mobilnetz). Code-Splitting ist ein Umweg. | Eigener, minimaler Einstiegspunkt für die Gastseite; die Termindaten werden vom Server vorab als JSON in die HTML-Antwort eingebettet (axum, ohne Node). Messen in Spike F-1 (MF-1, MF-2). |
| N2 | **Ohne JavaScript keine Antwort:** Das Fragment-Token (T3-A) wird per Skript gegen das Gast-Cookie getauscht. | Als Voraussetzung dokumentieren; Hinweisseite für Browser ohne JS (`noscript`). |
| N3 | **Werkzeug größer als die Aufgabe:** RB-011 verlangt eine einfache Oberfläche; echte Interaktivität nur bei Assistent, Stapel-Vorschau und Terminfindung, die SPA macht aber jede Seite zu Client-Code. | Frameworkwahl nach Bundle-Größe und Barrierefreiheit (Spike F-1); Seiten schlank halten. |
| N4 | **Barrierefreiheit nachzubauen:** Fokus und Ansage beim Seitenwechsel (WCAG 2.4.3, 4.1.3) setzt der Browser bei einer SPA nicht. | Einmal im Router-Wrapper lösen (Fokus auf H1, `aria-live="polite"`); axe-core in den Tests; Rollen-basierte Playwright-Tests. |
| N5 | **Zweite Werkzeugkette und Lieferkette** (npm neben cargo, einige hundert Entwicklungsabhängigkeiten; RA-003). | Abhängigkeiten zählen (MF-5), Lockfile, Pipeline-Prüfung wie bei ADR-004. |
| N6 | **Zwei Übersetzungskataloge** (Oberfläche im Client, Benachrichtigungen im Server) mit zwei Pluralschreibweisen (T7-A). | Getrennte Verzeichnisse, ein Test auf Vollständigkeit beider Sprachen. |
| N7 | **Bundle-Größe** muss aktiv begrenzt werden (C3); Zahlen noch ungemessen ▲. | Budget je Einstiegspunkt festlegen, im Build prüfen. |
| N8 | **Framework offen:** Die bisherige Begründung (Vertrautheit) ist fachfremd. | Technische Auswahl per Spike F-1. |

### Nachteile, die V1 mit den anderen Varianten teilt

| Nr. | Nachteil | Anmerkung |
|---|---|---|
| G1 | Sperrung in Keycloak wirkt nur mit eingerichtetem Back-Channel-Logout sofort | hängt vom Keycloak-Betreiber ab (SH-006), Frage 5 |
| G2 | Sitzung im Spike unfertig (Token im Klartext, kein Ablauf, `Secure` fehlt ohne TLS) | Umbau auf Hash, `__Host-`-Präfix, Ablauf, Origin-Prüfung |
| G3 | Gast-Cookie gilt nur für ein Gerät; Rückkehr-Link kann von jedem genutzt werden, der ihn hat | T2-B; freiwillige E-Mail (T2-C) später |
| G4 | Kein Push für Gäste auf iOS ▲ | Gäste installieren selten |
| G5 | OIDC-Weiterleitung aus installierter PWA auf iOS ungetestet ▲ | Test auf Gerät |
| G6 | Brücke wird zur Laufzeit erzeugt (Generator braucht laufenden Server, Node, Netz) | Binärprogramm schreibt die Beschreibung als Datei, Typen entstehen beim Build, Gleichstandstest |

## Fragen an den Product Owner

1. V1 (SPA mit eigener Sitzung), V2 (Server-Rendering) oder V3 (Refresh-Token)?
2. Framework bei V1: Vue 3 (vertraut) oder Svelte (kleiner)?
3. Gast: Rückkehr-Link (T2-B) zum Start, freiwillige E-Mail (T2-C) später?
4. Sitzungsdauer: 30 Tage gleitend, Höchstdauer 180 Tage?
5. Kann der Keycloak-Betreiber für Chronos einen vertraulichen Client mit Back-Channel-Logout und Selbstregistrierung einrichten (SH-006)?
6. WCAG 2.2 AA als Maßstab der Definition of Done?

## Nächster Schritt (Vorschlag)

Nach der Entscheidung: ADR-007 (E-004) und ADR-008 (E-008). Danach ein kurzer Durchstich: Gastseite (Link öffnen, Name, Antwort, Rückkehr-Link) und Anmeldung mit Push auf iPhone (installierte PWA) und Android. Messen: Interaktionen und Zeit bis zur gespeicherten Antwort (C2), Ladezeit der Gastseite auf einem langsamen Mobilnetz (C3), Bundle-Größe.

# K3: Web Push an echte Browser (manueller Test)

Automatisch nicht prüfbar, weil ein echter Browser mit Push-Dienst beteiligt ist. Durchführung je Kandidat, nach bestandener Abnahmesuite.

**Voraussetzungen:** Dienst läuft unter `http://localhost:8080` (localhost zählt als sicherer Kontext); `VAPID_*` sind gesetzt; `STATIC_DIR` enthält `push-test.html` und `sw.js` (liefert V-4); Chrome und Firefox (Desktop) installiert.

1. `http://localhost:8080/static/push-test.html` öffnen, als `alice` anmelden (Token wird im Formular eingefügt oder über `/auth/login`).
2. Schaltfläche **„Abo anlegen“**: Die Seite holt `GET /api/v1/push/vapid-public-key`, registriert `sw.js`, abonniert und ruft `notification.subscribe_push` auf. Erwartet: „Abo gespeichert“.
3. Schaltfläche **„Test-Push senden“** ruft `notification.test_push`. Erwartet: Benachrichtigung erscheint im Browser innerhalb von 10 s; Inhalt enthält `notification.test`.
4. `notification.list` zeigt eine Zeile `channel=webpush`, `result=success`.
5. Wiederholen in Firefox.

**Bestanden (K3)**, wenn Schritte 2 bis 4 in **beiden** Browsern funktionieren und die Verschlüsselung/VAPID-Signatur **ohne eigenen Kryptocode** (nur Bibliothek) umgesetzt ist (README des Kandidaten, Abschnitt „Eigenbau“).

Protokollieren: Browserversionen, Zeit bis zur Anzeige, Auffälligkeiten.

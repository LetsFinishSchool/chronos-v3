"""Erzeugt alle C4-Diagramme (Excalidraw + SVG-Vorschau). Quelle: docs/arc42, Stand der ADRs 2026-11-24."""
import os
from c4lib import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LEG_ALL = [("person", "Person"), ("system", "Chronos (System)"), ("external", "Nachbarsystem"),
           ("container", "Container"), ("component", "Baustein / Komponente")]


# --------------------------------------------------------------------------------------------
def d01():
    d = Diagram("c4-1-systemkontext", "C4 Ebene 1: Systemkontext von Chronos",
                "arc42 Kapitel 3 (Fachlicher und technischer Kontext). Gestrichelt = optional.")
    d.box("L", 60, 230, 260, 110, "Leitungsteam-Mitglied", "person", desc="Plant Teams, Termine, Veranstaltungen; nutzt den Assistenten")
    d.box("G", 60, 430, 260, 110, "Externe Person (Gast)", "person", desc="Antwortet per Link ohne Konto")
    d.box("KA", 60, 640, 260, 100, "Kalender-Apps", "external", desc="webcal-Abruf des persönlichen Feeds")
    d.box("C", 640, 400, 340, 150, "Chronos", "system",
          desc="Terminplanung und Rückmeldung für Leitungsteams; Weboberfläche, KI-Assistent, Feed")
    d.box("PUSH", 400, 90, 250, 100, "Push-Dienste der Browser", "external", desc="Web Push")
    d.box("MAIL", 690, 90, 250, 100, "Mailserver / SMTP", "external", desc="E-Mail, Ersatzkanal")
    d.box("MSG", 980, 90, 250, 100, "Messenger-Anbieter", "external", desc="optional", dashed=True)
    d.box("KC", 1340, 200, 280, 100, "Keycloak (geteilt)", "external", desc="Anmeldung und Identität; keine Passwörter in Chronos")
    d.box("KI", 1340, 350, 280, 110, "KI-Gateway und KI-Anbieter", "external", desc="Nur EU-Datenstandort, OpenAI-kompatibel (ADR-006)")
    d.box("FER", 1340, 510, 280, 100, "Öffentliche Ferien-API", "external", desc="Schulferien, mit Cache")
    d.box("ROOT", 1340, 660, 280, 100, "chronos-root", "external", desc="Altsystem, einmalige wiederholbare Übernahme", dashed=True)
    d.box("S3", 640, 780, 340, 100, "S3-kompatibler EU-Objektspeicher", "external", desc="Verschlüsselte Sicherung")
    d.box("OBS", 1040, 780, 260, 100, "Beobachtung", "external", desc="Metriken und Logs")
    d.edge("L", "C", "Teams, Termine, Rückmeldungen, Assistent-Dialog [HTTPS]", both=True)
    d.edge("G", "C", "Antwort per Link [HTTPS]", both=True)
    d.edge("KA", "C", "webcal-Abruf, Token-URL, iCalendar")
    d.edge("C", "PUSH", "Benachrichtigung")
    d.edge("C", "MAIL", "Benachrichtigung")
    d.edge("C", "MSG", "Benachrichtigung", dashed=True)
    d.edge("C", "KC", "Anmeldung, Sitzung erneuern")
    d.edge("C", "KI", "Dialog, Operationsaufrufe", both=True)
    d.edge("FER", "C", "Schulferien abrufen")
    d.edge("ROOT", "C", "Bestandsdaten (lesend)", dashed=True)
    d.edge("C", "S3", "täglich, clientseitig verschlüsselt")
    d.edge("C", "OBS", "Metriken, Logs, Korrelations-ID")
    d.add_legend([("person", "Person"), ("system", "Chronos"), ("external", "Nachbarsystem")])
    return d


# --------------------------------------------------------------------------------------------
def d02():
    d = Diagram("c4-2-container", "C4 Ebene 2: Container von Chronos",
                "arc42 Kapitel 5 und 7 (ADR-002 Monolith plus Worker, ADR-003, ADR-007, ADR-008, ADR-011). Eine Codebasis, zwei Prozesse, eine Datenbank je Umgebung.")
    oy = 260
    d.box("KAP", 860, 100, 280, 90, "Kalender-Apps", "external", desc="webcal-Abruf")
    d.box("L", 40, oy, 230, 100, "Leitungsteam-Mitglied", "person")
    d.box("G", 40, oy + 130, 230, 100, "Externe Person (Gast)", "person")
    d.boundary("CH", 370, oy - 45, 850, 700, "System Chronos (je Umgebung: prod, staging)")
    d.box("SPA", 420, oy, 260, 110, "Weboberfläche", "container", "Svelte, SPA und PWA",
          "Mobil zuerst; Push-Abo, Service Worker")
    d.box("GAST", 420, oy + 130, 260, 110, "Gastseite", "container", "Svelte, eigener Einstieg",
          "Termin lesen, Antwort speichern; eigener Service Worker")
    d.box("WEB", 860, oy, 310, 160, "Web-Prozess", "container", "Rust, axum",
          "Operationsschicht, Fachbereiche, KI-Assistent, Kalender-Feed, Sitzung (BFF), liefert die SPA aus")
    d.box("WRK", 860, oy + 340, 310, 140, "Worker-Prozess", "container", "Rust, gleiche Codebasis",
          "Zeitauslöser, Zustellung mit Wiederholung, Sitzungs-Heartbeat (6 h)")
    d.box("DB", 420, oy + 340, 260, 110, "PostgreSQL", "database", "eigene Instanz je Umgebung",
          "Fachdaten, Verlauf, Outbox, Sitzungen")
    d.box("MIG", 420, oy + 500, 260, 100, "Migrationsjob", "container", "chronos migrate, sqlx",
          "Helm-Hook vor dem Rollout (ADR-011)")
    X = 1400
    d.box("GW", X, oy, 260, 95, "KI-Gateway", "external", "LiteLLM, Betreiber", "Nur EU-Anbieter (ADR-006)")
    d.box("KC", X, oy + 115, 260, 95, "Keycloak (geteilt)", "external", desc="Authorization Code mit PKCE")
    d.box("FER", X, oy + 230, 260, 95, "Ferien-API", "external", desc="Zuordnung zum Prozess offen")
    d.box("PUSH", X, oy + 345, 260, 95, "Push-Dienste", "external", desc="Web Push")
    d.box("SMTP", X, oy + 460, 260, 95, "SMTP / EU-Anbieter", "external")
    d.box("MSG", X, oy + 575, 260, 95, "Messenger", "external", desc="optional", dashed=True)
    d.box("S3", X, oy + 690, 260, 95, "EU-Objektspeicher (S3)", "external", desc="Ausführung offen (E-010)")
    d.edge("L", "SPA", "nutzt [HTTPS]")
    d.edge("G", "GAST", "öffnet Link")
    d.edge("KAP", "WEB", "iCalendar")
    d.edge("SPA", "WEB", "Operationsaufrufe [JSON]")
    d.edge("GAST", "WEB", "Token tauschen, lesen, antworten")
    d.edge("WEB", "DB", "liest, schreibt, Outbox [SQL]")
    d.edge("WRK", "DB", "Outbox, Sitzungen [SQL]", both=True)
    d.edge("MIG", "DB", "Schema [DDL]")
    d.edge("WEB", "GW", "Dialog")
    d.edge("WEB", "KC", "Anmeldung, Logout; Heartbeat per Worker")
    d.edge("WEB", "FER", "Ferien", dashed=True)
    d.edge("WRK", "PUSH", "zustellen")
    d.edge("WRK", "SMTP", "zustellen")
    d.edge("WRK", "MSG", "zustellen", dashed=True)
    d.edge("DB", "S3", "täglich, verschlüsselt", dashed=True)
    d.add_legend([("person", "Person"), ("container", "Container"), ("external", "Nachbarsystem")])
    return d

# --------------------------------------------------------------------------------------------
def d03():
    d = Diagram("c4-3-komponenten", "C4 Ebene 3: Bausteine (Komponenten) von Web und Worker",
                "arc42 Kapitel 5, Ebene 1. Crate-Zuschnitt (ADR-009) ist noch offen; Pfeile = erlaubte Abhängigkeiten, vom Compiler erzwungen.")
    d.boundary("WEB", 40, 100, 1430, 730, "Web-Prozess")
    d.boundary("FB", 80, 430, 1100, 170, "Fachbereiche (kennen keine Kanäle und Anbieter)")
    d.boundary("QS", 80, 640, 1190, 170, "Querschnitt")
    d.boundary("WRK", 40, 850, 1430, 200, "Worker-Prozess")
    d.boundary("AD", 40, 1080, 1430, 190, "Adapter (kapseln je einen Nachbarn)")
    # Clients
    d.box("UI", 80, 150, 300, 90, "Weboberfläche", "component", desc="Auslieferung der SPA, Gastseite")
    d.box("AS", 500, 150, 300, 90, "KI-Assistent", "component", desc="Dialog, Vorschau, Freigabe")
    d.box("KI", 920, 150, 300, 90, "KI-Adapter", "component", desc="Gateway, nur EU (ADR-006)")
    d.box("OP", 80, 300, 1100, 90, "Operationsschicht mit Rahmen", "component",
          desc="Transaktion, Berechtigung, Verlauf, Ereignis, Vorschau, Freigabe-Beleg, Stapel")
    names = ["Teams und Mitglieder", "Termine, Serien, Veranstaltungen", "Rückmeldung", "Terminfindung", "Labels",
             "Termin-nachrichten", "Zeitraums-regeln"]
    for i, n in enumerate(names):
        d.box("FB%d" % i, 95 + i * 155, 470, 146, 110, n, "component")
    d.box("FD", 1210, 450, 190, 100, "Kalender-Feed", "component", desc="nur lesend, Token")
    # Querschnitt
    d.box("BE", 100, 680, 270, 100, "Berechtigung und Zugang", "component", desc="Mitgliedschaft, Gastlinks, Sitzung (BFF)")
    d.box("VL", 400, 680, 270, 100, "Änderungsverlauf", "component", desc="Akteur, Aktion, Bündel-ID; 30 Tage Wiederherstellung")
    d.box("EV", 700, 680, 270, 100, "Ereignisse", "component", desc="Outbox, benannter Auslöser")
    d.box("KO", 1000, 680, 270, 100, "Kostenerfassung", "component", desc="Posten je Person und Team, KI-Limit")
    # Worker
    d.box("HB", 100, 900, 270, 100, "Sitzungs-Heartbeat", "component", desc="Refresh bei Keycloak alle 6 h")
    d.box("ZT", 400, 900, 270, 100, "Zeitauslöser", "component", desc="Erinnerungen, Fristen, Linkablauf, Löschen nach 30 Tagen")
    d.box("NB", 700, 900, 270, 100, "Benachrichtigung", "component", desc="Empfänger, Bündelung, Wiederholung, Protokoll")
    d.box("KA", 1000, 900, 270, 100, "Kanäle", "component", desc="Push, E-Mail, Messenger")
    # Adapter
    d.box("ID", 100, 1130, 270, 100, "Identität", "component", desc="Keycloak")
    d.box("FE", 400, 1130, 270, 100, "Ferien-Quelle", "component", desc="Zeitraumsregeln, Cache")
    d.box("BK", 700, 1130, 270, 100, "Backup", "component", desc="Zuordnung offen (E-010)", dashed=True)
    d.box("MG", 1000, 1130, 270, 100, "Datenübernahme", "component", desc="Import über die Operationsschicht (Akteur-Art Import)")
    d.edge("UI", "OP", "ruft Operationen")
    d.edge("AS", "OP", "mit den Rechten der Person")
    d.edge("AS", "KI", "Dialog")
    d.edge("KI", "KO", "Posten, Limit", via=[(1440, 195), (1440, 730)])
    d.edge("OP", "FB", "")
    d.edge("OP", "BE", "prüft Zugriff", via=[(62, 345), (62, 730)])
    d.edge("FD", "FB", "liest")
    d.edge("FB", "VL", "")
    d.edge("FB", "EV", "erzeugt")
    d.edge("ZT", "EV", "zeitgesteuerte Ereignisse")
    d.edge("EV", "NB", "Outbox abarbeiten")
    d.edge("NB", "KA", "zustellen")
    d.edge("KA", "KO", "Kostenposten")
    d.edge("BE", "ID", "Anmeldung", via=[(52, 730), (52, 1180)])
    d.edge("HB", "ID", "Token erneuern")
    d.add_legend([("component", "Baustein")])
    return d


# --------------------------------------------------------------------------------------------
def d04():
    d = Diagram("c4-3-komponenten-rahmen", "C4 Ebene 3: Rahmen der Operationsschicht",
                "arc42 Kapitel 5, Ebene 2 (ADR-005 V2: Der Rahmen trägt den Querschnitt, Operationen enthalten nur Fachlogik).")
    d.box("CALL", 60, 100, 250, 70, "Aufrufer", "external", desc="Oberfläche, Assistent, Worker, Import")
    d.box("BEL", 1220, 100, 250, 70, "Freigabe-Beleg", "component", desc="gültig 10 Minuten")
    d.boundary("R", 40, 250, 1470, 300, "Rahmen (ADR-005)")
    xs = [60, 350, 640, 930, 1220]
    steps = [("S1", "1 Transaktion öffnen", "Lesende Operationen als READ ONLY"),
             ("S2", "2 Geltungsbereich prüfen", "Aus den Parametern ableiten, gegen Akteur-Art prüfen; erzeugt geprüften Kontext (ohne Adapter)"),
             ("S3", "3 Fachlogik ausführen", "Änderungen und Ereignisse werden gesammelt"),
             ("S4", "4 Verlauf und Outbox schreiben", "Akteur und Bündel-ID, in derselben Transaktion"),
             ("S5", "5 Commit oder Rollback", "Vorschau: Probelauf mit Rollback; Stapel max. 50 Aufrufe oder 500 Objekte")]
    for x, (i, n, t) in zip(xs, steps):
        d.box(i, x, 300, 250, 200, n, "component", desc=t)
    d.box("BER", 350, 620, 250, 90, "Berechtigungskonzept", "component", desc="K-002")
    d.box("OPR", 640, 620, 250, 90, "Operation", "component", desc="Trait: Name, Schema, Bereich; Registrierung über inventory")
    d.box("DB", 1060, 620, 380, 90, "PostgreSQL", "database", desc="Fachdaten, Verlauf, Outbox")
    d.edge("CALL", "S1", "Aufruf: Name, Params, Modus")
    for a, b in [("S1", "S2"), ("S2", "S3"), ("S3", "S4"), ("S4", "S5")]:
        d.edge(a, b)
    d.edge("S2", "BER", "Bereich und Akteur-Art", both=True)
    d.edge("OPR", "S3", "Fachlogik")
    d.edge("S4", "DB", "schreibt")
    d.edge("S5", "DB", "commit oder rollback")
    d.edge("S5", "BEL", "stellt aus (Vorschau)")
    d.add_legend([("component", "Schritt / Komponente"), ("external", "Aufrufer")])
    return d


# --------------------------------------------------------------------------------------------
def d05():
    d = Diagram("c4-dynamisch-l2-termin-aendern", "C4 Dynamisch: L-2 Termin ändern und Benachrichtigung zustellen",
                "arc42 Kapitel 6. Das Ereignis ist vor der Zustellung dauerhaft festgehalten (Outbox); höchstens eine Zustellung je Empfänger und Kanal.")
    d.box("M", 40, 170, 230, 100, "Mitglied", "person")
    d.box("OP", 440, 170, 250, 100, "Operationsschicht", "component", "Web-Prozess")
    d.box("TE", 870, 170, 250, 100, "Termine", "component", "Web-Prozess")
    d.box("VL", 1300, 170, 250, 100, "Änderungsverlauf", "component", "Web-Prozess")
    d.box("EV", 870, 420, 250, 100, "Ereignisse", "component", "Web-Prozess, Outbox")
    d.box("NB", 440, 410, 250, 130, "Benachrichtigung", "component", "Worker-Prozess", "Protokoll: Auslöser, Empfänger, Kanal, Ergebnis")
    d.box("PU", 40, 680, 230, 100, "Kanal Push", "component", "Worker-Prozess")
    d.box("EM", 440, 680, 250, 100, "Kanal E-Mail", "component", "Worker-Prozess")
    d.box("KO", 870, 680, 250, 100, "Kostenerfassung", "component")
    d.edge("M", "OP", "1 Termin verschieben")
    d.edge("OP", "TE", "2 ändern")
    d.edge("TE", "VL", "3 Eintrag mit Akteur, Vorher-Zustand")
    d.edge("TE", "EV", "4 Ereignis „Termin geändert“, Auslöser, Korrelations-ID")
    d.edge("EV", "NB", "5 festhalten, Empfänger bestimmen")
    d.edge("NB", "PU", "6 zustellen: fehlgeschlagen")
    d.edge("NB", "EM", "7 Ersatzkanal, sofern erlaubt")
    d.edge("EM", "KO", "8 Kostenposten (E-Mail)")
    d.add_legend([("person", "Person"), ("component", "Baustein")])
    return d

def d06():
    d = Diagram("c4-dynamisch-l4-assistent", "C4 Dynamisch: L-4 Assistent mit Vorschau und Freigabe",
                "arc42 Kapitel 6 (ADR-005, ADR-006). Ohne Freigabe wird nichts geschrieben; lesende Operationen brauchen keine Freigabe.")
    d.box("M", 40, 340, 250, 120, "Mitglied", "person", desc="„Sage alle Termine in den Herbstferien ab“")
    d.box("AS", 560, 340, 280, 120, "KI-Assistent", "component", "Web-Prozess", "Dialogschleife im Server")
    d.box("KO", 560, 80, 280, 100, "Kostenerfassung", "component", desc="Monatslimit je Team")
    d.box("GW", 1140, 80, 300, 110, "KI-Gateway und Anbieter", "external", desc="EU-Datenstandort")
    d.box("OP", 1140, 600, 300, 140, "Operationsschicht", "component", desc="Vorschau (Probelauf), Beleg, Ausführung; Verlauf „durch Assistent im Auftrag von …“")
    d.edge("M", "AS", "1 Auftrag", off=-40)
    d.edge("AS", "M", "8 Vorschau anzeigen", off=0)
    d.edge("M", "AS", "9 Freigabe", off=40)
    d.edge("AS", "KO", "2 Limit prüfen", off=-30, lt=0.35)
    d.edge("AS", "KO", "5 Kostenposten (Kopfzeilen)", off=30, lt=0.65)
    d.edge("AS", "GW", "3 Dialog (auch Fehlversuch zählt)", off=-26, lt=0.4)
    d.edge("GW", "AS", "4 geplante Operation", off=-26, lt=0.4)
    d.edge("AS", "OP", "6 Vorschau anfordern (lesend), 7 zurück: Änderungen, Anzahl, Beleg", both=True, off=-50)
    d.edge("AS", "OP", "10 ausführen mit Beleg (Rechte der Person, Bündel-ID), 11 zurück: Ergebnis", both=True, off=50)
    d.add_legend([("person", "Person"), ("component", "Baustein"), ("external", "Nachbarsystem")])
    return d

def d07():
    d = Diagram("c4-dynamisch-l1-gastlink", "C4 Dynamisch: L-1 Antwort über Gastlink",
                "arc42 Kapitel 6 (ADR-008). Antwort in höchstens 3 Interaktionen; ein widerrufener oder abgelaufener Link liefert keine Daten.")
    d.box("G", 40, 300, 220, 100, "Gast", "person")
    d.box("UI", 440, 300, 240, 100, "Gastseite", "container", "Svelte")
    d.box("OP", 860, 300, 250, 100, "Operationsschicht", "component", "Web-Prozess")
    d.box("BE", 1300, 100, 300, 110, "Berechtigung und Zugang", "component", desc="Token: gültig, nicht widerrufen, nicht abgelaufen")
    d.box("RM", 1300, 440, 300, 100, "Rückmeldung", "component")
    d.box("EV", 1300, 680, 300, 100, "Ereignisse", "component", desc="Outbox")
    d.edge("G", "UI", "1 Link öffnen, Namen angeben, antworten")
    d.edge("UI", "OP", "2 Antwort setzen (Token, Name, Antwort)", off=-24, lt=0.4)
    d.edge("OP", "UI", "7 bestätigt", off=-24, lt=0.5)
    d.edge("OP", "BE", "3 Token prüfen", off=-26, lt=0.4)
    d.edge("BE", "OP", "4 Gast-Person für diesen Termin", off=-26, lt=0.5)
    d.edge("OP", "RM", "5 Rückmeldung speichern")
    d.edge("RM", "EV", "6 Ereignis „Rückmeldung geändert“")
    d.add_legend([("person", "Person"), ("container", "Container"), ("component", "Baustein")])
    return d

# --------------------------------------------------------------------------------------------
def d08():
    d = Diagram("c4-deployment", "C4 Deployment: k3s-Cluster, prod und staging",
                "arc42 Kapitel 7 (RB-003, RB-005, ADR-002, ADR-003, ADR-011). Je Umgebung 1 vCPU und 1 GiB; Manifeste im Repository, per CI angewendet.")
    d.box("KI", 560, 100, 230, 90, "KI-Gateway", "external", desc="LiteLLM, Betreiber; Ort offen")
    d.box("FER", 810, 100, 230, 90, "Ferien-API", "external")
    d.box("PUSH", 1060, 100, 230, 90, "Push-Dienste", "external")
    d.box("SMTP", 1310, 100, 230, 90, "SMTP / EU-Anbieter", "external")
    d.box("BR", 40, 330, 240, 110, "Browser / Smartphone", "external", desc="SPA, PWA, Service Worker")
    d.box("KAP", 40, 480, 240, 90, "Kalender-Apps", "external")
    d.boundary("CL", 340, 230, 1040, 700, "Geteilter k3s-Cluster (3 Nodes)")
    d.box("KC", 370, 270, 220, 100, "Keycloak", "external", desc="geteilt, nicht im Budget")
    d.box("ING", 370, 400, 220, 100, "Ingress", "container", desc="HTTPS")
    d.boundary("PROD", 640, 260, 700, 300, "Chronos prod (Limit 1 vCPU, 1 GiB)")
    d.box("WP", 670, 300, 240, 90, "Web", "container", "Container, eigenes Image")
    d.box("RP", 950, 300, 240, 90, "Worker", "container", "Container, eigenes Image")
    d.box("JP", 670, 440, 200, 90, "Migrationsjob", "container", "Helm-Hook")
    d.box("DP", 910, 440, 260, 90, "PostgreSQL", "database", "eigene Instanz")
    d.boundary("STG", 640, 600, 700, 300, "Chronos staging (Limit 1 vCPU, 1 GiB, eigene Testdaten)")
    d.box("WS", 670, 640, 240, 90, "Web", "container", "Container, eigenes Image")
    d.box("RS", 950, 640, 240, 90, "Worker", "container", "Container, eigenes Image")
    d.box("JS", 670, 780, 200, 90, "Migrationsjob", "container", "Helm-Hook")
    d.box("DS", 910, 780, 260, 90, "PostgreSQL", "database", "eigene Instanz")
    d.box("S3", 1450, 440, 220, 100, "S3-kompatibler EU-Speicher", "external", desc="Sicherung, RPO 24 h")
    d.edge("BR", "ING", "HTTPS")
    d.edge("KAP", "ING", "webcal")
    d.edge("ING", "WP", "")
    d.edge("ING", "WS", "")
    d.edge("WP", "KC", "OIDC")
    d.edge("WP", "KI", "Dialog")
    d.edge("WP", "FER", "")
    d.edge("RP", "PUSH", "")
    d.edge("RP", "SMTP", "")
    for a, b in [("WP", "DP"), ("RP", "DP"), ("JP", "DP"), ("WS", "DS"), ("RS", "DS"), ("JS", "DS")]:
        d.edge(a, b)
    d.edge("DP", "S3", "täglich, clientseitig verschlüsselt")
    d.add_legend([("external", "Nachbarsystem"), ("container", "Container"), ("database", "Datenbank")])
    return d


if __name__ == "__main__":
    for f in (d01, d02, d03, d04, d05, d06, d07, d08):
        f().write(OUT)
        print("ok", f.__name__)

---
id: RA-009
title: Budget und Abhängigkeit von Keycloak
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: risiko
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: []
---

# RA-009: Budget und Abhängigkeit von Keycloak

Entscheidung: Betrieb im bestehenden Cluster-Budget; Zusatzkosten gering (Backup-Speicher, E-Mail, KI mit Monatslimit je Team). Obergrenze: 10 € pro Monat für Zusatzkosten (ohne Cluster und Personal). Bei Erreichen pausiert die KI bis Monatsende, Backup und E-Mail laufen weiter, der Betreiber wird benachrichtigt.

Risiko: Das Ressourcenbudget ([RB-003](../07-randbedingungen/RB-003-ressourcenbudget.md)) begrenzt Technikwahl; fällt Keycloak aus, kann sich niemand neu anmelden (Gäste mit Link bleiben nutzbar).

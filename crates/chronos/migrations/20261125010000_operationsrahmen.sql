-- Minimalstand des Operationsrahmens (ADR-005, K-003, K-004).

-- Kennung und Art jedes Akteurs; Keycloak-Anbindung und Profil erweitern die Tabelle später.
CREATE TABLE person (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    art text NOT NULL CHECK (art IN ('person', 'gast')),
    angelegt_am timestamptz NOT NULL DEFAULT now()
);

-- Ein Eintrag je geänderter Objektzustand. `vorher` hält den Zustand vor der Änderung,
-- damit der volle Verlaufsmechanismus (#34) darauf aufbauen kann.
CREATE TABLE verlauf (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    akteur uuid NOT NULL REFERENCES person (id),
    zeitpunkt timestamptz NOT NULL DEFAULT now(),
    aktion text NOT NULL,
    objekt_art text NOT NULL,
    objekt_id uuid NOT NULL,
    vorher jsonb,
    korrelations_id uuid NOT NULL,
    buendel_id uuid
);

-- Ereignisse entstehen in derselben Transaktion wie die Fachänderung; der Worker
-- arbeitet sie später ab (K-003).
CREATE TABLE outbox (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ereignis text NOT NULL,
    nutzdaten jsonb NOT NULL,
    ausloeser uuid NOT NULL REFERENCES person (id),
    korrelations_id uuid NOT NULL,
    erstellt_am timestamptz NOT NULL DEFAULT now(),
    verarbeitet_am timestamptz
);

CREATE INDEX outbox_offen ON outbox (id) WHERE verarbeitet_am IS NULL;

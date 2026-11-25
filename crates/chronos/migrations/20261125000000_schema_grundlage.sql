-- Grundlage für alle Migrationen: Rechte des Anwendungsbenutzers (ADR-011, Punkt 8).
-- Die Rollen legt die Bereitstellung an (tools/db/init-roles.sql lokal und in CI).

-- sqlx legt _sqlx_migrations vor der ersten Migration an; Web und Worker lesen daraus
-- die Schemaversion.
GRANT SELECT ON _sqlx_migrations TO chronos_app;

-- Tabellen und Sequenzen späterer Migrationen brauchen so keine eigenen GRANTs.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO chronos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO chronos_app;

-- Legt die beiden Datenbankbenutzer an (ADR-011, Punkt 8). Läuft nur lokal und in CI;
-- im Cluster legt die Bereitstellung die Rollen an (RB-008). Die Passwörter sind
-- Wegwerfwerte und gehören nie in eine echte Umgebung.
--
-- Aufruf als Superuser gegen die Datenbank `chronos`:
--   psql "$SUPERUSER_URL" -v ON_ERROR_STOP=1 -f tools/db/init-roles.sql

-- CREATEDB braucht `#[sqlx::test]` für je eine frische Datenbank pro Test.
CREATE ROLE chronos_migrate LOGIN CREATEDB PASSWORD 'chronos_migrate';
CREATE ROLE chronos_app LOGIN PASSWORD 'chronos_app';

-- PostgreSQL erlaubt jedem CREATE im Schema public nicht mehr (ab 15), aber der
-- Besitzer muss ausdrücklich der Migrationsbenutzer sein.
ALTER DATABASE chronos OWNER TO chronos_migrate;
ALTER SCHEMA public OWNER TO chronos_migrate;
REVOKE ALL ON DATABASE chronos FROM PUBLIC;
GRANT CONNECT ON DATABASE chronos TO chronos_app;
GRANT USAGE ON SCHEMA public TO chronos_app;

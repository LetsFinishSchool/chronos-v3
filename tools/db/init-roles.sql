-- Creates the two database users (ADR-011, point 8). Runs only locally and in CI;
-- in the cluster the deployment creates the roles (RB-008). The passwords are
-- throwaway values and never belong in a real environment.
--
-- Call as superuser against the database `chronos`:
--   psql "$SUPERUSER_URL" -v ON_ERROR_STOP=1 -f tools/db/init-roles.sql

-- CREATEDB is needed by `#[sqlx::test]` for a fresh database per test.
CREATE ROLE chronos_migrate LOGIN CREATEDB PASSWORD 'chronos_migrate';
CREATE ROLE chronos_app LOGIN PASSWORD 'chronos_app';

-- Since version 15 PostgreSQL no longer lets everyone CREATE in schema public, but the
-- owner must explicitly be the migration user.
ALTER DATABASE chronos OWNER TO chronos_migrate;
ALTER SCHEMA public OWNER TO chronos_migrate;
REVOKE ALL ON DATABASE chronos FROM PUBLIC;
GRANT CONNECT ON DATABASE chronos TO chronos_app;
GRANT USAGE ON SCHEMA public TO chronos_app;

-- docker/postgres/init-extensions.sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age;
SET search_path = ag_catalog, "$user", public;

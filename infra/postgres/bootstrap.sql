-- Идемпотентно: роли создаются, если их нет; пароли обновляются всегда.
-- Порядок: роли -> пароли -> \connect -> схемы -> владельцы -> гранты -> таймауты.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'parser_writer')  THEN CREATE ROLE parser_writer  LOGIN; END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'backend_writer') THEN CREATE ROLE backend_writer LOGIN; END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'matcher_writer') THEN CREATE ROLE matcher_writer LOGIN; END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'catalog_ro')     THEN CREATE ROLE catalog_ro     NOLOGIN; END IF;
END $$;

ALTER ROLE parser_writer  WITH PASSWORD :'parser_pw';
ALTER ROLE backend_writer WITH PASSWORD :'backend_pw';
ALTER ROLE matcher_writer WITH PASSWORD :'matcher_pw';

\connect :"app_db"

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS parser;
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS matcher;

ALTER SCHEMA parser  OWNER TO parser_writer;
ALTER SCHEMA catalog OWNER TO parser_writer;
ALTER SCHEMA core    OWNER TO backend_writer;
ALTER SCHEMA matcher OWNER TO matcher_writer;

GRANT USAGE ON SCHEMA catalog TO catalog_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA catalog TO catalog_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE parser_writer IN SCHEMA catalog
    GRANT SELECT ON TABLES TO catalog_ro;
GRANT catalog_ro TO backend_writer, matcher_writer;

REVOKE ALL ON SCHEMA parser, core, matcher FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

ALTER ROLE matcher_writer SET statement_timeout = '5s';
ALTER ROLE backend_writer SET statement_timeout = '5s';
ALTER ROLE parser_writer  SET statement_timeout = '60s';
ALTER ROLE matcher_writer SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE backend_writer SET idle_in_transaction_session_timeout = '30s';
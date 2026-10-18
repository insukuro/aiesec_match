-- Идемпотентно: роли создаются, если нет; пароли обновляются всегда.
-- Запускается из db-init на каждом `docker compose up`.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'parser_writer') THEN
        CREATE ROLE parser_writer LOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'backend_reader') THEN
        CREATE ROLE backend_reader LOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'backend_writer') THEN
        CREATE ROLE backend_writer LOGIN;
    END IF;
END
$$;

ALTER ROLE parser_writer   WITH PASSWORD :'parser_pw';
ALTER ROLE backend_reader  WITH PASSWORD :'backend_pw';
ALTER ROLE backend_writer  WITH PASSWORD :'backend_pw';

\connect :"parser_db"

GRANT CONNECT ON DATABASE :"parser_db" TO parser_writer, backend_reader, backend_writer;

-- Схемы: владелец parser_writer, но создаются от platform (суперюзер).
-- IF NOT EXISTS — идемпотентно.
CREATE SCHEMA IF NOT EXISTS raw AUTHORIZATION parser_writer;
CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION parser_writer;

GRANT USAGE, CREATE ON SCHEMA raw TO parser_writer;
GRANT USAGE, CREATE ON SCHEMA app TO parser_writer;

GRANT USAGE ON SCHEMA app TO backend_reader, backend_writer;
GRANT USAGE ON SCHEMA raw TO backend_reader, backend_writer;
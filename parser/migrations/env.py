from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, inspect, pool

from app.config import Settings
from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = Settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def _require_schemas(connection) -> None:
    """Схемы создаёт db-init (bootstrap.sql). Здесь — только проверка.
    Если схемы нет — даём понятную ошибку вместо невнятного 'schema does not exist'."""
    existing = set(inspect(connection).get_schema_names())
    for schema in filter(None, [settings.db_schema, "app"]):
        if schema not in existing:
            raise RuntimeError(
                f"Схема '{schema}' не существует в БД. "
                f"Проверьте: docker compose logs db-init. "
                f"Если db-init не отработал — пересоздайте инфраструктуру: "
                f"docker compose down -v && docker compose up -d"
            )


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=settings.db_schema or None,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        _require_schemas(connection)
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=settings.db_schema or None,
            include_schemas=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
# Data Flow Diagrams

Эта папка содержит reverse-engineering DFD для проекта `aiesec_match`. Диаграммы построены по фактическому исполняемому коду; противоречия с документацией разрешаются в пользу реализации.

## Files

| Diagram | Purpose |
|---|---|
| `00_system_context.drawio` | Context: system and confirmed external entities |
| `01_system_level_0.drawio` | Main processes and logical stores |
| `02_authentication_account.drawio` | Registration, login, JWT, Telegram and account management |
| `03_profile_questionnaire.drawio` | Form, validation, normalization, profile versions and consents |
| `04_opportunity_catalog_parser.drawio` | AIESEC API, OAuth, sync strategies, ingest and parser stores |
| `05_matching_recommendations.drawio` | Backend-to-matcher flow, filters, scoring and persistence |
| `06_feedback_history_analytics.drawio` | Feedback, history and analytical aggregation |
| `07_notifications_outbox.drawio` | Subscription, outbox, external Telegram lease/ack and in-app read state |
| `08_database_data_stores.drawio` | PostgreSQL logical stores and process read/write relations |

## Notation

- **External Entity**: blue rectangle.
- **Process**: yellow ellipse/rounded process with hierarchical number.
- **Data Store**: grey open-style rectangle.
- **Data Flow**: directed arrow with a label naming transferred data.
- **Trust Boundary**: dashed grey frame around a trust domain.

Arrows describe data movement, not structural dependencies. Edges labeled `UNVERIFIED` are explicitly not confirmed as implementation facts.

## Opening

Open each `.drawio` file directly in VS Code with a draw.io extension or in diagrams.net:

1. Open <https://app.diagrams.net/>.
2. Choose **File > Open From > Device**.
3. Select the desired file from `docs/dfd/`.

All diagrams are separate native draw.io XML files and remain editable.

## Scope and Sources

Primary sources: Python/FastAPI implementation, SQLAlchemy models, Alembic migrations, Docker Compose configuration, frontend API client, OpenAPI and pytest sources. `architecture_inventory.md` records component inputs, outputs, stores and source evidence.

## Known Limits

- No Telegram bot sender/consumer implementation is present in the repository. Telegram is therefore shown as an external entity connected only by backend internal endpoints.
- The exact mechanism/materialized relation populating `catalog.*` from `parser.*` was not established by executable application code and is marked `UNVERIFIED`.
- A parser's `retry`-related outbox state exists, but an implemented repeated-delivery loop was not found.
- The email sender is not implemented; email-change code delivery behavior is only in the API implementation.

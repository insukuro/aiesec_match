# aiesec-platform (монорепо)


## Быстрый старт

```bash
cp .env.example .env     # заполнить AIESEC_TOKEN, PARSER_API_KEY, POSTGRES_PASSWORD
make up                  # postgres + парсер; первый full-sync стартует сам
```


```
aiesec_match
├─ .dockerignore
├─ .ruff_cache
│  ├─ 0.17.5
│  │  ├─ 6609985663905342634
│  │  └─ 8213006384568045760
│  └─ CACHEDIR.TAG
├─ Makefile
├─ README.md
├─ backend
│  ├─ alembic.ini
│  ├─ app
│  │  ├─ __init__.py
│  │  ├─ __pycache__
│  │  │  ├─ __init__.cpython-312.pyc
│  │  │  ├─ config.cpython-312.pyc
│  │  │  ├─ db.cpython-312.pyc
│  │  │  ├─ errors.cpython-312.pyc
│  │  │  ├─ formschema.cpython-312.pyc
│  │  │  ├─ main.cpython-312.pyc
│  │  │  └─ schemas.cpython-312.pyc
│  │  ├─ api
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ analytics.cpython-312.pyc
│  │  │  │  ├─ auth.cpython-312.pyc
│  │  │  │  ├─ feedback.cpython-312.pyc
│  │  │  │  ├─ health.cpython-312.pyc
│  │  │  │  ├─ history.cpython-312.pyc
│  │  │  │  ├─ internal_notifications.cpython-312.pyc
│  │  │  │  ├─ me.cpython-312.pyc
│  │  │  │  ├─ meta.cpython-312.pyc
│  │  │  │  ├─ notifications.cpython-312.pyc
│  │  │  │  ├─ opportunities.cpython-312.pyc
│  │  │  │  ├─ profiles.cpython-312.pyc
│  │  │  │  ├─ recommendations.cpython-312.pyc
│  │  │  │  └─ subscriptions.cpython-312.pyc
│  │  │  ├─ analytics.py
│  │  │  ├─ auth.py
│  │  │  ├─ feedback.py
│  │  │  ├─ health.py
│  │  │  ├─ history.py
│  │  │  ├─ internal_notifications.py
│  │  │  ├─ me.py
│  │  │  ├─ meta.py
│  │  │  ├─ notifications.py
│  │  │  ├─ opportunities.py
│  │  │  ├─ profiles.py
│  │  │  ├─ recommendations.py
│  │  │  └─ subscriptions.py
│  │  ├─ application
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ analytics_service.cpython-312.pyc
│  │  │  │  ├─ auth_service.cpython-312.pyc
│  │  │  │  ├─ catalog_service.cpython-312.pyc
│  │  │  │  ├─ consent_service.cpython-312.pyc
│  │  │  │  ├─ deps.cpython-312.pyc
│  │  │  │  ├─ dto_mappers.cpython-312.pyc
│  │  │  │  ├─ feedback_service.cpython-312.pyc
│  │  │  │  ├─ history_service.cpython-312.pyc
│  │  │  │  ├─ link_code_service.cpython-312.pyc
│  │  │  │  ├─ matching_service.cpython-312.pyc
│  │  │  │  ├─ me_service.cpython-312.pyc
│  │  │  │  ├─ meta_service.cpython-312.pyc
│  │  │  │  ├─ notification_service.cpython-312.pyc
│  │  │  │  ├─ profile_service.cpython-312.pyc
│  │  │  │  └─ subscription_service.cpython-312.pyc
│  │  │  ├─ analytics_service.py
│  │  │  ├─ auth_service.py
│  │  │  ├─ catalog_service.py
│  │  │  ├─ consent_service.py
│  │  │  ├─ deps.py
│  │  │  ├─ dto_mappers.py
│  │  │  ├─ feedback_service.py
│  │  │  ├─ history_service.py
│  │  │  ├─ link_code_service.py
│  │  │  ├─ matching_service.py
│  │  │  ├─ me_service.py
│  │  │  ├─ meta_service.py
│  │  │  ├─ notification_service.py
│  │  │  ├─ profile_service.py
│  │  │  └─ subscription_service.py
│  │  ├─ config.py
│  │  ├─ db.py
│  │  ├─ domain
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ age.cpython-312.pyc
│  │  │  │  ├─ completeness.cpython-312.pyc
│  │  │  │  └─ scoring.cpython-312.pyc
│  │  │  ├─ age.py
│  │  │  ├─ completeness.py
│  │  │  └─ scoring.py
│  │  ├─ errors.py
│  │  ├─ forms
│  │  │  ├─ consents.v1.yaml
│  │  │  └─ form_schema.v2.yaml
│  │  ├─ formschema.py
│  │  ├─ infrastructure
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ matcher_client.cpython-312.pyc
│  │  │  │  ├─ telegram_adapter.cpython-312.pyc
│  │  │  │  └─ time_utils.cpython-312.pyc
│  │  │  ├─ matcher_client.py
│  │  │  ├─ models
│  │  │  │  ├─ __init__.py
│  │  │  │  ├─ __pycache__
│  │  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  │  ├─ catalog.cpython-312.pyc
│  │  │  │  │  └─ core.cpython-312.pyc
│  │  │  │  ├─ catalog.py
│  │  │  │  └─ core.py
│  │  │  ├─ repositories
│  │  │  │  ├─ __init__.py
│  │  │  │  ├─ __pycache__
│  │  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  │  ├─ catalog_repo.cpython-312.pyc
│  │  │  │  │  ├─ consent_repo.cpython-312.pyc
│  │  │  │  │  ├─ feedback_repo.cpython-312.pyc
│  │  │  │  │  ├─ link_code_repo.cpython-312.pyc
│  │  │  │  │  ├─ outbox_repo.cpython-312.pyc
│  │  │  │  │  ├─ profile_repo.cpython-312.pyc
│  │  │  │  │  ├─ run_repo.cpython-312.pyc
│  │  │  │  │  ├─ subscription_repo.cpython-312.pyc
│  │  │  │  │  └─ user_repo.cpython-312.pyc
│  │  │  │  ├─ catalog_repo.py
│  │  │  │  ├─ consent_repo.py
│  │  │  │  ├─ feedback_repo.py
│  │  │  │  ├─ link_code_repo.py
│  │  │  │  ├─ outbox_repo.py
│  │  │  │  ├─ profile_repo.py
│  │  │  │  ├─ run_repo.py
│  │  │  │  ├─ subscription_repo.py
│  │  │  │  └─ user_repo.py
│  │  │  ├─ telegram_adapter.py
│  │  │  └─ time_utils.py
│  │  ├─ main.py
│  │  └─ schemas.py
│  ├─ migrations
│  │  ├─ README
│  │  ├─ env.py
│  │  ├─ script.py.mako
│  │  └─ versions
│  │     ├─ 0001_core.py
│  │     ├─ 0002_auth.py
│  │     ├─ 0003_auth.py
│  │     ├─ 0004_feedback_unique.py
│  │     ├─ 0005_drop_anonymous.py
│  │     ├─ 0006_missing_scenarios.py
│  │     └─ __pycache__
│  │        ├─ 0001_core.cpython-312.pyc
│  │        └─ 71ae476ee49e_.cpython-312.pyc
│  ├─ openapi
│  │  └─ backend.v1.json
│  ├─ pytest.ini
│  ├─ tests
│  │  ├─ conftest.py
│  │  ├─ test_age.py
│  │  ├─ test_api_auth.py
│  │  ├─ test_api_feedback.py
│  │  ├─ test_api_profiles.py
│  │  ├─ test_api_recommendations.py
│  │  ├─ test_auth_unit.py
│  │  ├─ test_completeness.py
│  │  ├─ test_concurrency.py
│  │  ├─ test_errors.py
│  │  ├─ test_matcher_client.py
│  │  └─ test_schemas_unit.py
│  └─ workers
│     └─ outbox.py
├─ docker-compose.dev.yml
├─ docker-compose.test.yml
├─ docker-compose.yml
├─ docs
│  ├─ README.md
│  └─ testing.md
├─ htmlcov
│  ├─ class_index.html
│  ├─ coverage_html_cb_54cfdca1.js
│  ├─ favicon_32_cb_c827f16f.png
│  ├─ function_index.html
│  ├─ index.html
│  ├─ keybd_closed_cb_900cfef5.png
│  ├─ status.json
│  ├─ style_cb_4667309f.css
│  ├─ z_5f5a17c013354698___init___py.html
│  ├─ z_5f5a17c013354698_age_py.html
│  ├─ z_5f5a17c013354698_auth_py.html
│  ├─ z_5f5a17c013354698_catalog_py.html
│  ├─ z_5f5a17c013354698_client_py.html
│  ├─ z_5f5a17c013354698_completeness_py.html
│  ├─ z_5f5a17c013354698_config_py.html
│  ├─ z_5f5a17c013354698_db_py.html
│  ├─ z_5f5a17c013354698_errors_py.html
│  ├─ z_5f5a17c013354698_formschema_py.html
│  ├─ z_5f5a17c013354698_main_py.html
│  ├─ z_5f5a17c013354698_matcher_client_py.html
│  ├─ z_5f5a17c013354698_models_py.html
│  ├─ z_5f5a17c013354698_normalize_py.html
│  ├─ z_5f5a17c013354698_schemas_py.html
│  ├─ z_5f5a17c013354698_tokens_py.html
│  ├─ z_bcd186691859bdf8___init___py.html
│  ├─ z_bcd186691859bdf8_gapfill_py.html
│  ├─ z_bcd186691859bdf8_ingest_py.html
│  ├─ z_bcd186691859bdf8_queries_py.html
│  ├─ z_bcd186691859bdf8_service_py.html
│  ├─ z_bcd186691859bdf8_state_py.html
│  ├─ z_bcd186691859bdf8_strategies_py.html
│  ├─ z_cfb6adc3f81c8e3c___init___py.html
│  ├─ z_cfb6adc3f81c8e3c_admin_py.html
│  ├─ z_cfb6adc3f81c8e3c_analytics_py.html
│  ├─ z_cfb6adc3f81c8e3c_auth_py.html
│  ├─ z_cfb6adc3f81c8e3c_deps_py.html
│  ├─ z_cfb6adc3f81c8e3c_feedback_py.html
│  ├─ z_cfb6adc3f81c8e3c_health_py.html
│  ├─ z_cfb6adc3f81c8e3c_history_py.html
│  ├─ z_cfb6adc3f81c8e3c_me_py.html
│  ├─ z_cfb6adc3f81c8e3c_meta_py.html
│  ├─ z_cfb6adc3f81c8e3c_notifications_py.html
│  ├─ z_cfb6adc3f81c8e3c_opportunities_py.html
│  ├─ z_cfb6adc3f81c8e3c_profiles_py.html
│  ├─ z_cfb6adc3f81c8e3c_recommendations_py.html
│  ├─ z_cfb6adc3f81c8e3c_schemas_py.html
│  ├─ z_cfb6adc3f81c8e3c_subscriptions_py.html
│  └─ z_cfb6adc3f81c8e3c_sync_py.html
├─ infra
│  ├─ docker
│  │  ├─ backend.Dockerfile
│  │  ├─ matcher.Dockerfile
│  │  ├─ parser.Dockerfile
│  │  ├─ web.Dockerfile
│  │  └─ web.nginx.conf
│  ├─ postgres
│  │  ├─ bootstrap.sql
│  │  └─ init
│  │     └─ 01-databases.sh
│  └─ requirements
│     ├─ README.md
│     ├─ backend-dev.txt
│     ├─ backend.txt
│     ├─ matcher-dev.txt
│     ├─ matcher.txt
│     ├─ parser-dev.txt
│     └─ parser.txt
├─ loadtest
│  ├─ Makefile.loadtest
│  ├─ data
│  │  └─ tokens.json
│  ├─ docker-compose.loadtest.yml
│  ├─ k6
│  │  ├─ backend.js
│  │  ├─ e2e.js
│  │  ├─ matcher.js
│  │  └─ profiles.js
│  ├─ results
│  │  ├─ backend-baseline.json
│  │  ├─ backend-spike.json
│  │  ├─ backend-stress.json
│  │  ├─ e2e.json
│  │  ├─ matcher-baseline.json
│  │  ├─ matcher-spike.json
│  │  └─ matcher-stress.json
│  └─ scripts
│     ├─ seed_users.sh
│     └─ summarize.sh
├─ matcher
│  ├─ app
│  │  ├─ __init__.py
│  │  ├─ config.py
│  │  ├─ data
│  │  │  ├─ _lists_backgrounds.json
│  │  │  ├─ _lists_industries.json
│  │  │  ├─ _lists_issues.json
│  │  │  ├─ _lists_languages.json
│  │  │  ├─ _lists_skills.json
│  │  │  └─ fake_catalog.json
│  │  ├─ deps.py
│  │  ├─ domain
│  │  │  ├─ __init__.py
│  │  │  ├─ features.py
│  │  │  ├─ filters.py
│  │  │  ├─ models.py
│  │  │  ├─ profile.py
│  │  │  ├─ scoring.py
│  │  │  └─ taxonomy.yaml
│  │  ├─ main.py
│  │  ├─ repo
│  │  │  ├─ __init__.py
│  │  │  └─ catalog_reader.py
│  │  ├─ routers
│  │  │  ├─ __init__.py
│  │  │  ├─ dictionaries.py
│  │  │  ├─ health.py
│  │  │  └─ match.py
│  │  ├─ schemas.py
│  │  └─ weights.yaml
│  ├─ migrations
│  ├─ pytest.ini
│  ├─ tests
│  │  ├─ __init__.py
│  │  ├─ conftest.py
│  │  ├─ factories.py
│  │  ├─ test_ai_cycle.py
│  │  ├─ test_api.py
│  │  ├─ test_boundaries.py
│  │  ├─ test_catalog_cache.py
│  │  ├─ test_catalog_reader.py
│  │  ├─ test_contract.py
│  │  ├─ test_features.py
│  │  ├─ test_filters.py
│  │  ├─ test_negative.py
│  │  ├─ test_privacy.py
│  │  ├─ test_profile.py
│  │  ├─ test_regression_bugs.py
│  │  ├─ test_router.py
│  │  ├─ test_scoring.py
│  │  └─ test_spec_values.py
│  └─ tools
│     └─ control_defects.py
├─ parser
│  ├─ .coveragerc
│  ├─ alembic.ini
│  ├─ app
│  │  ├─ __init__.py
│  │  ├─ api
│  │  │  ├─ __init__.py
│  │  │  ├─ admin.py
│  │  │  ├─ deps.py
│  │  │  ├─ health.py
│  │  │  ├─ opportunities.py
│  │  │  ├─ schemas.py
│  │  │  └─ sync.py
│  │  ├─ auth.py
│  │  ├─ client.py
│  │  ├─ config.py
│  │  ├─ errors.py
│  │  ├─ main.py
│  │  ├─ models.py
│  │  ├─ normalize.py
│  │  ├─ runtime.py
│  │  ├─ sync
│  │  │  ├─ __init__.py
│  │  │  ├─ gapfill.py
│  │  │  ├─ ingest.py
│  │  │  ├─ queries.py
│  │  │  ├─ service.py
│  │  │  ├─ state.py
│  │  │  └─ strategies.py
│  │  └─ tokens.py
│  ├─ migrations
│  │  ├─ env.py
│  │  ├─ script.py.mako
│  │  └─ versions
│  │     ├─ 0001_initial.py
│  │     ├─ 0002_catalog_v1.py
│  │     └─ 0003_catalog_v1_fix.py
│  ├─ pytest.ini
│  ├─ targets.json
│  └─ tests
│     ├─ __init__.py
│     ├─ conftest.py
│     ├─ test_api.py
│     ├─ test_auth.py
│     ├─ test_live.py
│     ├─ test_normalize.py
│     ├─ test_openapi.py
│     └─ test_sync.py
├─ qa
│  ├─ catalog_data.py
│  ├─ conftest.py
│  ├─ load
│  │  ├─ locustfile_backend.py
│  │  ├─ locustfile_matcher.py
│  │  ├─ monitor.py
│  │  ├─ run_load.sh
│  │  ├─ shape.py
│  │  └─ summarize.py
│  ├─ pytest.ini
│  ├─ seed_catalog.py
│  ├─ test_backend_negative.py
│  ├─ test_db_contract.py
│  ├─ test_e2e_user_flow.py
│  ├─ test_matcher_db.py
│  ├─ test_parser_api.py
│  └─ test_smoke.py
├─ scripts
│  ├─ find_env_vars.py
│  └─ smoke.sh
└─ web
   ├─ README.md
   ├─ coverage
   │  ├─ base.css
   │  ├─ block-navigation.js
   │  ├─ favicon.png
   │  ├─ index.html
   │  ├─ lcov-report
   │  │  ├─ base.css
   │  │  ├─ block-navigation.js
   │  │  ├─ favicon.png
   │  │  ├─ index.html
   │  │  ├─ prettify.css
   │  │  ├─ prettify.js
   │  │  ├─ readex-pro-license.txt
   │  │  ├─ readex-pro.woff2
   │  │  ├─ sort-arrow-sprite.png
   │  │  ├─ sorter.js
   │  │  └─ theme.js
   │  ├─ lcov.info
   │  ├─ prettify.css
   │  ├─ prettify.js
   │  ├─ readex-pro-license.txt
   │  ├─ readex-pro.woff2
   │  ├─ sort-arrow-sprite.png
   │  ├─ sorter.js
   │  └─ theme.js
   ├─ dist
   │  ├─ assets
   │  │  ├─ index-BpcgN5Bj.js
   │  │  └─ index-C_Y0ROFh.css
   │  └─ index.html
   ├─ eslint.config.js
   ├─ index.html
   ├─ package-lock.json
   ├─ package.json
   ├─ src
   │  ├─ app
   │  │  ├─ App.tsx
   │  │  ├─ providers.tsx
   │  │  ├─ router.tsx
   │  │  └─ routes.ts
   │  ├─ entities
   │  │  ├─ history
   │  │  │  └─ HistoryEventItem.tsx
   │  │  ├─ opportunity
   │  │  │  ├─ CapacityBadge.tsx
   │  │  │  ├─ CostLabel.tsx
   │  │  │  ├─ OpportunityCard.tsx
   │  │  │  ├─ ProgrammeBadge.tsx
   │  │  │  └─ RequirementChips.tsx
   │  │  ├─ profile
   │  │  │  └─ ProfileSummary.tsx
   │  │  └─ recommendation
   │  │     ├─ MatchLabel.tsx
   │  │     ├─ ReasonList.tsx
   │  │     └─ RecItemCard.tsx
   │  ├─ features
   │  │  ├─ account
   │  │  │  ├─ AccountSecurityForm.tsx
   │  │  │  ├─ DeleteAccountDialog.tsx
   │  │  │  └─ LinkTelegramPanel.tsx
   │  │  ├─ auth
   │  │  │  └─ AuthContext.tsx
   │  │  ├─ consent
   │  │  │  └─ ConsentSettings.tsx
   │  │  ├─ dashboard
   │  │  ├─ feedback
   │  │  │  └─ useSendFeedback.ts
   │  │  ├─ questionnaire
   │  │  │  ├─ FieldRenderer.tsx
   │  │  │  ├─ FormRenderer.tsx
   │  │  │  ├─ ProgrammeCards.tsx
   │  │  │  ├─ useFormState.test.ts
   │  │  │  ├─ useFormState.ts
   │  │  │  └─ validation.ts
   │  │  ├─ recommendations
   │  │  │  └─ useCreateRecommendations.ts
   │  │  └─ subscription
   │  │     └─ SubscriptionForm.tsx
   │  ├─ main.tsx
   │  ├─ pages
   │  │  ├─ errors
   │  │  │  ├─ NotFoundPage.tsx
   │  │  │  └─ OfflinePage.tsx
   │  │  ├─ history
   │  │  │  └─ HistoryPage.tsx
   │  │  ├─ login
   │  │  │  └─ LoginPage.tsx
   │  │  ├─ notifications
   │  │  │  └─ NotificationsPage.tsx
   │  │  ├─ onboarding
   │  │  │  └─ OnboardingPage.tsx
   │  │  ├─ opportunities
   │  │  ├─ opportunity
   │  │  │  └─ OpportunityPage.tsx
   │  │  ├─ profile
   │  │  │  ├─ FavoritesPage.tsx
   │  │  │  ├─ ProfileEditPage.tsx
   │  │  │  ├─ ProfilePage.tsx
   │  │  │  └─ ProfileStatisticsPage.tsx
   │  │  ├─ register
   │  │  │  └─ RegisterPage.tsx
   │  │  ├─ results
   │  │  │  └─ ResultsPage.tsx
   │  │  ├─ settings
   │  │  │  └─ SettingsPage.tsx
   │  │  └─ welcome
   │  │     └─ WelcomePage.tsx
   │  ├─ shared
   │  │  ├─ api
   │  │  │  ├─ client.test.ts
   │  │  │  ├─ client.ts
   │  │  │  ├─ endpoints.ts
   │  │  │  ├─ queries.ts
   │  │  │  └─ types.ts
   │  │  ├─ config
   │  │  │  └─ brand.ts
   │  │  ├─ hooks
   │  │  │  ├─ useMediaQuery.ts
   │  │  │  └─ useOnline.ts
   │  │  ├─ lib
   │  │  │  ├─ age.test.ts
   │  │  │  ├─ age.ts
   │  │  │  ├─ condition.test.ts
   │  │  │  ├─ condition.ts
   │  │  │  ├─ date.ts
   │  │  │  ├─ errors.test.ts
   │  │  │  ├─ errors.ts
   │  │  │  ├─ format.test.ts
   │  │  │  ├─ format.ts
   │  │  │  ├─ get.test.ts
   │  │  │  ├─ get.ts
   │  │  │  ├─ password.test.ts
   │  │  │  └─ password.ts
   │  │  ├─ styles
   │  │  │  ├─ global.css
   │  │  │  ├─ layout.css
   │  │  │  └─ tokens.css
   │  │  └─ ui
   │  │     ├─ AuthCard.tsx
   │  │     ├─ Avatar.tsx
   │  │     ├─ Badge.tsx
   │  │     ├─ BarChart.tsx
   │  │     ├─ Button.tsx
   │  │     ├─ Card.tsx
   │  │     ├─ ChartLegend.tsx
   │  │     ├─ ChartTooltip.tsx
   │  │     ├─ Chip.tsx
   │  │     ├─ ChipGroup.tsx
   │  │     ├─ DateField.tsx
   │  │     ├─ DateRangeFilter.tsx
   │  │     ├─ Dialog.tsx
   │  │     ├─ DonutChart.tsx
   │  │     ├─ EmptyState.tsx
   │  │     ├─ ErrorBanner.tsx
   │  │     ├─ IconButton.tsx
   │  │     ├─ LineChart.tsx
   │  │     ├─ NavigationBar.tsx
   │  │     ├─ NumberStepper.tsx
   │  │     ├─ PasswordField.tsx
   │  │     ├─ Progress.tsx
   │  │     ├─ Segmented.tsx
   │  │     ├─ Select.tsx
   │  │     ├─ Skeleton.tsx
   │  │     ├─ Tabs.tsx
   │  │     ├─ TextArea.tsx
   │  │     ├─ TextField.tsx
   │  │     ├─ Timeline.tsx
   │  │     ├─ Toast.tsx
   │  │     ├─ Toggle.tsx
   │  │     └─ index.ts
   │  ├─ test
   │  │  ├─ msw
   │  │  │  ├─ handlers.ts
   │  │  │  └─ server.ts
   │  │  ├─ setup.ts
   │  │  └─ utils.tsx
   │  └─ widgets
   │     ├─ MainNavigation.tsx
   │     ├─ OnboardingWizard.tsx
   │     ├─ ProfileCompleteness.tsx
   │     ├─ ProfileSummaryBar.tsx
   │     ├─ ProfileVersionHistory.tsx
   │     ├─ ResultsTabs.tsx
   │     └─ UserStatisticsDashboard.tsx
   ├─ tsconfig.app.json
   ├─ tsconfig.json
   ├─ tsconfig.node.json
   ├─ vite.config.ts
   └─ vitest.config.ts

```
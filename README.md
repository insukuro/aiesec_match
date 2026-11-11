# aiesec-platform (монорепо)


## Быстрый старт

```bash
cp .env.example .env     # заполнить AIESEC_TOKEN, PARSER_API_KEY, POSTGRES_PASSWORD
make up                  # postgres + парсер; первый full-sync стартует сам
```


```
aiesec_match
├─ .dockerignore
├─ Makefile
├─ README.md
├─ backend
│  ├─ alembic.ini
│  ├─ app
│  │  ├─ __init__.py
│  │  ├─ api
│  │  │  ├─ __init__.py
│  │  │  ├─ auth.py
│  │  │  ├─ feedback.py
│  │  │  ├─ health.py
│  │  │  ├─ me.py
│  │  │  ├─ meta.py
│  │  │  ├─ notifications.py
│  │  │  ├─ opportunities.py
│  │  │  ├─ profiles.py
│  │  │  ├─ recommendations.py
│  │  │  └─ subscriptions.py
│  │  ├─ auth.py
│  │  ├─ catalog.py
│  │  ├─ completeness.py
│  │  ├─ config.py
│  │  ├─ db.py
│  │  ├─ errors.py
│  │  ├─ forms
│  │  │  └─ form_schema.v1.yaml
│  │  ├─ formschema.py
│  │  ├─ main.py
│  │  ├─ matcher_client.py
│  │  ├─ models.py
│  │  ├─ schemas.py
│  │  └─ workers
│  │     └─ outbox.py
│  ├─ migrations
│  │  ├─ README
│  │  ├─ env.py
│  │  ├─ script.py.mako
│  │  └─ versions
│  │     └─ 0001_core.py
│  ├─ pytest.ini
│  ├─ requirements-dev.txt
│  ├─ requirements.txt
│  └─ tests
│     ├─ conftest.py
│     └─ test_concurrency.py
├─ docker-compose.dev.yml
├─ docker-compose.yml
├─ docs
│  ├─ README.md
│  └─ testing.md
├─ htmlcov
├─ infra
│  ├─ docker
│  │  ├─ backend.Dockerfile
│  │  ├─ backend.dev.Dockerfile
│  │  ├─ parser.Dockerfile
│  │  ├─ parser.dev.Dockerfile
│  │  ├─ web.Dockerfile
│  │  └─ web.nginx.conf
│  └─ postgres
│     ├─ bootstrap.sql
│     └─ init
│        └─ 01-databases.sh
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
│  │     └─ 0001_initial.py
│  ├─ pytest.ini
│  ├─ requirements-dev.txt
│  ├─ requirements.txt
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
├─ scripts
│  └─ smoke.sh
└─ web
   ├─ README.md
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
   │  │  │  ├─ DeleteAccountDialog.tsx
   │  │  │  └─ LinkTelegramPanel.tsx
   │  │  ├─ dashboard
   │  │  │  └─ useDashboardPreferences.ts
   │  │  ├─ feedback
   │  │  │  └─ useSendFeedback.ts
   │  │  ├─ questionnaire
   │  │  │  ├─ FieldRenderer.tsx
   │  │  │  ├─ FormRenderer.tsx
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
   │  │  ├─ onboarding
   │  │  │  └─ OnboardingPage.tsx
   │  │  ├─ opportunity
   │  │  │  └─ OpportunityPage.tsx
   │  │  ├─ profile
   │  │  │  ├─ ProfileEditPage.tsx
   │  │  │  ├─ ProfilePage.tsx
   │  │  │  ├─ ProfileStatisticsPage.tsx
   │  │  │  └─ StatisticsSettingsPage.tsx
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
   │  │  │  ├─ condition.ts
   │  │  │  ├─ date.ts
   │  │  │  ├─ errors.ts
   │  │  │  ├─ format.ts
   │  │  │  └─ get.ts
   │  │  ├─ styles
   │  │  │  ├─ global.css
   │  │  │  └─ tokens.css
   │  │  └─ ui
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
   │  └─ widgets
   │     ├─ DashboardCustomizer.tsx
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
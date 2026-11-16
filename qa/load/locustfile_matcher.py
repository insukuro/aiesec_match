"""Нагрузка на матчер напрямую: POST /v1/match (самая тяжёлая операция сервиса).

Запуск (из папки qa/load):
  USERS=50 locust -f locustfile_matcher.py --headless --host http://127.0.0.1:8002 \
      --csv out/matcher_u50 --html out/matcher_u50.html
"""
import random

from locust import HttpUser, between, task

from shape import RampHoldDown  # noqa: F401  (Locust сам находит профиль нагрузки)

SPHERES = ["marketing", "sales", "it", "finance", "teaching_kids", "design"]
ACTIVITIES = ["events", "ecology", "community"]
LEVELS = ["A2", "B1", "B2", "C1"]


def random_profile(rnd: random.Random) -> dict:
    """Синтетическая анкета. Настоящих анкет в тестах нет (152-ФЗ)."""
    kind = rnd.choices(["talent", "volunteer", "teacher"], weights=[5, 3, 2])[0]
    lo = rnd.choice([6, 8, 12])
    return {
        "programmes": [kind],
        "english_level": rnd.choice(LEVELS),
        "study": {"status": rnd.choice(["bachelor", "school", "master"])},
        "spheres": rnd.sample(SPHERES, rnd.randint(1, 3)),
        "activities": rnd.sample(ACTIVITIES, rnd.randint(0, 2)),
        "other_languages": rnd.sample(["ru", "es", "pt"], rnd.randint(0, 2)),
        "duration": {"min_weeks": lo, "max_weeks": lo + rnd.choice([0, 4, 12])},
        "financial": {"willing_to_pay": rnd.random() < 0.7, "max_budget_eur": rnd.choice([200, 400, 800])},
    }


class MatcherClient(HttpUser):
    """Ведёт себя как бэкенд: шлёт анкету, ждёт подбор."""
    wait_time = between(0.5, 1.5)

    def on_start(self):
        self.rnd = random.Random()

    @task(10)
    def match(self):
        body = {"profile_id": f"load-{self.rnd.randrange(10**9)}", "profile": random_profile(self.rnd),
                "filters": {}, "limit_per_programme": 10, "explain": True}
        with self.client.post("/v1/match", json=body, name="POST /v1/match", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
            elif not r.json().get("groups"):
                r.failure("нет групп в ответе")

    @task(1)
    def health(self):
        self.client.get("/health", name="GET /health")

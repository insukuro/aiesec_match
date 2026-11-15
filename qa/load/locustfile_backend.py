"""Нагрузка на весь сервис через бэкенд: поведение обычного пользователя сайта.

Запуск (из папки qa/load):
  USERS=50 locust -f locustfile_backend.py --headless --host http://127.0.0.1:8000 \
      --csv out/backend_u50 --html out/backend_u50.html

Каждый виртуальный пользователь сначала регистрируется, даёт согласие и заполняет анкету,
а потом ходит по сайту. Веса задач взяты из модели нагрузки (таблица в отчёте).
"""
import random
import uuid

from locust import HttpUser, between, task

from locustfile_matcher import random_profile
from shape import RampHoldDown  # noqa: F401

API = "/api/v1"


class SiteUser(HttpUser):
    wait_time = between(1, 3)                      # человек думает 1-3 секунды между действиями

    def on_start(self):
        self.rnd = random.Random()
        self.seen: list[int] = []
        email = f"load_{uuid.uuid4().hex[:14]}@example.com"
        r = self.client.post(f"{API}/auth/register", json={"email": email, "password": "Passw0rd123"},
                             name="POST /auth/register")
        self.h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        self.client.post(f"{API}/me/consents", json={"kind": "pd_processing", "version": "1"},
                         headers=self.h, name="POST /me/consents")
        profile = {**random_profile(self.rnd), "birth_date": "2003-05-10", "work_experience": "none"}
        self.client.put(f"{API}/profiles/me", json=profile, headers=self.h, name="PUT /profiles/me")

    def on_stop(self):
        self.client.delete(f"{API}/me", headers=self.h, name="DELETE /me")     # убираем за собой

    @task(5)
    def browse_catalog(self):
        params = {"limit": 20, "offset": self.rnd.choice([0, 20, 40]),
                  "programme_kind": self.rnd.choice(["talent", "volunteer", "teacher"])}
        r = self.client.get(f"{API}/opportunities", params=params, name="GET /opportunities")
        if r.status_code == 200:
            self.seen = [i["opportunity_id"] for i in r.json()["items"]] or self.seen

    @task(3)
    def open_card(self):
        if self.seen:
            self.client.get(f"{API}/opportunities/{self.rnd.choice(self.seen)}", name="GET /opportunities/{id}")

    @task(2)
    def get_recommendations(self):
        headers = {**self.h, "Idempotency-Key": str(uuid.uuid4())}
        with self.client.post(f"{API}/recommendations", json={"limit_per_programme": 10}, headers=headers,
                              name="POST /recommendations", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
            else:
                ids = [it["opportunity"]["opportunity_id"] for g in r.json()["groups"] for it in g["items"]]
                self.seen = ids or self.seen

    @task(2)
    def latest_recommendations(self):
        with self.client.get(f"{API}/recommendations/latest", headers=self.h,
                             name="GET /recommendations/latest", catch_response=True) as r:
            if r.status_code in (200, 404):        # 404 = подбор ещё не запускали, это не ошибка
                r.success()

    @task(1)
    def like(self):
        if self.seen:
            self.client.post(f"{API}/feedback", headers=self.h, name="POST /feedback",
                             json={"opportunity_id": self.rnd.choice(self.seen), "signal": "liked"})

    @task(1)
    def my_profile(self):
        self.client.get(f"{API}/profiles/me", headers=self.h, name="GET /profiles/me")

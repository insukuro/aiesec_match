from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.repositories.catalog_repo import CatalogRepo

STATIC_OPTIONS = {
    "study_status": [
        {"code": "school", "label": "Школьник(ца)"},
        {"code": "bachelor", "label": "Бакалавриат"},
        {"code": "master", "label": "Магистратура"},
        {"code": "postgraduate", "label": "Аспирантура"},
        {"code": "graduate", "label": "Уже выпустился(ась)"},
        {"code": "not_studying", "label": "Не учусь"},
    ],
    "english_level": [
        {"code": "A1", "label": "A1 — базовый"},
        {"code": "A2", "label": "A2 — базовый"},
        {"code": "B1", "label": "B1 — могу общаться"},
        {"code": "B2", "label": "B2 — могу общаться"},
        {"code": "C1", "label": "C1 — свободно"},
        {"code": "C2", "label": "C2 — свободно"},
    ],
    "work_experience": [
        {"code": "none", "label": "Нет опыта"},
        {"code": "1_2_years", "label": "1–2 года"},
        {"code": "3_5_years", "label": "3–5 лет"},
        {"code": "5_plus_years", "label": "5+ лет"},
    ],
    "start_window": [
        {"code": "asap", "label": "Как можно скорее"},
        {"code": "within_3_months", "label": "В течение 3 месяцев"},
        {"code": "within_6_months", "label": "В течение 6 месяцев"},
        {"code": "later", "label": "Позже"},
        {"code": "unsure", "label": "Пока не знаю"},
    ],
    "spheres": [
        {"code": "it", "label": "IT и разработка"},
        {"code": "marketing", "label": "Маркетинг"},
        {"code": "sales", "label": "Продажи"},
        {"code": "finance", "label": "Финансы"},
        {"code": "hr", "label": "HR"},
        {"code": "design", "label": "Дизайн"},
        {"code": "engineering", "label": "Инженерия"},
        {"code": "education", "label": "Образование"},
        {"code": "healthcare", "label": "Медицина"},
        {"code": "ngo", "label": "НКО и социальные проекты"},
        {"code": "entrepreneurship", "label": "Предпринимательство"}, 
    ],
    "activities": [
        {"code": "teaching", "label": "Преподавание"},
        {"code": "teaching_kids", "label": "Преподавание детям"}, 
        {"code": "teaching_english", "label": "Преподавание английского"}, 
        {"code": "events", "label": "Организация мероприятий"},
        {"code": "ecology", "label": "Экология"},
        {"code": "community", "label": "Работа с сообществом"},
        {"code": "culture", "label": "Культура и искусство"},
        {"code": "sports", "label": "Спорт"},
    ],
    "durations": [
        {"code": "6", "label": "6 недель"},
        {"code": "8", "label": "8 недель"},
        {"code": "12", "label": "12 недель"},
        {"code": "24", "label": "24 недели"},
        {"code": "52", "label": "52 недели (год)"},
    ],
    "countries": [
        {"code": "TR", "label": "Турция"},
        {"code": "PL", "label": "Польша"},
        {"code": "DE", "label": "Германия"},
        {"code": "CZ", "label": "Чехия"},
        {"code": "HU", "label": "Венгрия"},
        {"code": "RO", "label": "Румыния"},
    ],
    "other_languages": [
        {"code": "en", "label": "Английский"},
        {"code": "ru", "label": "Русский"},
        {"code": "tr", "label": "Турецкий"},
        {"code": "de", "label": "Немецкий"},
        {"code": "fr", "label": "Французский"},
        {"code": "es", "label": "Испанский"},
    ],
}

_PROGRAMME_LABELS = {
    "talent": "Global Talent",
    "teacher": "Global Teacher",
    "volunteer": "Global Volunteer",
}


class MetaService:
    def __init__(self, session: AsyncSession):
        self._catalog = CatalogRepo(session)

    async def form_options(self) -> dict:
        stats = await self._catalog.programme_stats()
        out = dict(STATIC_OPTIONS)
        out["programmes"] = [
            {
                "code": r["code"],
                "label": _PROGRAMME_LABELS.get(r["code"], r["code"]),
                "count": r["count"],
            }
            for r in stats
        ]
        return out
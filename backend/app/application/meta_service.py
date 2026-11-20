from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.repositories.catalog_repo import CatalogRepo


STATIC_OPTIONS = {
    # --- программы (на них ссылается анкета: talent/teacher/volunteer) ---
    "programmes": [
        {"code": "talent",    "label": "Global Talent (стажировка)"},
        {"code": "teacher",   "label": "Global Teacher (преподавание)"},
        {"code": "volunteer", "label": "Global Volunteer (волонтёрство)"},
    ],

    "study_status": [
        {"code": "school",       "label": "Школьник(ца)"},
        {"code": "bachelor",     "label": "Бакалавриат"},
        {"code": "master",       "label": "Магистратура"},
        {"code": "postgraduate", "label": "Аспирантура"},
        {"code": "graduate",     "label": "Уже выпустился(ась)"},
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
        {"code": "none",         "label": "Нет опыта"},
        {"code": "1_2_years",    "label": "1–2 года"},
        {"code": "3_5_years",    "label": "3–5 лет"},
        {"code": "5_plus_years", "label": "5+ лет"},
    ],

    "start_window": [
        {"code": "asap",            "label": "Как можно скорее"},
        {"code": "within_3_months", "label": "В течение 3 месяцев"},
        {"code": "within_6_months", "label": "В течение 6 месяцев"},
        {"code": "later",           "label": "Позже"},
        {"code": "unsure",          "label": "Пока не знаю"},
    ],

    "spheres": [
        {"code": "it",               "label": "IT и разработка"},
        {"code": "marketing",        "label": "Маркетинг"},
        {"code": "sales",            "label": "Продажи"},
        {"code": "finance",          "label": "Финансы"},
        {"code": "hr",               "label": "HR"},
        {"code": "design",           "label": "Дизайн"},
        {"code": "engineering",      "label": "Инженерия"},
        {"code": "education",        "label": "Образование"},
        {"code": "healthcare",       "label": "Медицина"},
        {"code": "ngo",              "label": "НКО и социальные проекты"},
        {"code": "entrepreneurship", "label": "Предпринимательство"},
    ],

    "activities": [
        {"code": "teaching",         "label": "Преподавание"},
        {"code": "teaching_kids",    "label": "Преподавание детям"},
        {"code": "teaching_english", "label": "Преподавание английского"},
        {"code": "events",           "label": "Организация мероприятий"},
        {"code": "ecology",          "label": "Экология"},
        {"code": "community",        "label": "Работа с сообществом"},
        {"code": "culture",          "label": "Культура и искусство"},
        {"code": "sports",           "label": "Спорт"},
    ],

    "durations": [
        {"code": "6",  "label": "6 недель"},
        {"code": "8",  "label": "8 недель"},
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

    # --- гражданство (ISO-3166-1 alpha-2, UPPERCASE) ---
    # Полный список — в spheres.txt (nationalities -> constant_id).
    # Здесь — подмножество для UI, синхронизировано с дампом.
    "nationality": [
        {"code": "RU", "label": "Россия",        "constant_id": 10463},
        {"code": "BY", "label": "Беларусь",      "constant_id": 10358},
        {"code": "KZ", "label": "Казахстан",     "constant_id": 10486},
        {"code": "UA", "label": "Украина",       "constant_id": 10549},
        {"code": "UZ", "label": "Узбекистан",    "constant_id": 10558},
        {"code": "KG", "label": "Кыргызстан",    "constant_id": 10488},
        {"code": "AM", "label": "Армения",       "constant_id": 10349},
        {"code": "GE", "label": "Грузия",        "constant_id": 10412},
        {"code": "AZ", "label": "Азербайджан",   "constant_id": 10353},
        {"code": "MD", "label": "Молдова",       "constant_id": 10443},
        {"code": "TR", "label": "Турция",        "constant_id": 10547},
        {"code": "PL", "label": "Польша",        "constant_id": 10513},
        {"code": "DE", "label": "Германия",      "constant_id": 10432},
        {"code": "CZ", "label": "Чехия",         "constant_id": 10392},
        {"code": "HU", "label": "Венгрия",       "constant_id": 10424},
        {"code": "RO", "label": "Румыния",       "constant_id": 10516},
        {"code": "XX", "label": "Другое",        "constant_id": 10271},
    ],

    "gender": [
        {"code": "male",   "label": "Мужской"},
        {"code": "female", "label": "Женский"},
        {"code": "other",  "label": "Другой / не указывать"},
    ],

    # --- языки: code = ISO-639-1/2, constant_id — из дампа ---
    "other_languages": [
        {"code": "en", "label": "Английский",  "constant_id": 10018},
        {"code": "ru", "label": "Русский",     "constant_id": 10043},
        {"code": "tr", "label": "Турецкий",    "constant_id": 10051},
        {"code": "de", "label": "Немецкий",    "constant_id": 10024},
        {"code": "fr", "label": "Французский", "constant_id": 10022},
        {"code": "es", "label": "Испанский",   "constant_id": 10048},
        {"code": "it", "label": "Итальянский", "constant_id": 10031},
        {"code": "zh", "label": "Китайский",   "constant_id": 10012},
        {"code": "ja", "label": "Японский",    "constant_id": 10032},
        {"code": "ko", "label": "Корейский",   "constant_id": 10034},
        {"code": "ar", "label": "Арабский",    "constant_id": 10006},
        {"code": "pt", "label": "Португальский","constant_id": 10041},
        {"code": "ro", "label": "Румынский",   "constant_id": 10042},
        {"code": "hu", "label": "Венгерский",  "constant_id": 10028},
        {"code": "uk", "label": "Украинский",  "constant_id": 10052},
        {"code": "bg", "label": "Болгарский",  "constant_id": 10011},
        {"code": "el", "label": "Греческий",   "constant_id": 10025},
        {"code": "hi", "label": "Хинди",       "constant_id": 10027},
        {"code": "id", "label": "Индонезийский","constant_id": 10009},
        {"code": "vi", "label": "Вьетнамский", "constant_id": 10054},
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
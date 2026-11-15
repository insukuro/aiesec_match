"""Контрольные дефекты: доказательство, что тесты ловят ошибки (Коцур, лекция 2).

Идея простая. Берём рабочий код, намеренно вносим в копию одну ошибку
(например, меняем >= на >) и запускаем тесты. Хороший набор тестов должен покраснеть.
Если тесты остались зелёными, значит эту ошибку никто бы не заметил.

Скрипт делает это для списка ошибок и печатает таблицу для двух наборов:
  старый набор  - 4 исходных файла (28 тестов),
  новый набор   - все тесты.
Исходный код не меняется: каждая ошибка вносится во временную копию.

Запуск из папки matcher:   python tools/control_defects.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD_TESTS = ["tests/test_api.py", "tests/test_features.py", "tests/test_filters.py", "tests/test_scoring.py"]

# (номер, файл, что было, что стало, какую ошибку имитируем)
DEFECTS = [
    ("D01", "app/domain/filters.py", "o.available_openings <= 0", "o.available_openings < 0", "вакансия без свободных мест попадает в подбор"),
    ("D02", "app/domain/filters.py", "o.applications_close_date < today", "o.applications_close_date <= today", "вакансия с дедлайном сегодня отбрасывается"),
    ("D03", "app/domain/filters.py", 'if opt == "required"}', 'if opt == "preferred"}', "фильтр смотрит на желательные языки вместо обязательных"),
    ("D04", "app/domain/filters.py", "and o.cost_total > p.max_budget_eur", "and o.cost_total >= p.max_budget_eur", "вакансия ровно по бюджету отбрасывается"),
    ("D05", "app/domain/filters.py", "if o.opportunity_id in filters.exclude_opportunity_ids:", "if False:", "скрытые пользователем вакансии возвращаются"),
    ("D06", "app/domain/filters.py", "if p.willing_to_pay is False:", "if p.willing_to_pay is None:", "не готов платить, но платные вакансии показываются"),
    ("D07", "app/domain/profile.py", ">= CEFR.index(min_english)", "> CEFR.index(min_english)", "уровень английского ровно на пороге не засчитывается"),
    ("D08", "app/domain/features.py", '"preferred": 0.5', '"preferred": 1.0', "желательное требование весит как обязательное"),
    ("D09", "app/domain/features.py", "1 - dist / 8", "1 - dist / 4", "штраф за длительность падает вдвое быстрее"),
    ("D10", "app/domain/features.py", "math.exp(-days / 90)", "math.exp(-days / 30)", "свежесть затухает за 30 дней вместо 90"),
    ("D11", "app/domain/features.py", "return 1.0 if o.cost_total <= p.max_budget_eur else 0.0", "return 1.0 if o.cost_total < p.max_budget_eur else 0.0", "стоимость ровно по бюджету считается превышением"),
    ("D12", "app/domain/features.py", "a: float = 10.0", "a: float = 0.1", "сглаживание шанса почти отключено"),
    ("D13", "app/domain/features.py", 'if opt == "preferred"}', 'if opt == "required"}', "оценка языка считает обязательные языки вместо желательных"),
    ("D14", "app/domain/scoring.py", "if score >= excellent", "if score > excellent", "оценка ровно 0.75 получает метку good"),
    ("D15", "app/domain/scoring.py", "(-t[0], t[1].opportunity_id)", "(-t[0], -t[1].opportunity_id)", "при равных оценках порядок обратный"),
    ("D16", "app/domain/scoring.py", "and v >= 0.7)", "and v >= 0.9)", "порог для объяснений поднят"),
    ("D17", "app/domain/scoring.py", "for c, k in pos[:3]]", "for c, k in pos[:5]]", "объяснений больше трёх"),
    ("D18", "app/domain/scoring.py", "if key in siblings:", "if False and key in siblings:", "семьи вакансий не схлопываются"),
    ("D19", "app/domain/scoring.py", "enumerate(best[:limit], start=1)", "enumerate(best, start=1)", "лимит выдачи не применяется"),
    ("D20", "app/domain/scoring.py", "make_reasons(f, w) if explain else []", "make_reasons(f, w)", "объяснения отдаются даже при explain=false"),
    ("D21", "app/weights.yaml", "talent:    {background: 0.35, skill: 0.15", "talent:    {background: 0.15, skill: 0.35", "веса образования и навыков перепутаны (сумма та же)"),
    ("D22", "app/weights.yaml", "chance: 0.20, freshness: 0.10}", "chance: 0.25, freshness: 0.10}", "сумма весов teacher больше 1"),
    ("D23", "app/routers/match.py", 's.min_english.get(kind, "B1")', '"A1"', "минимальный английский не зависит от программы"),
    ("D24", "app/routers/match.py", "req.filters.programme_kinds or req.profile.programmes", "req.profile.programmes or req.filters.programme_kinds", "фильтр программ не перекрывает анкету"),
    ("D25", "app/routers/match.py", 'raise HTTPException(503, detail={"type": "catalog-unavailable"}) from e', "raise", "сбой каталога отдаётся как 500"),
    ("D26", "app/repo/catalog_reader.py", 'r.get("option") or "required"', 'r.get("option") or "preferred"', "требование без пометки считается желательным"),
    ("D27", "app/domain/profile.py", 'bg.update(m.get("backgrounds", []))', 'bg.update(m.get("skills", []))', "сфера анкеты превращается не в то требование"),
    ("D28", "app/schemas.py", "limit_per_programme: int = Field(10, ge=1, le=50)", "limit_per_programme: int = Field(10, ge=0, le=500)", "границы лимита ослаблены"),
    ("D29", "app/repo/catalog_reader.py", "self._clock() - hit[0] < self._ttl", "self._clock() - hit[0] <= self._ttl", "кэш каталога живёт на мгновение дольше срока"),
    ("D30", "app/repo/catalog_reader.py", "self._data[programme_kind] = (self._clock(), rows)", 'self._data["talent"] = (self._clock(), rows)', "кэш каталога путает программы"),
    ("D31", "app/routers/match.py", "request_id=req.request_id", "request_id=None", "номер запроса не возвращается в ответе"),
    ("D32", "app/domain/features.py", "days = max(0, (today - o.date_opened).days)", "days = (today - o.date_opened).days", "возврат бага BUG-M-03: свежесть больше 1 для даты в будущем"),
]


def run_tests(workdir: Path, targets: list[str]) -> bool:
    """True, если тесты покраснели (ошибка поймана)."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "-W", "ignore", *targets],
        cwd=workdir, capture_output=True, text=True,
    )
    return proc.returncode != 0


def main() -> int:
    rows, old_caught, new_caught = [], 0, 0
    for num, rel, old, new, what in DEFECTS:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "matcher"
            shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", "htmlcov"))
            target = work / rel
            src = target.read_text(encoding="utf-8")
            if old not in src:
                rows.append((num, what, "нет такого места в коде", "", rel))
                continue
            target.write_text(src.replace(old, new, 1), encoding="utf-8")
            by_old = run_tests(work, OLD_TESTS)
            by_new = run_tests(work, ["tests"])
        old_caught += by_old
        new_caught += by_new
        rows.append((num, what, "пойман" if by_old else "НЕ пойман", "пойман" if by_new else "НЕ пойман", rel))

    print("| № | Внесённая ошибка | Файл | Старый набор (28) | Новый набор |")
    print("|---|---|---|---|---|")
    for num, what, o, n, rel in rows:
        print(f"| {num} | {what} | {rel} | {o} | {n} |")
    total = len(DEFECTS)
    print(f"\nИтого поймано: старый набор {old_caught} из {total} ({old_caught / total:.0%}), "
          f"новый набор {new_caught} из {total} ({new_caught / total:.0%}).")
    return 0 if new_caught == total else 1


if __name__ == "__main__":
    raise SystemExit(main())

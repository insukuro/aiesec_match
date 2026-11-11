CHECK_FIELDS = [
    "programmes", "english_level", "study.status", "work_experience",
    "spheres_or_activities", "desired_countries", "duration", "start_window", "motivation_text",
]


def _get(d: dict, path: str):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def completeness(body: dict) -> float:
    hits = 0
    if body.get("programmes"): hits += 1
    if _get(body, "english_level"): hits += 1
    if _get(body, "study.status"): hits += 1
    if _get(body, "work_experience"): hits += 1
    if body.get("spheres") or body.get("activities"): hits += 1
    if body.get("desired_countries"): hits += 1
    if _get(body, "duration.min_weeks") or _get(body, "duration.max_weeks"): hits += 1
    if _get(body, "start_window"): hits += 1
    if body.get("motivation_text"): hits += 1
    return round(hits / len(CHECK_FIELDS), 3)


def missing_for_match(body: dict) -> list[str]:
    """Возвращает список недостающих полей по ТЗ-B §3 (минимум для подбора)."""
    miss: list[str] = []
    if not _get(body, "english_level"): miss.append("english_level")
    if not _get(body, "study.status"): miss.append("study.status")
    if not body.get("birth_date"):       miss.append("birth_date")
    if not (body.get("programmes") or body.get("spheres") or body.get("activities")):
        miss.append("programmes")
    return miss
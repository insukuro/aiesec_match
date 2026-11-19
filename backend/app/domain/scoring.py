def label(score: float) -> str:
    if score >= 0.8:
        return "excellent"
    if score >= 0.6:
        return "good"
    return "fair"


def programme_prior(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, dict):
        return list(value.keys())
    return list(value)
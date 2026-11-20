
def programme_prior(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, dict):
        return list(value.keys())
    return list(value)
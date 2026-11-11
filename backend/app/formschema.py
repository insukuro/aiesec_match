from pathlib import Path
import yaml
from .config import get_settings


def load_form_schema() -> dict:
    path: Path = get_settings().form_schema_path
    return yaml.safe_load(path.read_text(encoding="utf-8"))
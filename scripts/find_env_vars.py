#!/usr/bin/env python3
"""
Сканирует кодовую базу и находит все обращения к переменным окружения.
Поддерживает: os.environ, os.getenv, os.environ.get, os.environ[...],
dotenv, pydantic Settings (env-поля), docker-compose, .env.example и т.д.

Выдаёт:
  - .env.example (готовый шаблон)
  - отчёт в консоль / JSON
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EnvOccurrence:
    name: str
    file: Path
    line: int
    pattern: str      # какой шаблон сработал
    default: str | None = None
    context: str = ""  # строка кода (обрезанная)


# Паттерны поиска. Порядок важен — более специфичные выше.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # os.getenv("VAR", "default") / os.getenv('VAR')
    ("os.getenv", re.compile(
        r"""os\.getenv\(\s*['"](?P<name>[A-Za-z_][A-Za-z0-9_]*)['"]"""
        r"""(?:\s*,\s*(?P<default>[^)]+))?\s*\)""")),
    # os.environ.get("VAR", "default")
    ("os.environ.get", re.compile(
        r"""os\.environ\.get\(\s*['"](?P<name>[A-Za-z_][A-Za-z0-9_]*)['"]"""
        r"""(?:\s*,\s*(?P<default>[^)]+))?\s*\)""")),
    # os.environ["VAR"]
    ("os.environ[]", re.compile(
        r"""os\.environ\[\s*['"](?P<name>[A-Za-z_][A-Za-z0-9_]*)['"]\s*\]""")),
    # os.environ.setdefault("VAR", ...)
    ("os.environ.setdefault", re.compile(
        r"""os\.environ\.setdefault\(\s*['"](?P<name>[A-Za-z_][A-Za-z0-9_]*)['"]"""
        r"""(?:\s*,\s*(?P<default>[^)]+))?\s*\)""")),
    # environs / decouple: config("VAR", default=...)
    ("config()", re.compile(
        r"""(?:config|Config)\(\s*['"](?P<name>[A-Z_][A-Za-z0-9_]*)['"]""")),
    # pydantic-settings: VAR: str = ... / Field(..., env="VAR")
    ("Field(env=)", re.compile(
        r"""Field\([^)]*?env\s*=\s*['"](?P<name>[A-Za-z_][A-Za-z0-9_]*)['"]""")),
    # django: os.getenv уже покрыт; settings через env( )
    # generic: get_env("VAR") / getenv("VAR") без os.
    ("getenv", re.compile(
        r"""(?<!os\.)\bgetenv\(\s*['"](?P<name>[A-Za-z_][A-Za-z0-9_]*)['"]""")),
]

# Для не-Python файлов (docker-compose, Dockerfile, .env, yaml, sh)
NON_PY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("${VAR}", re.compile(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)")),
    ("$VAR", re.compile(r"\$(?P<name>[A-Za-z_][A-Za-z0-9_]*)")),
    ("env VAR", re.compile(r"^\s*ENV\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)", re.M)),
    ("env_file line", re.compile(r"^\s*(?P<name>[A-Z_][A-Z0-9_]*)\s*=", re.M)),
]

PY_EXTS = {".py", ".pyi"}
OTHER_EXTS = {".yaml", ".yml", ".env", ".sh", ".dockerfile", ".toml", ".ini"}
OTHER_NAMES = {"Dockerfile", ".env", ".env.example", ".env.local", "docker-compose.yml"}


@dataclass
class Config:
    root: Path
    exclude_dirs: set[str] = field(default_factory=lambda: {
        ".git", ".venv", "venv", "env", "__pycache__", "node_modules",
        ".mypy_cache", ".ruff_cache", ".pytest_cache", "build", "dist",
        ".tox", "site-packages", ".idea", ".vscode",
    })
    include_non_py: bool = True
    include_tests: bool = True


def iter_files(cfg: Config):
    for path in cfg.root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in cfg.exclude_dirs for part in path.parts):
            continue
        name = path.name
        ext = path.suffix.lower()
        if ext in PY_EXTS:
            yield path, True
        elif cfg.include_non_py and (ext in OTHER_EXTS or name in OTHER_NAMES):
            # пропускаем тестовые файлы, если не нужны
            if not cfg.include_tests and (name.startswith("test_") or name.endswith("_test.py")):
                continue
            yield path, False


def scan_python(path: Path) -> list[EnvOccurrence]:
    out: list[EnvOccurrence] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for lineno, line in enumerate(text.splitlines(), 1):
        if "#" in line:
            code_part = line.split("#", 1)[0]
        else:
            code_part = line
        for pat_name, pat in PATTERNS:
            for m in pat.finditer(code_part):
                default = m.groupdict().get("default")
                out.append(EnvOccurrence(
                    name=m.group("name"),
                    file=path,
                    line=lineno,
                    pattern=pat_name,
                    default=default.strip().strip("'\"") if default else None,
                    context=code_part.strip()[:120],
                ))
    return out


def scan_other(path: Path) -> list[EnvOccurrence]:
    out: list[EnvOccurrence] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        for pat_name, pat in NON_PY_PATTERNS:
            for m in pat.finditer(line):
                out.append(EnvOccurrence(
                    name=m.group("name"),
                    file=path,
                    line=lineno,
                    pattern=pat_name,
                    context=stripped[:120],
                ))
    return out


def scan(cfg: Config) -> list[EnvOccurrence]:
    results: list[EnvOccurrence] = []
    for path, is_py in iter_files(cfg):
        if is_py:
            results.extend(scan_python(path))
        else:
            results.extend(scan_other(path))
    return results


def aggregate(occurrences: list[EnvOccurrence]) -> dict[str, dict]:
    """Собирает уникальные имена с метаданными."""
    agg: dict[str, dict] = {}
    for occ in occurrences:
        entry = agg.setdefault(occ.name, {
            "name": occ.name,
            "defaults": set(),
            "files": set(),
            "count": 0,
            "patterns": set(),
            "first_seen": occ,
        })
        entry["count"] += 1
        entry["files"].add(str(occ.file))
        entry["patterns"].add(occ.pattern)
        if occ.default is not None:
            entry["defaults"].add(occ.default)
    # нормализуем множества в списки
    for e in agg.values():
        e["defaults"] = sorted(e["defaults"])
        e["files"] = sorted(e["files"])
        e["patterns"] = sorted(e["patterns"])
    return dict(sorted(agg.items()))


def write_env_example(agg: dict[str, dict], path: Path) -> None:
    lines = [
        "# Автоматически сгенерировано find_env_vars.py",
        "# Проверьте значения и заполните реальные данные",
        "",
    ]
    for name, info in agg.items():
        defaults = info["defaults"]
        if defaults:
            lines.append(f"# default в коде: {', '.join(defaults)}")
        lines.append(f"{name}=")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def print_report(agg: dict[str, dict], occurrences: list[EnvOccurrence]) -> None:
    print(f"\n{'='*60}")
    print(f"Найдено уникальных переменных: {len(agg)}")
    print(f"Всего вхождений: {len(occurrences)}")
    print(f"{'='*60}\n")
    for name, info in agg.items():
        print(f"● {name}  (вхождений: {info['count']})")
        if info["defaults"]:
            print(f"    default: {', '.join(info['defaults'])}")
        for f in info["files"]:
            print(f"    → {f}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Поиск переменных окружения в кодовой базе")
    parser.add_argument("root", nargs="?", default=".", help="Корень проекта (по умолчанию .)")
    parser.add_argument("--json", metavar="FILE", help="Сохранить отчёт в JSON")
    parser.add_argument("--env-example", metavar="FILE", default=".env.example.generated",
                        help="Файл для сгенерированного .env.example")
    parser.add_argument("--no-non-py", action="store_true", help="Не сканировать YAML/Dockerfile/.env")
    parser.add_argument("--no-tests", action="store_true", help="Пропустить тестовые файлы")
    parser.add_argument("--quiet", action="store_true", help="Только записать файлы, не печатать отчёт")
    args = parser.parse_args()

    cfg = Config(
        root=Path(args.root).resolve(),
        include_non_py=not args.no_non_py,
        include_tests=not args.no_tests,
    )
    if not cfg.root.exists():
        print(f"Ошибка: путь не существует: {cfg.root}", file=sys.stderr)
        return 1

    occurrences = scan(cfg)
    agg = aggregate(occurrences)

    write_env_example(agg, Path(args.env_example))
    if args.json:
        Path(args.json).write_text(
            json.dumps(agg, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"JSON отчёт: {args.json}")
    print(f".env.example: {args.env_example}")

    if not args.quiet:
        print_report(agg, occurrences)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
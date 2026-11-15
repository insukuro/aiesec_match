"""Сводная таблица по результатам прогонов: python summarize.py out matcher matcher_cache backend ..."""
import csv
import sys
from pathlib import Path


def row(path, name):
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if r["Name"] == name:
            return r
    return None


def resources(path):
    if not Path(path).exists():
        return ""
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    hold = rows[len(rows) // 4: -max(1, len(rows) // 8)] or rows        # середина прогона, без разгона и спада
    parts = []
    for col in rows[0].keys():
        if col.startswith("cpu_") and col != "cpu_total":
            vals = [float(r[col]) for r in hold if r[col]]
            if vals:
                parts.append(f"{col[4:]} CPU {sum(vals) / len(vals):.0f}%")
        if col.startswith(("rss_mb_", "mem_mb_")):
            vals = [float(r[col]) for r in rows if r[col]]
            if vals:
                parts.append(f"{col.split('_mb_')[1]} RAM {max(vals):.0f} МБ")
    return ", ".join(parts)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    print("| Прогон | Пользователей | Операция | Запросов | Ошибок | RPS | p50, мс | p95, мс | p99, мс | Макс, мс | Ресурсы на полке |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for run in sys.argv[2:]:
        for u in (10, 50, 100):
            stats = out / f"{run}_u{u}_stats.csv"
            if not stats.exists():
                continue
            res = resources(out / f"{run}_u{u}_resources.csv")
            for r in csv.DictReader(open(stats, encoding="utf-8")):
                name = r["Name"]
                if name in ("GET /health",) or (run.startswith("backend") and name not in ("Aggregated", "POST /recommendations", "GET /opportunities")):
                    continue
                print(f"| {run} | {u} | {name} | {r['Request Count']} | {r['Failure Count']} | {float(r['Requests/s']):.1f} | "
                      f"{r['50%']} | {r['95%']} | {r['99%']} | {float(r['Max Response Time']):.0f} | {res if name == 'Aggregated' else ''} |")

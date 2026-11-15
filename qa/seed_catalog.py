"""Заливает N синтетических вакансий в parser.opportunities (для нагрузочного и объёмного тестов).

Примеры:
  python seed_catalog.py --n 1000          # добавить 1000 вакансий
  python seed_catalog.py --clean           # удалить всё, что добавил этот скрипт
Запускать только на dev или test окружении. Номера вакансий берутся из отдельного
диапазона 8 000 000 ... 8 999 999, настоящие вакансии не затрагиваются.
"""
import argparse
import os
import random

import psycopg

from catalog_data import delete_range, insert_rows, random_row

LO, HI = 8_000_000, 8_999_999
DSN = os.environ.get("QA_DB_PARSER_DSN", "postgresql://parser_writer:parser@postgres:5432/aiesec_match_dev")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--clean", action="store_true")
    a = ap.parse_args()
    with psycopg.connect(DSN) as conn:
        print("удалено старых синтетических:", delete_range(conn, LO, HI))
        if not a.clean:
            rnd = random.Random(a.seed)
            rows = [random_row(LO + i, rnd) for i in range(a.n)]
            for i in range(0, len(rows), 1000):
                insert_rows(conn, rows[i:i + 1000])
            print("добавлено:", len(rows))

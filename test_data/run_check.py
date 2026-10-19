"""Проверка бэкенда на работающем сервере: upload -> analyze -> report для двух нейросетей.
Запуск: python -X utf8 run_check.py  (сервер должен работать на :5000)"""
import json
import sys
from pathlib import Path

import requests

BASE = "http://127.0.0.1:5000"
here = Path(__file__).parent
out = here.parent / "reports"  # app/reports — в git не идёт
out.mkdir(exist_ok=True)

up = requests.post(f"{BASE}/api/upload", files={"file": open(here / "test_data.xlsx", "rb")}).json()
for provider, fname in (("yandex", "report-yandexgpt.pdf"), ("gigachat", "report-gigachat.pdf")):
    a = requests.post(f"{BASE}/api/analyze", json={"provider": provider, "columns": up["columns"],
                                                   "rows": up["rows"][:15]}, timeout=120).json()
    print("=====", provider, a.get("model"), a.get("seconds"), "с", a.get("error", ""))
    print(a.get("analysis", ""))
    (out / f"answer-{provider}.json").write_text(json.dumps(a, ensure_ascii=False, indent=1), encoding="utf-8")
    if "analysis" in a:
        r = requests.post(f"{BASE}/api/report", json={
            "filename": up["filename"], "columns": up["columns"], "rows": up["rows"][:15],
            "total_rows": up["total_rows"], "stats": up["stats"], "analysis": a["analysis"],
            "model": a["model"], "seconds": a["seconds"]})
        (out / fname).write_bytes(r.content)
        print("PDF:", fname, r.status_code, len(r.content))
sys.exit(0)

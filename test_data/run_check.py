"""Проверка бэкенда на работающем сервере: upload -> analyze -> report.
Запуск: python -X utf8 run_check.py [yandex] [gigachat] [local] [local-qwen]  (сервер должен работать на :5000;
без аргументов — две облачные модели)"""
import json
import sys
from pathlib import Path

import requests

BASE = "http://127.0.0.1:5000"
here = Path(__file__).parent
out = here.parent / "reports"  # app/reports — в git не идёт
out.mkdir(exist_ok=True)

up = requests.post(f"{BASE}/api/upload", files={"file": open(here / "test_data.xlsx", "rb")}).json()
FILES = {"yandex": "report-yandexgpt.pdf", "gigachat": "report-gigachat.pdf", "local": "report-local-gemma3.pdf",
         "local-qwen": "report-local-qwen3.pdf"}
for provider in sys.argv[1:] or ["yandex", "gigachat"]:
    fname = FILES[provider]
    a = requests.post(f"{BASE}/api/analyze", json={"provider": provider, "columns": up["columns"],
                                                   "rows": up["rows"][:15]},
                      timeout=4 * 3600 if provider.startswith("local") else 120).json()
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

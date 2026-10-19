"""Генерирует тестовые данные: test_data.xlsx, test_data.csv, test_table.pdf.
Запуск: backend/.venv/Scripts/python make_test_data.py"""
import random
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

random.seed(7)
here = Path(__file__).parent
months = ["2024-%02d" % m for m in range(1, 13)]
regions = {"Западная Сибирь": 1250, "Урал-Поволжье": 640, "Восточная Сибирь": 410}
price = {m: round(random.uniform(66, 78), 1) for m in months}

rows = []
for m in months:
    for reg, base in regions.items():
        prod = round(base * random.uniform(0.96, 1.04), 1)
        rev = round(prod * price[m] * 0.0735 * random.uniform(0.97, 1.03), 1)  # условная выручка, млн руб.
        rows.append([m, reg, prod, rev, price[m]])

df = pd.DataFrame(rows, columns=["Месяц", "Регион", "Добыча, тыс. т", "Выручка, млн руб.", "Цена нефти, $/барр."])
# Аномалии в первых 15 строках (месяцы 1-5)
df.loc[7, "Добыча, тыс. т"] = 215.4          # Март, Урал-Поволжье: резкий провал добычи (авария/остановка)
df.loc[7, "Выручка, млн руб."] = round(215.4 * price["2024-03"] * 0.0735, 1)
df.loc[11, "Выручка, млн руб."] = 14980.0   # Апрель, Восточная Сибирь: выручка в разы выше нормы при обычной добыче

df.to_excel(here / "test_data.xlsx", index=False)
df.to_csv(here / "test_data.csv", index=False, encoding="utf-8-sig")

# PDF с таблицей (первые 20 строк)
pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
data = [list(df.columns)] + [[str(v) for v in r] for r in df.head(20).itertuples(index=False)]
t = Table(data, repeatRows=1)
t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Arial"), ("FONTSIZE", (0, 0), (-1, -1), 8),
                       ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                       ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)]))
SimpleDocTemplate(str(here / "test_table.pdf"), pagesize=A4).build([t])
print(df.iloc[[7, 11]].to_string(), len(df))

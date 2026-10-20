"""Бэкенд ИИ-аналитика: загрузка таблицы (CSV/XLSX/PDF), анализ нейросетью, PDF-отчёт."""
import io
import re
import time
from datetime import datetime
from xml.sax.saxutils import escape

import pandas as pd
import pdfplumber
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from llm import gigachat, ollama_local, yandex_gpt
from llm.common import SYSTEM_PROMPT, user_message

app = Flask(__name__)
CORS(app)
app.json.ensure_ascii = False

N_ROWS = 15
PROVIDERS = {
    "yandex": (yandex_gpt, yandex_gpt.MODEL_NAME),
    "gigachat": (gigachat, gigachat.MODEL_NAME),
    "local": (ollama_local, ollama_local.MODEL_NAME),
}

# --- Шрифт с кириллицей для PDF (у коуча здесь были «?») ---
FONT, FONT_B = "ReportFont", "ReportFont-Bold"
for regular, bold in (("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
                      ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")):
    try:
        pdfmetrics.registerFont(TTFont(FONT, regular))
        pdfmetrics.registerFont(TTFont(FONT_B, bold))
        pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT_B, italic=FONT, boldItalic=FONT_B)
        break
    except Exception:  # noqa: BLE001
        continue


# ---------------- Разбор файлов ----------------

def parse_pdf(data: bytes) -> pd.DataFrame:
    rows = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                rows.extend(table)
    rows = [r for r in rows if r and any(c for c in r)]
    if len(rows) < 2:
        raise ValueError("В PDF не найдена таблица")
    header = [(c or f"col{i + 1}").replace("\n", " ").strip() for i, c in enumerate(rows[0])]
    body = [r for r in rows[1:] if [(c or "").strip() for c in r] != header]  # убираем повтор шапки на страницах
    df = pd.DataFrame(body, columns=header)
    for col in df.columns:  # в PDF всё текст — пробуем превратить числа обратно в числа
        conv = pd.to_numeric(df[col].astype(str).str.replace(" ", "").str.replace(",", "."), errors="coerce")
        if conv.notna().sum() >= 0.8 * df[col].notna().sum() and conv.notna().any():
            df[col] = conv
    return df


def parse_csv(data: bytes) -> pd.DataFrame:
    for enc in ("utf-8-sig", "cp1251"):
        try:
            return pd.read_csv(io.BytesIO(data), sep=None, engine="python", encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Не удалось прочитать кодировку CSV")


def parse_file(name: str, data: bytes) -> pd.DataFrame:
    low = name.lower()
    if low.endswith(".csv"):
        return parse_csv(data)
    if low.endswith((".xlsx", ".xlsm", ".xls")):
        return pd.read_excel(io.BytesIO(data))
    if low.endswith(".pdf"):
        return parse_pdf(data)
    raise ValueError("Поддерживаются файлы CSV, XLSX и PDF")


def cell(v):
    if pd.isna(v):
        return None
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.strftime("%Y-%m-%d")
    return v


def statistics(df: pd.DataFrame) -> dict:
    out = {}
    for col in df.select_dtypes("number").columns:
        s = df[col].dropna()
        if s.empty:
            continue
        out[str(col)] = {"count": int(s.count()), "mean": round(float(s.mean()), 2),
                         "min": round(float(s.min()), 2), "max": round(float(s.max()), 2),
                         "sum": round(float(s.sum()), 2)}
    return out


@app.post("/api/upload")
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify(error="Файл не передан"), 400
    try:
        df = parse_file(f.filename or "", f.read())
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"Не удалось прочитать файл: {e}"), 400
    df.columns = [str(c) for c in df.columns]
    return jsonify(filename=f.filename, columns=list(df.columns),
                   rows=[[cell(v) for v in r] for r in df.itertuples(index=False)],
                   total_rows=len(df), stats=statistics(df))


@app.post("/api/analyze")
def analyze():
    d = request.get_json(force=True)
    provider = d.get("provider")
    if provider not in PROVIDERS:
        return jsonify(error="provider должен быть yandex, gigachat или local"), 400
    module, model_name = PROVIDERS[provider]
    rows = (d.get("rows") or [])[:N_ROWS]
    t0 = time.monotonic()
    try:
        text = module.ask(SYSTEM_PROMPT, user_message(d.get("columns") or [], rows))
    except Exception as e:  # noqa: BLE001
        return jsonify(error=str(e)[:300]), 502
    return jsonify(analysis=text, provider=provider, model=model_name,
                   seconds=round(time.monotonic() - t0, 1), rows_sent=len(rows))


# ---------------- PDF-отчёт ----------------

def md_to_flowables(text: str, body: ParagraphStyle):
    """Минимальный markdown: **жирный**, списки (-, *, 1.), заголовки #."""
    items = []
    for line in text.splitlines():
        line = line.rstrip()
        if not line.strip():
            items.append(Spacer(1, 2 * mm))
            continue
        m = re.match(r"^\s*(?:[-*•]|\d+[.)])\s+(.*)", line)
        content = m.group(1) if m else re.sub(r"^#+\s*", "", line)
        html = escape(content)
        html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html)
        html = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", html)
        html = html.replace("`", "")
        if line.lstrip().startswith("#"):
            html = f"<b>{html}</b>"
        if m:
            items.append(Paragraph(html, body, bulletText="•"))
        else:
            items.append(Paragraph(html, body))
    return items


@app.post("/api/report")
def report():
    d = request.get_json(force=True)
    columns, rows = d.get("columns") or [], (d.get("rows") or [])[:N_ROWS]
    stats = d.get("stats") or {}
    base = ParagraphStyle("b", fontName=FONT, fontSize=10, leading=14)
    h1 = ParagraphStyle("h1", parent=base, fontName=FONT_B, fontSize=18, leading=22, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=base, fontName=FONT_B, fontSize=13, leading=16, spaceBefore=10, spaceAfter=4)
    small = ParagraphStyle("s", parent=base, fontSize=7, leading=9)
    smallb = ParagraphStyle("sb", parent=small, fontName=FONT_B)
    bullet = ParagraphStyle("bl", parent=base, leftIndent=14, bulletIndent=2)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm, title="Отчёт ИИ-аналитика")
    el = [Paragraph("Отчёт ИИ-аналитика", h1),
          Paragraph(f"Файл: <b>{escape(str(d.get('filename', '—')))}</b> &nbsp;|&nbsp; "
                    f"Дата: {datetime.now():%d.%m.%Y %H:%M}", base),
          Paragraph(f"Нейросеть: <b>{escape(str(d.get('model', '—')))}</b> &nbsp;|&nbsp; "
                    f"время ответа: {d.get('seconds', '—')} с &nbsp;|&nbsp; "
                    f"проанализировано строк: {len(rows)} из {d.get('total_rows', len(rows))}", base),
          Paragraph(f"Первые {len(rows)} строк таблицы", h2)]

    if columns:
        data = [[Paragraph(escape(str(c)), smallb) for c in columns]]
        for r in rows:
            data.append([Paragraph(escape("" if v is None else str(v)), small) for v in r])
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3e8ef")),
                               ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
        el.append(t)

    if stats:
        el.append(Paragraph("Статистика по числовым колонкам (весь файл)", h2))
        sd = [[Paragraph(x, smallb) for x in ("Колонка", "Кол-во", "Среднее", "Мин", "Макс", "Сумма")]]
        for k, v in stats.items():
            sd.append([Paragraph(escape(k), small)] + [Paragraph(str(v[x]), small)
                       for x in ("count", "mean", "min", "max", "sum")])
        st = Table(sd, repeatRows=1)
        st.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3e8ef"))]))
        el.append(st)

    el.append(Paragraph(f"Анализ от нейросети ({escape(str(d.get('model', '—')))})", h2))
    el.extend(md_to_flowables(d.get("analysis") or "Анализ не выполнен.", bullet))
    doc.build(el)
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name="report.pdf")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

#!/usr/bin/env python3
"""
generate_pdf.py — Render the Pathogen of the Week 1-page briefing PDF from data.json.

Usage:
    python3 generate_pdf.py [data.json] [output.pdf]

Defaults to ./data.json and ./pathogen-of-the-week.pdf in the script's directory.
Requires weasyprint:  pip install weasyprint --break-system-packages
"""
import json
import sys
from pathlib import Path
from html import escape

try:
    from weasyprint import HTML, CSS
except ImportError:
    sys.exit("ERROR: weasyprint is not installed. Run: pip install weasyprint --break-system-packages")


TAG_STYLES = {
    "acute":   {"bg": "#fee2e2", "bd": "#fca5a5", "fg": "#991b1b"},
    "smolder": {"bg": "#fef3c7", "bd": "#fcd34d", "fg": "#92400e"},
    "watch":   {"bg": "#dbeafe", "bd": "#93c5fd", "fg": "#1e40af"},
}

SCORE_DIMS = [
    ("severity",  "Severity"),
    ("novelty",   "Novelty"),
    ("attention", "Attention"),
    ("policy",    "Policy"),
    ("pandemic",  "Pandemic"),
]


def render_card(p: dict) -> str:
    tag = TAG_STYLES.get(p["tag"], TAG_STYLES["watch"])
    lead = '<span class="lead-pill">LEAD</span>' if p.get("is_lead") else ""
    stats_html = "".join(
        f'<div class="stat"><div class="num {escape(s.get("tone","neutral"))}">{escape(s["num"])}</div>'
        f'<div class="lbl">{escape(s["label"])}</div></div>'
        for s in p["stats"]
    )
    scores = p["scores"]
    score_rows = ""
    for key, label in SCORE_DIMS:
        v = float(scores.get(key, 0))
        pct = max(0.0, min(100.0, v * 10))
        score_rows += (
            f'<div class="score-row">'
            f'<span class="score-lbl">{label}</span>'
            f'<span class="score-bar"><span style="width:{pct:.1f}%"></span></span>'
            f'<span class="score-val">{v:.1f}</span>'
            f'</div>'
        )
    bullets = "".join(f"<li>{escape(b)}</li>" for b in p["policy_bullets"][:3])
    composite = sum(scores[k] for k, _ in SCORE_DIMS) / len(SCORE_DIMS)
    return f"""
    <article class="card">
      <header class="card-head" style="background:{tag['bg']};border-color:{tag['bd']};">
        <div class="tag" style="color:{tag['fg']};">{escape(p['tag_label'])}{lead}</div>
        <h3>{escape(p['name'])}</h3>
        <div class="latin">{escape(p['scientific_name'])}</div>
        <div class="where">{escape(p['location'])}</div>
      </header>
      <div class="stats">{stats_html}</div>
      <div class="scores">{score_rows}
        <div class="composite">Composite: <b>{composite:.1f}</b> / 10</div>
      </div>
      <div class="why">
        <h4>Why it matters</h4>
        <p>{escape(p['why'])}</p>
      </div>
      <div class="policy">
        <h4>For policymakers</h4>
        <ul>{bullets}</ul>
      </div>
    </article>
    """


def render_html(data: dict) -> str:
    week_label = (
        f"ISO Week {data['iso_week']} · "
        f"Mon {data['week_start'][-2:].lstrip('0')} – "
        f"Sun {data['week_end'][-2:].lstrip('0')} "
        f"{_month_name(data['week_end'])} {data['iso_year']}"
    )
    cards = "\n".join(render_card(p) for p in data["pathogens"])
    takeaway = escape(data["headline"]["takeaway"])
    summary = escape(data["headline"]["summary"])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Pathogen of the Week — {escape(week_label)}</title>
<style>
@page {{
  size: A4 landscape;
  margin: 10mm 12mm 9mm 12mm;
}}
* {{ box-sizing: border-box; }}
html, body {{
  margin: 0; padding: 0;
  font-family: -apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif;
  color: #0f172a;
  font-size: 8.5pt;
  line-height: 1.32;
}}
header.page-head {{
  display: flex; justify-content: space-between; align-items: flex-end;
  border-bottom: 1.5pt solid #0f172a; padding-bottom: 4pt; margin-bottom: 5pt;
}}
header.page-head .brand {{
  font-size: 14pt; font-weight: 700; letter-spacing: -0.01em;
}}
header.page-head .brand small {{
  display: block; font-size: 8pt; color: #475569; font-weight: 500; margin-top: 1pt; letter-spacing: 0;
}}
header.page-head .week {{
  text-align: right;
  font-size: 8.5pt; color: #475569;
}}
header.page-head .week b {{ color: #0f172a; }}

.hero {{
  background: #f1f5f9;
  border-left: 3pt solid #0f172a;
  padding: 6pt 9pt;
  margin-bottom: 6pt;
  font-size: 8.2pt;
}}
.hero .label {{
  font-size: 7pt; text-transform: uppercase; letter-spacing: 0.06em; color: #64748b;
  font-weight: 600; margin-bottom: 2pt;
}}
.hero p {{ margin: 0 0 2pt; }}
.hero .take {{ font-size: 8.2pt; }}
.hero .take b {{ color: #0f172a; }}

.cards {{
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 5pt;
}}
.card {{
  border: 0.75pt solid #cbd5e1;
  border-radius: 4pt;
  overflow: hidden;
  page-break-inside: avoid;
  background: #fff;
}}
.card-head {{
  padding: 5pt 7pt 6pt;
  border-bottom: 0.5pt solid;
}}
.card-head .tag {{
  font-size: 6.5pt; text-transform: uppercase; letter-spacing: 0.08em;
  font-weight: 700;
  display: flex; align-items: center; gap: 4pt;
  margin-bottom: 3pt;
}}
.card-head .lead-pill {{
  background: #0f172a; color: #fff; padding: 1pt 4pt; border-radius: 99pt; font-size: 6pt;
}}
.card-head h3 {{
  margin: 0; font-size: 11pt; letter-spacing: -0.01em;
}}
.card-head .latin {{
  font-style: italic; color: #475569; font-size: 7pt; margin-top: 1pt;
}}
.card-head .where {{
  color: #475569; font-size: 7pt; margin-top: 2pt;
}}

.stats {{
  display: grid; grid-template-columns: 1fr 1fr 1fr;
  border-bottom: 0.5pt solid #e2e8f0;
}}
.stat {{
  padding: 4pt 5pt;
  border-right: 0.5pt solid #e2e8f0;
  text-align: center;
}}
.stat:last-child {{ border-right: none; }}
.stat .num {{
  font-size: 13pt; font-weight: 700; letter-spacing: -0.02em;
  color: #0f172a;
}}
.stat .num.crit {{ color: #b91c1c; }}
.stat .num.warn {{ color: #b45309; }}
.stat .num.ok   {{ color: #047857; }}
.stat .lbl {{
  font-size: 6pt; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;
  margin-top: 1pt;
}}

.scores {{
  padding: 5pt 7pt 4pt;
  border-bottom: 0.5pt solid #e2e8f0;
}}
.score-row {{
  display: grid; grid-template-columns: 38pt 1fr 18pt;
  align-items: center; gap: 4pt;
  margin-bottom: 2pt;
  font-size: 7pt;
}}
.score-row .score-lbl {{ color: #475569; }}
.score-row .score-val {{ text-align: right; font-variant-numeric: tabular-nums; color: #0f172a; font-weight: 600; }}
.score-bar {{
  height: 3pt; background: #e2e8f0; border-radius: 99pt; overflow: hidden; display: block;
}}
.score-bar > span {{
  display: block; height: 100%;
  background: linear-gradient(90deg, #0ea5e9, #6366f1);
}}
.composite {{
  margin-top: 3pt; font-size: 7pt; color: #475569; text-align: right;
}}
.composite b {{ color: #0f172a; }}

.why, .policy {{
  padding: 5pt 7pt;
}}
.why h4, .policy h4 {{
  margin: 0 0 2pt; font-size: 6.5pt; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.07em; font-weight: 700;
}}
.why p {{ margin: 0; font-size: 7.2pt; }}
.policy {{ border-top: 0.5pt solid #e2e8f0; }}
.policy ul {{ margin: 0; padding-left: 11pt; }}
.policy li {{ font-size: 7.2pt; margin-bottom: 1.5pt; }}

footer.page-foot {{
  margin-top: 5pt;
  border-top: 0.5pt solid #cbd5e1;
  padding-top: 3pt;
  font-size: 6.5pt;
  color: #64748b;
  display: flex; justify-content: space-between; align-items: center;
}}
footer.page-foot b {{ color: #0f172a; }}
footer.page-foot a {{ color: #0f172a; text-decoration: none; }}
</style>
</head>
<body>
  <header class="page-head">
    <div class="brand">Pathogen of the Week
      <small>Weekly briefing for policymakers · WHO · ECDC · CDC · open-source signals</small>
    </div>
    <div class="week">
      <b>{escape(week_label)}</b><br>
      Produced {escape(data['produced_on'])}
    </div>
  </header>

  <section class="hero">
    <div class="label">This week at a glance</div>
    <p>{summary}</p>
    <p class="take"><b>Bottom line:</b> {takeaway}</p>
  </section>

  <section class="cards">
    {cards}
  </section>

  <footer class="page-foot">
    <span>Full sources, interactive radar, expanded details → <a href="{escape(data.get('site_url',''))}">{escape(data.get('site_url',''))}</a></span>
    <span>ISO Week {data['iso_week']} · {data['iso_year']} · auto-regenerated every Monday</span>
  </footer>
</body></html>
"""


def _month_name(date_str: str) -> str:
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return months[int(date_str.split("-")[1]) - 1]


def main():
    here = Path(__file__).parent
    data_path = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "data.json"
    out_path  = Path(sys.argv[2]) if len(sys.argv) > 2 else here / "pathogen-of-the-week.pdf"

    if not data_path.exists():
        sys.exit(f"ERROR: data file not found: {data_path}")

    data = json.loads(data_path.read_text(encoding="utf-8"))
    html = render_html(data)

    debug_html = out_path.with_suffix(".print.html")
    debug_html.write_text(html, encoding="utf-8")

    HTML(string=html, base_url=str(here)).write_pdf(str(out_path))
    print(f"Wrote {out_path}  ({out_path.stat().st_size} bytes)")
    print(f"Print HTML preview: {debug_html}")


if __name__ == "__main__":
    main()

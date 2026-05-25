#!/usr/bin/env python3
"""
Generate index.html from data.json.
Preserves design; updates content from data.
"""

import json
from datetime import datetime

with open('data.json', 'r') as f:
    data = json.load(f)

iso_week = data['iso_week']
iso_year = data['iso_year']
week_start = data['week_start']  # YYYY-MM-DD
week_end = data['week_end']      # YYYY-MM-DD
headline = data['headline']
pathogens = data['pathogens']
all_sources = data['all_sources']

# Parse dates for display
from datetime import datetime as dt
start = dt.strptime(week_start, '%Y-%m-%d')
end = dt.strptime(week_end, '%Y-%m-%d')
week_range = f"{start.strftime('%a %d')} – {end.strftime('%a %d %b %Y')}"
title = f"Pathogen of the Week — Week {iso_week}, {iso_year} ({week_range})"
footer_date = dt.now().strftime('%d %b %Y')

# Build radar data: [severity, novelty, attention, policy, pandemic] per pathogen
radar_data = []
for p in pathogens:
    scores = p['scores']
    radar_data.append([
        scores['severity'],
        scores['novelty'],
        scores['attention'],
        scores['policy'],
        scores['pandemic']
    ])

# Build signal table rows (composite = mean of 5 scores)
signal_rows = []
for p in pathogens:
    scores = p['scores']
    values = [scores['severity'], scores['novelty'], scores['attention'], scores['policy'], scores['pandemic']]
    composite = round(sum(values) / len(values), 1)
    signal_rows.append(f"""            <tr>
              <td>{p['name']}</td>
              <td>{scores['severity']}</td>
              <td>{scores['novelty']}</td>
              <td>{scores['attention']}</td>
              <td>{scores['policy']}</td>
              <td>{scores['pandemic']}</td>
              <td class="composite">{composite}</td>
            </tr>""")

# Build card HTML blocks
cards_html = []
for p in pathogens:
    tag_class = p['tag']  # acute, smolder, watch
    tag_label = p['tag_label']
    is_lead = ' lead' if p['is_lead'] else ''

    # Stats rows
    stats_html = '\n'.join([
        f'                <div class="stat"><span class="num">{s["num"]}</span><span class="label">{s["label"]}</span></div>'
        for s in p['stats']
    ])

    # Score bars
    scores = p['scores']
    score_bars = '\n'.join([
        f'                <div class="bar-group"><span class="bar-label">Severity</span><div class="bar-outer"><div class="bar-inner" style="width: {scores["severity"]*10}%"></div></div><span class="bar-value">{scores["severity"]}</span></div>',
        f'                <div class="bar-group"><span class="bar-label">Novelty</span><div class="bar-outer"><div class="bar-inner" style="width: {scores["novelty"]*10}%"></div></div><span class="bar-value">{scores["novelty"]}</span></div>',
        f'                <div class="bar-group"><span class="bar-label">Attention</span><div class="bar-outer"><div class="bar-inner" style="width: {scores["attention"]*10}%"></div></div><span class="bar-value">{scores["attention"]}</span></div>',
        f'                <div class="bar-group"><span class="bar-label">Policy urgency</span><div class="bar-outer"><div class="bar-inner" style="width: {scores["policy"]*10}%"></div></div><span class="bar-value">{scores["policy"]}</span></div>',
        f'                <div class="bar-group"><span class="bar-label">Pandemic potential</span><div class="bar-outer"><div class="bar-inner" style="width: {scores["pandemic"]*10}%"></div></div><span class="bar-value">{scores["pandemic"]}</span></div>'
    ])

    # Sources
    sources_html = '\n'.join([
        f'                <li><a href="{s["url"]}">{s["label"]}</a></li>'
        for s in p['sources']
    ])

    card = f'''          <article class="card {tag_class}{is_lead}">
            <div class="card-head">
              <div>
                <h2>{p['name']}</h2>
                <span class="tag">{tag_label}</span>
              </div>
            </div>
            <div class="card-body">
              <p><strong>{p['scientific_name']}</strong></p>
              <p><em>Location:</em> {p['location']}</p>
              <div class="stats">
{stats_html}
              </div>
              <div class="scores">
{score_bars}
              </div>
              <div class="narrative">
                <h3>Why this matters</h3>
                <p>{p['why']}</p>
              </div>
              <div class="bullets">
                <h3>Policy bullets</h3>
                <ul>
{''.join([f"<li>{b}</li>" for b in p['policy_bullets']])}
                </ul>
              </div>
              <div class="details">
                <h3>Key facts</h3>
                <dl>
{''.join([f"<dt>{k}</dt><dd>{v}</dd>" for k, v in p['details'].items()])}
                </dl>
              </div>
              <div class="sources">
                <h4>Sources</h4>
                <ul>
{sources_html}
                </ul>
              </div>
            </div>
          </article>'''
    cards_html.append(card)

# All sources list
all_sources_html = '\n'.join([
    f'        <li><strong>{s["org"]}:</strong> <a href="{s["url"]}">{s["title"]}</a></li>'
    for s in all_sources
])

html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<meta name="description" content="{headline['summary']}" />

<!-- Open Graph / social share preview -->
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Pathogen of the Week" />
<meta property="og:url" content="https://ivetyorda.github.io/pathogen-of-the-week/" />
<meta property="og:title" content="Pathogen of the Week — Week {iso_week}, {iso_year}: {pathogens[0]['name']}" />
<meta property="og:description" content="Week {iso_week} · {week_range}. {pathogens[0]['stats'][0]['num']} {pathogens[0]['stats'][0]['label']} · {pathogens[0]['stats'][1]['num']} {pathogens[0]['stats'][1]['label']} · {pathogens[0]['stats'][2]['num']} {pathogens[0]['stats'][2]['label']}" />
<meta property="og:image" content="https://ivetyorda.github.io/pathogen-of-the-week/og-image.png?v={iso_year}-W{iso_week}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="Pathogen of the Week — Week {iso_week}, {iso_year}: {pathogens[0]['name']}" />

<!-- Twitter / X card -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Pathogen of the Week — Week {iso_week}, {iso_year}: {pathogens[0]['name']}" />
<meta name="twitter:description" content="Week {iso_week} · {week_range}. {pathogens[0]['stats'][0]['num']} {pathogens[0]['stats'][0]['label']} · {pathogens[0]['stats'][1]['num']} {pathogens[0]['stats'][1]['label']} · {pathogens[0]['stats'][2]['num']} {pathogens[0]['stats'][2]['label']}" />
<meta name="twitter:image" content="https://ivetyorda.github.io/pathogen-of-the-week/og-image.png?v={iso_year}-W{iso_week}" />

<link rel="canonical" href="https://ivetyorda.github.io/pathogen-of-the-week/" />
<style>
  :root {{
    --bg: #0b1020;
    --bg-elev: #131a32;
    --bg-soft: #1a2244;
    --line: #263158;
    --text: #e8ecf7;
    --muted: #9aa3c2;
    --accent: #6ee7ff;
    --accent-2: #a78bfa;
    --crit: #f87171;
    --warn: #fbbf24;
    --ok: #34d399;
    --acute-bg: rgba(248,113,113,0.12);
    --acute-bd: rgba(248,113,113,0.45);
    --smolder-bg: rgba(251,191,36,0.12);
    --smolder-bd: rgba(251,191,36,0.45);
    --watch-bg: rgba(110,231,255,0.10);
    --watch-bd: rgba(110,231,255,0.40);
    --shadow: 0 12px 40px rgba(0,0,0,0.45);
    --radius: 14px;
  }}
  @media (prefers-color-scheme: light) {{
    /* keep dark theme regardless; this dashboard is briefing-room style */
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0;
    background:
      radial-gradient(1200px 600px at 80% -10%, rgba(167,139,250,0.18), transparent 60%),
      radial-gradient(900px 500px at -10% 20%, rgba(110,231,255,0.10), transparent 60%),
      var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .wrap {{ max-width: 1280px; margin: 0 auto; padding: 28px 24px 80px; }}

  /* Header */
  header.top {{
    display: flex; align-items: flex-start; justify-content: space-between;
    gap: 24px; flex-wrap: wrap; margin-bottom: 28px;
  }}
  .brand {{
    display: flex; align-items: center; gap: 14px;
  }}
  .brand-mark {{
    width: 44px; height: 44px; border-radius: 12px;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    display: grid; place-items: center;
    box-shadow: var(--shadow);
  }}
  .brand-mark svg {{ width: 26px; height: 26px; }}
  h1 {{
    font-size: 26px; margin: 0; letter-spacing: -0.01em;
  }}
  .sub {{
    color: var(--muted); font-size: 14px; margin-top: 2px;
  }}
  .meta {{
    display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
    font-size: 13px; color: var(--muted);
  }}
  .chip {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 10px; border-radius: 999px;
    background: var(--bg-elev); border: 1px solid var(--line);
    color: var(--text); font-size: 12px;
  }}
  .chip .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--ok); }}
  .chip.live .dot {{ background: var(--crit); box-shadow: 0 0 0 4px rgba(248,113,113,0.15); animation: pulse 2s infinite; }}
  @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} 100% {{ opacity: 1; }} }}

  /* Hero */
  .hero {{ margin-bottom: 48px; }}
  .hero h2 {{ font-size: 18px; margin: 0 0 12px; color: var(--muted); font-weight: 500; }}
  .hero p {{ font-size: 16px; margin: 0; line-height: 1.6; }}

  /* Cards */
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 20px; margin-bottom: 48px; }}
  article.card {{
    background: var(--bg-elev); border: 1px solid var(--line); border-radius: var(--radius);
    box-shadow: var(--shadow); overflow: hidden;
  }}
  article.card.lead {{ border-color: var(--accent); }}
  article.card.acute {{ border-color: var(--crit); background: linear-gradient(135deg, var(--bg-elev) 0%, rgba(248,113,113,0.04) 100%); }}
  article.card.smolder {{ border-color: var(--warn); background: linear-gradient(135deg, var(--bg-elev) 0%, rgba(251,191,36,0.04) 100%); }}
  article.card.watch {{ border-color: var(--accent); background: linear-gradient(135deg, var(--bg-elev) 0%, rgba(110,231,255,0.04) 100%); }}

  .card-head {{
    padding: 16px 20px; border-bottom: 1px solid var(--line);
    display: flex; justify-content: space-between; align-items: flex-start;
  }}
  .card-head h2 {{ font-size: 18px; margin: 0 0 4px; }}
  .tag {{
    display: inline-block; font-size: 11px; padding: 4px 8px; border-radius: 6px;
    background: var(--bg-soft); color: var(--muted); font-weight: 500; margin-top: 4px;
  }}

  .card-body {{ padding: 20px; }}
  .card-body > p {{ margin: 0 0 16px; font-size: 14px; color: var(--muted); }}
  .card-body h3 {{ font-size: 13px; margin: 20px 0 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }}
  .card-body h4 {{ font-size: 12px; margin: 12px 0 8px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }}

  /* Stats */
  .stats {{ display: flex; flex-wrap: wrap; gap: 12px; margin: 16px 0; }}
  .stat {{ flex: 1; min-width: 120px; padding: 10px; background: var(--bg-soft); border-radius: 8px; }}
  .stat .num {{ display: block; font-size: 18px; font-weight: 600; color: var(--accent); }}
  .stat .label {{ display: block; font-size: 11px; color: var(--muted); margin-top: 4px; }}

  /* Scores */
  .scores {{ margin: 16px 0; }}
  .bar-group {{ margin: 12px 0; }}
  .bar-label {{ display: inline-block; font-size: 12px; color: var(--muted); width: 100px; }}
  .bar-outer {{ display: inline-block; width: calc(100% - 110px); height: 6px; background: var(--bg-soft); border-radius: 3px; vertical-align: middle; margin: 0 6px; }}
  .bar-inner {{ height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-2)); border-radius: 3px; }}
  .bar-value {{ display: inline-block; width: 30px; text-align: right; font-size: 12px; color: var(--text); }}

  /* Narrative */
  .narrative p, .details p {{ font-size: 14px; line-height: 1.6; margin: 0 0 12px; }}
  .narrative {{ margin: 16px 0; }}

  /* Bullets */
  .bullets ul {{ margin: 8px 0; padding-left: 20px; }}
  .bullets li {{ font-size: 13px; margin: 6px 0; line-height: 1.5; color: var(--text); }}

  /* Details */
  .details {{ margin: 16px 0; }}
  .details dl {{ margin: 0; }}
  .details dt {{ font-size: 12px; color: var(--muted); font-weight: 500; margin-top: 8px; }}
  .details dd {{ font-size: 13px; margin: 2px 0 0 0; color: var(--text); }}

  /* Sources */
  .sources {{ margin: 16px 0; }}
  .sources ul {{ margin: 8px 0; padding-left: 20px; list-style: none; }}
  .sources li {{ font-size: 12px; margin: 4px 0; }}
  .sources a {{ color: var(--accent); }}

  /* Signal table */
  .signal-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 16px 0; }}
  .signal-table th {{ text-align: left; padding: 10px; background: var(--bg-soft); color: var(--muted); font-weight: 500; border-bottom: 1px solid var(--line); }}
  .signal-table td {{ padding: 10px; border-bottom: 1px solid var(--line); }}
  .signal-table tr:last-child td {{ border-bottom: none; }}
  .signal-table .composite {{ font-weight: 600; color: var(--accent); }}

  /* Radar (SVG) */
  .radar {{ margin: 24px 0; }}
  .radar-label {{ font-size: 11px; color: var(--muted); }}
  .radar-grid {{ stroke: var(--line); }}
  .radar-axis {{ stroke: var(--line); }}
  .radar-poly {{ fill: none; stroke-width: 2; }}
  .radar-poly:nth-child(1) {{ stroke: var(--crit); opacity: 0.7; }}
  .radar-poly:nth-child(2) {{ stroke: var(--warn); opacity: 0.7; }}
  .radar-poly:nth-child(3) {{ stroke: var(--accent); opacity: 0.7; }}
  .radar-poly:nth-child(4) {{ stroke: var(--accent-2); opacity: 0.7; }}

  /* Sections */
  .section {{ margin-bottom: 48px; }}
  .section h2 {{ font-size: 18px; margin: 0 0 16px; }}
  .section ul {{ padding-left: 20px; }}
  .section li {{ font-size: 14px; margin: 8px 0; line-height: 1.5; }}

  /* Footer */
  footer {{ color: var(--muted); font-size: 12px; text-align: center; padding-top: 24px; border-top: 1px solid var(--line); margin-top: 60px; }}

  /* Download chip */
  .download-chip {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 14px; background: linear-gradient(135deg, var(--accent), var(--accent-2));
    color: var(--bg); border-radius: 999px; font-size: 13px; font-weight: 500;
    text-decoration: none; cursor: pointer;
  }}
  .download-chip:hover {{ opacity: 0.9; }}

  @media (max-width: 768px) {{
    .wrap {{ padding: 16px 16px 60px; }}
    h1 {{ font-size: 20px; }}
    .cards {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div class="brand">
      <div class="brand-mark">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M12 3v18M3 9l6-6 6 6-6 6-6-6M15 3l6 6-6 6-6-6 6-6z"/></svg>
      </div>
      <div>
        <h1>Pathogen of the Week</h1>
        <p class="sub">ISO Week {iso_week} · Mon {start.strftime('%d')} – Sun {end.strftime('%d %b %Y')}</p>
      </div>
    </div>
    <div class="meta">
      <span class="chip live"><span class="dot"></span> This week</span>
    </div>
  </header>

  <section class="hero">
    <h2>{headline['title']}</h2>
    <p>{headline['summary']}</p>
  </section>

  <div class="cards">
{''.join(cards_html)}
  </div>

  <section class="section">
    <h2>Risk signal summary</h2>
    <table class="signal-table">
      <thead>
        <tr>
          <th>Pathogen</th>
          <th>Severity</th>
          <th>Novelty</th>
          <th>Attention</th>
          <th>Policy</th>
          <th>Pandemic</th>
          <th>Composite</th>
        </tr>
      </thead>
      <tbody>
{''.join(signal_rows)}
      </tbody>
    </table>
    <p style="font-size: 12px; color: var(--muted); margin-top: 12px;"><em>Composite = mean of the 5 signal scores, rounded to 1 decimal. Severity, novelty, attention, policy urgency and pandemic potential each scored 0–10.</em></p>
  </section>

  <section class="section">
    <h2>Radar</h2>
    <svg class="radar" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;">
      <!-- Concentric circles (grid) -->
      <circle cx="200" cy="200" r="30" class="radar-grid" fill="none" stroke-dasharray="4,4" opacity="0.3"/>
      <circle cx="200" cy="200" r="60" class="radar-grid" fill="none" stroke-dasharray="4,4" opacity="0.3"/>
      <circle cx="200" cy="200" r="90" class="radar-grid" fill="none" stroke-dasharray="4,4" opacity="0.3"/>
      <circle cx="200" cy="200" r="120" class="radar-grid" fill="none" stroke-dasharray="4,4" opacity="0.3"/>
      <circle cx="200" cy="200" r="150" class="radar-grid" fill="none" stroke-dasharray="4,4" opacity="0.3"/>

      <!-- Axes to 5 vertices -->
      <line x1="200" y1="200" x2="200" y2="50" class="radar-axis" opacity="0.3"/>
      <line x1="200" y1="200" x2="345" y2="95" class="radar-axis" opacity="0.3"/>
      <line x1="200" y1="200" x2="345" y2="305" class="radar-axis" opacity="0.3"/>
      <line x1="200" y1="200" x2="55" y2="305" class="radar-axis" opacity="0.3"/>
      <line x1="200" y1="200" x2="55" y2="95" class="radar-axis" opacity="0.3"/>

      <!-- Pentagon outline -->
      <polygon points="200,50 345,95 345,305 55,305 55,95" class="radar-grid" fill="none" opacity="0.2"/>

      <!-- Polygons for each pathogen -->
      <script type="text/javascript">
        (function() {{
          const data = {json.dumps(radar_data)};
          const labels = ['Severity', 'Novelty', 'Attention', 'Policy', 'Pandemic'];
          const cx = 200, cy = 200, maxRadius = 150;

          data.forEach((scores, idx) => {{
            const points = [];
            const angleStep = (Math.PI * 2) / 5;
            for (let i = 0; i < 5; i++) {{
              const angle = i * angleStep - Math.PI / 2;
              const r = (scores[i] / 10) * maxRadius;
              const x = cx + r * Math.cos(angle);
              const y = cy + r * Math.sin(angle);
              points.push([x, y]);
            }}

            const svg = document.querySelector('svg.radar');
            const pointsStr = points.map(p => p.join(',')).join(' ');
            const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            poly.setAttribute('points', pointsStr);
            poly.setAttribute('class', 'radar-poly');
            svg.appendChild(poly);
          }});

          // Labels
          const labelPositions = [
            [200, 25],
            [345, 85],
            [345, 315],
            [55, 315],
            [55, 85]
          ];

          labels.forEach((label, i) => {{
            const svg = document.querySelector('svg.radar');
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', labelPositions[i][0]);
            text.setAttribute('y', labelPositions[i][1]);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'middle');
            text.setAttribute('class', 'radar-label');
            text.textContent = label;
            svg.appendChild(text);
          }});
        }})();
      </script>
    </svg>
    <p style="font-size: 12px; color: var(--muted); margin-top: 12px;"><em>Each axis represents a signal (0–10 scale). Outer edge = 10. Closer to center = lower score. Each polygon = one pathogen.</em></p>
  </section>

  <section class="section">
    <h2>All sources</h2>
    <ul>
{all_sources_html}
    </ul>
  </section>

  <section class="section">
    <h2>Methodology</h2>
    <p>Each week, we scan WHO Disease Outbreak News, ECDC Communicable Disease Threat Reports, CDC HAN advisories, and major news outlets (Reuters, AP, BBC, Nature, NEJM, CIDRAP, national broadcasters) for emerging infectious disease signals.</p>
    <p>We select the top 3 pathogens and assign each a profile:</p>
    <ul>
      <li><strong>ACUTE/LEAD:</strong> High novelty, high attention, rapid escalation, policy-critical.</li>
      <li><strong>ACUTE:</strong> Active investigation, cross-border spread, public health response ongoing.</li>
      <li><strong>SMOLDERING:</strong> Persistent transmission, moderate severity, policy gaps.</li>
      <li><strong>WATCH:</strong> High pandemic potential, emerging drug resistance, zoonotic risk.</li>
    </ul>
    <p>Each pathogen is scored 0–10 on five dimensions:</p>
    <ul>
      <li><strong>Severity:</strong> Case fatality rate, hospitalization burden, organ damage.</li>
      <li><strong>Novelty:</strong> First appearance, emergence in unexpected populations, new variant.</li>
      <li><strong>Attention:</strong> Media coverage intensity, public concern, health worker alarm.</li>
      <li><strong>Policy urgency:</strong> Regulatory action needed, treatment/vaccine gaps, border risk.</li>
      <li><strong>Pandemic potential:</strong> Basic reproduction number, transmission mode, geographic spread.</li>
    </ul>
  </section>

  <div style="text-align: center; margin: 40px 0; padding: 20px; border-top: 1px solid var(--line);">
    <a href="pathogen-of-the-week.pdf" class="download-chip">📄 Download PDF briefing</a>
  </div>

  <footer>
    <p>Pathogen of the Week briefing · produced {footer_date}</p>
    <p style="font-size: 11px; margin-top: 8px;">For policymakers, health officers, and epidemiologists. Data drawn from official public health sources. Not investment or medical advice.</p>
  </footer>
</div>
</body>
</html>
'''

with open('index.html', 'w') as f:
    f.write(html)

print(f"✓ Wrote index.html (Week {iso_week}, {iso_year})")

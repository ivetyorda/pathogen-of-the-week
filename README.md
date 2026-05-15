# Pathogen of the Week

A weekly briefing on the most relevant infectious-disease threats, tuned for policymakers and decision-makers.

**Live dashboard:** https://ivetyorda.github.io/pathogen-of-the-week/
**1-page PDF:** https://ivetyorda.github.io/pathogen-of-the-week/pathogen-of-the-week.pdf
**Archive of past weeks:** [`archive/`](archive/)

The dashboard surfaces three pathogens each ISO week (Monday–Sunday) and scores them across five dimensions (severity, novelty, public attention, policy urgency, pandemic potential). One is the acute lead story; one is a smoldering ongoing concern; one is a watch-list entry.

## Data sources

- WHO Disease Outbreak News
- ECDC Communicable Disease Threats Report
- CDC Health Alert Network and Current Outbreak List
- Open-source media and news signals (Reuters, AP, BBC, CNN, Nature, NEJM, CIDRAP, national broadcasters)

All numeric claims on every card carry a primary-source link in the expandable detail panel.

## Repo layout

```
.
├── index.html                 # The dashboard (GitHub Pages serves this)
├── pathogen-of-the-week.pdf   # Latest 1-page PDF briefing
├── data.json                  # Structured source of truth for the current week
├── generate_pdf.py            # Renders the PDF from data.json (weasyprint)
├── archive/                   # Dated copies, one HTML + one PDF per ISO week
│   ├── pathogen-of-the-week-2026-W20.html
│   └── pathogen-of-the-week-2026-W20.pdf
└── README.md
```

## Update cadence

A Cowork scheduled task runs every Monday at 07:00 local time. It:

1. Computes the new ISO week window (Mon–Sun)
2. Queries WHO / ECDC / CDC and news sources in parallel
3. Scores candidate pathogens and selects three
4. Rewrites `data.json` and `index.html`
5. Regenerates the PDF via `python3 generate_pdf.py`
6. Archives both files into `archive/`
7. Commits and pushes to this repo — GitHub Pages re-deploys within ~60 seconds

## Regenerate the PDF locally

```bash
pip install weasyprint --break-system-packages
python3 generate_pdf.py            # uses ./data.json → ./pathogen-of-the-week.pdf
```

## Disclaimer

This briefing is an editorial synthesis of public sources. It is not medical advice and is not an official communication from any health authority. Always confirm critical numbers against the cited primary source before quoting.

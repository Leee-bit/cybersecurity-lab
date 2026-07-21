"""
report.py
---------
Renders risk_register.json as a single-file HTML dashboard.
"""

import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent / "output"

LEVEL_COLORS = {
    "CRITICAL": "#B3261E",
    "HIGH": "#C4590C",
    "MEDIUM": "#8A6D00",
    "LOW": "#2E7D32",
}


def render():
    with open(OUTPUT_DIR / "risk_register.json") as f:
        register = json.load(f)

    total_instances = sum(r["instances_found"] for r in register)
    critical_count = sum(1 for r in register if r["risk_level"] == "CRITICAL")
    high_count = sum(1 for r in register if r["risk_level"] == "HIGH")

    rows_html = ""
    for r in register:
        color = LEVEL_COLORS.get(r["risk_level"], "#555")
        files = ", ".join(r["files_affected"])
        rows_html += f"""
        <tr>
          <td><strong>{r['type'].replace('_', ' ').title()}</strong></td>
          <td>{r['instances_found']}</td>
          <td>{files}</td>
          <td>{r['sensitivity']}</td>
          <td>{r['likelihood']}</td>
          <td>{r['risk_score']}</td>
          <td><span class="badge" style="background:{color}">{r['risk_level']}</span></td>
          <td>{r['ipp_reference']}</td>
          <td>{r['iso27799_reference']}</td>
          <td>{r['recommended_control']}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Privacy Risk Register - Synthetic Healthcare Data Scan</title>
<style>
  :root {{
    --bg: #0f1115;
    --panel: #171a21;
    --border: #2a2e38;
    --text: #e6e8ec;
    --muted: #9aa1ac;
    --accent: #4fa3ff;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0;
    padding: 40px;
  }}
  h1 {{ font-size: 22px; margin-bottom: 4px; }}
  .subtitle {{ color: var(--muted); font-size: 13px; margin-bottom: 28px; }}
  .summary {{
    display: flex;
    gap: 16px;
    margin-bottom: 28px;
    flex-wrap: wrap;
  }}
  .stat {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    min-width: 140px;
  }}
  .stat .num {{ font-size: 26px; font-weight: 600; }}
  .stat .label {{ font-size: 12px; color: var(--muted); margin-top: 2px; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    font-size: 13px;
  }}
  th {{
    text-align: left;
    padding: 10px 12px;
    background: #1d2129;
    color: var(--muted);
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    border-bottom: 1px solid var(--border);
  }}
  td {{
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }}
  tr:last-child td {{ border-bottom: none; }}
  .badge {{
    padding: 3px 9px;
    border-radius: 100px;
    font-size: 11px;
    font-weight: 600;
    color: white;
  }}
  footer {{
    margin-top: 24px;
    font-size: 11px;
    color: var(--muted);
  }}
</style>
</head>
<body>
  <h1>Privacy Risk Register</h1>
  <div class="subtitle">Synthetic healthcare dataset scan &middot; generated {datetime.now().strftime('%d %b %Y, %H:%M')}</div>

  <div class="summary">
    <div class="stat"><div class="num">{total_instances}</div><div class="label">PII/PHI instances found</div></div>
    <div class="stat"><div class="num">{len(register)}</div><div class="label">Data categories</div></div>
    <div class="stat"><div class="num" style="color:{LEVEL_COLORS['CRITICAL']}">{critical_count}</div><div class="label">Critical risk categories</div></div>
    <div class="stat"><div class="num" style="color:{LEVEL_COLORS['HIGH']}">{high_count}</div><div class="label">High risk categories</div></div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Data Type</th>
        <th>Instances</th>
        <th>Files Affected</th>
        <th>Sensitivity (1-5)</th>
        <th>Likelihood (1-5)</th>
        <th>Risk Score</th>
        <th>Risk Level</th>
        <th>Privacy Act 2020 IPP</th>
        <th>ISO 27799 Ref</th>
        <th>Recommended Control</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>

  <footer>
    All underlying data is synthetic (Faker-generated) for demonstration purposes only. No real patient or customer data was used.
  </footer>
</body>
</html>"""

    out_path = OUTPUT_DIR / "risk_dashboard.html"
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Dashboard written -> {out_path}")


if __name__ == "__main__":
    render()

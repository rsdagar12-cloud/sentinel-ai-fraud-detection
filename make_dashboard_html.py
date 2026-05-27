import json
from collections import Counter
from html import escape

INPUT_FILE = "Sentinel.json"
OUTPUT_FILE = "Sentinel_Dashboard.html"

with open(INPUT_FILE, "r") as f:
    data = json.load(f)

flags = data.get("individual_flags") or []
networks = data.get("suspected_networks") or []

if not flags:
    raise SystemExit("No individual_flags found in Sentinel.json")

risk_counts = Counter(str(x.get("risk_level", "Unknown")).upper() for x in flags)
store_counts = Counter(x.get("store_id", "Unknown") for x in flags)

avg_confidence = sum(float(x.get("confidence", 0) or 0) for x in flags) / len(flags)

def safe(v):
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return "" if v is None else str(v)

def risk_class(risk):
    risk = str(risk).upper()
    if "HIGH" in risk:
        return "risk-high"
    if "MEDIUM" in risk:
        return "risk-medium"
    if "LOW" in risk:
        return "risk-low"
    return ""

def inferred_network_risk(confidence):
    try:
        c = float(confidence)
    except:
        return "UNKNOWN"
    if c >= 0.80:
        return "HIGH"
    if c >= 0.60:
        return "MEDIUM"
    if c >= 0.40:
        return "LOW"
    return "LOW"

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Sentinel AI Fraud Detection Dashboard</title>
<style>
    body {{
        font-family: Arial, sans-serif;
        margin: 30px;
        background: #f5f7fa;
        color: #222;
    }}
    h1 {{
        background: #17365d;
        color: white;
        padding: 18px;
        border-radius: 8px;
    }}
    .subtitle {{
        color: #555;
        margin-bottom: 25px;
    }}
    .cards {{
        display: flex;
        gap: 16px;
        margin-bottom: 25px;
        flex-wrap: wrap;
    }}
    .card {{
        background: white;
        border-radius: 8px;
        padding: 18px;
        min-width: 180px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    .card .label {{
        font-size: 13px;
        color: #666;
    }}
    .card .value {{
        font-size: 28px;
        font-weight: bold;
        margin-top: 8px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 30px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    th {{
        background: #d9eaf7;
        padding: 10px;
        text-align: left;
        border: 1px solid #ccc;
    }}
    td {{
        padding: 9px;
        border: 1px solid #ddd;
        vertical-align: top;
    }}
    .risk-high {{
        background: #ffc7ce;
        color: #9c0006;
        font-weight: bold;
    }}
    .risk-medium {{
        background: #ffeb9c;
        color: #9c6500;
        font-weight: bold;
    }}
    .risk-low {{
        background: #c6efce;
        color: #006100;
        font-weight: bold;
    }}
    .section-title {{
        margin-top: 35px;
        color: #17365d;
    }}
    .bar-row {{
        display: flex;
        align-items: center;
        margin: 8px 0;
    }}
    .bar-label {{
        width: 140px;
        font-weight: bold;
    }}
    .bar {{
        height: 24px;
        background: #4f81bd;
        color: white;
        padding-left: 8px;
        line-height: 24px;
        border-radius: 4px;
    }}
    .note {{
        background: #fff3cd;
        padding: 14px;
        border-left: 5px solid #d39e00;
        margin-top: 25px;
    }}
</style>
</head>
<body>

<h1>Sentinel AI Fraud Detection Dashboard</h1>
<p class="subtitle">AI-assisted transaction monitoring for reseller pattern detection across store locations.</p>

<div class="cards">
    <div class="card">
        <div class="label">Total Flagged Transactions</div>
        <div class="value">{len(flags)}</div>
    </div>
    <div class="card">
        <div class="label">High Risk</div>
        <div class="value">{risk_counts.get("HIGH", 0) + risk_counts.get("MEDIUM-HIGH", 0)}</div>
    </div>
    <div class="card">
        <div class="label">Low Risk</div>
        <div class="value">{risk_counts.get("LOW", 0)}</div>
    </div>
    <div class="card">
        <div class="label">Average Confidence</div>
        <div class="value">{avg_confidence:.2f}</div>
    </div>
</div>

<h2 class="section-title">Risk Level Summary</h2>
"""

max_risk_count = max(risk_counts.values()) if risk_counts else 1
for risk, count in risk_counts.items():
    width = int((count / max_risk_count) * 400)
    html += f"""
    <div class="bar-row">
        <div class="bar-label">{escape(risk)}</div>
        <div class="bar" style="width:{width}px;">{count}</div>
    </div>
    """

html += """
<h2 class="section-title">Flagged Transactions</h2>
<table>
<tr>
    <th>Txn ID</th>
    <th>Store</th>
    <th>Products</th>
    <th>Quantity</th>
    <th>Confidence</th>
    <th>Risk Level</th>
    <th>Reason</th>
    <th>Recommended Action</th>
</tr>
"""

for row in flags:
    risk = row.get("risk_level", "")
    html += f"""
<tr>
    <td>{escape(safe(row.get("txn_id")))}</td>
    <td>{escape(safe(row.get("store_id")))}</td>
    <td>{escape(safe(row.get("products")))}</td>
    <td>{escape(safe(row.get("quantity")))}</td>
    <td>{escape(safe(row.get("confidence")))}</td>
    <td class="{risk_class(risk)}">{escape(safe(risk))}</td>
    <td>{escape(safe(row.get("reason")))}</td>
    <td>{escape(safe(row.get("recommended_action")))}</td>
</tr>
"""

html += """
</table>

<h2 class="section-title">Flagged Transactions by Store</h2>
"""

max_store_count = max(store_counts.values()) if store_counts else 1
for store, count in store_counts.items():
    width = int((count / max_store_count) * 400)
    html += f"""
    <div class="bar-row">
        <div class="bar-label">{escape(store)}</div>
        <div class="bar" style="width:{width}px;">{count}</div>
    </div>
    """

if networks:
    html += """
    <h2 class="section-title">Suspected Networks</h2>
    <table>
    <tr>
        <th>Network ID</th>
        <th>Network Name</th>
        <th>Transactions</th>
        <th>Gift Cards</th>
        <th>Stores</th>
        <th>Products</th>
        <th>Timeframe</th>
        <th>Confidence</th>
        <th>Risk Level</th>
        <th>Estimated Loss</th>
        <th>Indicators</th>
        <th>Recommended Action</th>
    </tr>
    """

    for n in networks:
        confidence = n.get("confidence", "")
        risk = n.get("risk_level") or inferred_network_risk(confidence)

        html += f"""
        <tr>
            <td>{escape(safe(n.get("network_id")))}</td>
            <td>{escape(safe(n.get("network_name")))}</td>
            <td>{escape(safe(n.get("transactions")))}</td>
            <td>{escape(safe(n.get("gift_cards")))}</td>
            <td>{escape(safe(n.get("stores")))}</td>
            <td>{escape(safe(n.get("primary_products")))}</td>
            <td>{escape(safe(n.get("timeframe")))}</td>
            <td>{escape(safe(confidence))}</td>
            <td class="{risk_class(risk)}">{escape(safe(risk))}</td>
            <td>{escape(safe(n.get("estimated_loss")))}</td>
            <td>{escape(safe(n.get("indicators")))}</td>
            <td>{escape(safe(n.get("recommended_action")))}</td>
        </tr>
        """
    html += "</table>"

html += f"""
<div class="note">
<strong>Responsible AI Note:</strong><br>
{escape(safe(data.get("responsible_ai_notes", "This prototype flags behavioral risk indicators only. Outputs require human review before operational action.")))}
</div>

</body>
</html>
"""

with open(OUTPUT_FILE, "w") as f:
    f.write(html)

print(f"Created {OUTPUT_FILE}")

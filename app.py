import json
from datetime import datetime
from io import StringIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Sentinel | Retail Leakage Control Tower",
    page_icon="🛡️",
    layout="wide"
)


# -----------------------------
# CSS
# -----------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.block-container {
    padding-top: 1.6rem;
    padding-bottom: 3rem;
    max-width: 1280px;
}

h1 {
    font-size: 3.1rem !important;
    font-weight: 900 !important;
    letter-spacing: -1.8px;
}

h2 {
    font-size: 1.65rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.6px;
    margin-top: 1.7rem;
}

h3 {
    font-size: 1.1rem !important;
    font-weight: 750 !important;
}

.hero {
    background: radial-gradient(circle at top left, #1e40af 0, #0f172a 42%, #020617 100%);
    border: 1px solid #1e293b;
    border-radius: 26px;
    padding: 34px 36px;
    margin-bottom: 24px;
    box-shadow: 0 18px 45px rgba(0,0,0,0.35);
}

.hero-kicker {
    color: #93c5fd;
    font-size: 0.86rem;
    font-weight: 800;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    margin-bottom: 10px;
}

.hero-title {
    color: #f8fafc;
    font-size: 3.5rem;
    line-height: 0.98;
    font-weight: 950;
    letter-spacing: -2.2px;
    margin-bottom: 16px;
}

.hero-sub {
    color: #cbd5e1;
    font-size: 1.05rem;
    max-width: 760px;
    line-height: 1.5;
}

.kpi {
    background: #0f172a;
    border: 1px solid #263449;
    border-radius: 22px;
    padding: 22px 22px;
    min-height: 136px;
    box-shadow: 0 10px 26px rgba(0,0,0,0.24);
}

.kpi-red { border-top: 5px solid #ef4444; }
.kpi-orange { border-top: 5px solid #f59e0b; }
.kpi-blue { border-top: 5px solid #38bdf8; }
.kpi-green { border-top: 5px solid #22c55e; }

.kpi-label {
    color: #94a3b8;
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.kpi-value {
    color: #f8fafc;
    font-size: 2.15rem;
    font-weight: 900;
    margin-top: 8px;
}

.kpi-caption {
    color: #cbd5e1;
    font-size: 0.88rem;
    margin-top: 5px;
    line-height: 1.35;
}

.panel {
    background: #0f172a;
    border: 1px solid #263449;
    border-radius: 22px;
    padding: 24px;
    margin-bottom: 18px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.18);
}

.panel-soft {
    background: linear-gradient(135deg, rgba(15,23,42,0.96), rgba(30,41,59,0.9));
    border: 1px solid #334155;
    border-radius: 22px;
    padding: 24px;
    margin-bottom: 18px;
}

.big-number {
    font-size: 2.5rem;
    font-weight: 950;
    color: #f8fafc;
}

.muted {
    color: #94a3b8;
    font-size: 0.92rem;
}

.card-title {
    font-size: 1.05rem;
    font-weight: 850;
    color: #f8fafc;
    margin-bottom: 6px;
}

.card-text {
    color: #cbd5e1;
    font-size: 0.93rem;
    line-height: 1.4;
}

.flow-card {
    background: #0b1220;
    border: 1px solid #243044;
    border-radius: 20px;
    padding: 20px;
    min-height: 148px;
    text-align: center;
}

.flow-icon {
    font-size: 2.25rem;
    margin-bottom: 8px;
}

.flow-title {
    color: #f8fafc;
    font-weight: 850;
    font-size: 1rem;
}

.flow-text {
    color: #94a3b8;
    font-size: 0.82rem;
    margin-top: 6px;
}

.arrow {
    color: #38bdf8;
    font-size: 2rem;
    text-align: center;
    margin-top: 48px;
}

.action-now {
    background: linear-gradient(135deg, #7f1d1d, #450a0a);
    border: 1px solid #ef4444;
    border-radius: 22px;
    padding: 24px;
    color: white;
}

.action-good {
    background: linear-gradient(135deg, #064e3b, #052e2b);
    border: 1px solid #10b981;
    border-radius: 22px;
    padding: 24px;
    color: white;
}

.badge {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;
    font-weight: 850;
    font-size: 0.76rem;
}

.badge-red { background: #7f1d1d; color: #fecaca; }
.badge-orange { background: #78350f; color: #fde68a; }
.badge-green { background: #064e3b; color: #a7f3d0; }
.badge-blue { background: #1e3a8a; color: #bfdbfe; }

.stButton > button {
    border-radius: 12px;
    font-weight: 800;
    padding: 0.65rem 1rem;
}

[data-testid="stSidebar"] {
    background: #020617;
}

[data-testid="stSidebar"] * {
    font-family: 'Inter', sans-serif;
}

.small-table {
    font-size: 0.86rem;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Core logic
# -----------------------------

def money(value):
    try:
        return f"${int(value):,}"
    except Exception:
        return "$0"


def normalize_columns(df):
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def estimate_unit_value(product):
    p = str(product).lower()
    if "iphone" in p or "phone" in p:
        return 950
    if "ps5" in p or "console" in p:
        return 650
    if "airpods" in p:
        return 250
    if "pokemon" in p or "etb" in p:
        return 120
    if "ipad" in p or "tablet" in p:
        return 700
    return 150


def build_sample_data():
    return pd.DataFrame([
        {
            "txn_id": "T101",
            "store_id": "Union Station",
            "products": "PS5 Console",
            "quantity": 1,
            "payment_method": "GiftCard-A93",
            "cashier_note": "Customer paid with stack of gift cards and asked if more were available in back"
        },
        {
            "txn_id": "T102",
            "store_id": "Eaton Centre",
            "products": "PS5 Console",
            "quantity": 1,
            "payment_method": "GiftCard-A93",
            "cashier_note": "Same buyer pattern noted from previous day and declined receipt"
        },
        {
            "txn_id": "T103",
            "store_id": "Yorkdale",
            "products": "Pokemon ETB",
            "quantity": 2,
            "payment_method": "GiftCard-B14",
            "cashier_note": "Customer asked about restock schedule and carried empty duffel bag"
        },
        {
            "txn_id": "T104",
            "store_id": "Union Station",
            "products": "AirPods Pro",
            "quantity": 1,
            "payment_method": "Visa-4421",
            "cashier_note": "Normal family purchase nothing unusual"
        },
        {
            "txn_id": "T105",
            "store_id": "Scarborough",
            "products": "Pokemon ETB",
            "quantity": 3,
            "payment_method": "GiftCard-B14",
            "cashier_note": "Asked for sealed boxes and stock at other stores"
        },
        {
            "txn_id": "T106",
            "store_id": "Union Station",
            "products": "iPhone 15",
            "quantity": 1,
            "payment_method": "Visa-8842",
            "cashier_note": "Customer asked about activation options and accessories"
        },
        {
            "txn_id": "T107",
            "store_id": "Yorkdale",
            "products": "PS5 Console",
            "quantity": 1,
            "payment_method": "GiftCard-A93",
            "cashier_note": "Asked about stock at other stores and left quickly"
        },
        {
            "txn_id": "T108",
            "store_id": "Eaton Centre",
            "products": "Pokemon ETB",
            "quantity": 2,
            "payment_method": "GiftCard-B14",
            "cashier_note": "Asked for sealed boxes and declined receipt"
        }
    ])


def analyze_transactions(df):
    df = normalize_columns(df)

    required = ["txn_id", "store_id", "products", "quantity", "payment_method", "cashier_note"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        return {
            "error": f"Missing required columns: {', '.join(missing)}",
            "required_columns": required
        }

    rows = []

    for _, row in df.iterrows():
        txn_id = str(row["txn_id"])
        store = str(row["store_id"])
        product = str(row["products"])
        payment = str(row["payment_method"])
        note = str(row["cashier_note"])

        try:
            qty = int(row["quantity"])
        except Exception:
            qty = 1

        p = product.lower()
        pay = payment.lower()
        n = note.lower()

        score = 0
        signals = []

        if any(x in p for x in ["ps5", "console", "pokemon", "etb", "iphone", "airpods", "ipad"]):
            score += 25
            signals.append("hot product")

        if "giftcard" in pay or "gift card" in pay:
            score += 25
            signals.append("gift card signal")

        if qty >= 2:
            score += 15
            signals.append("multi-unit buy")

        behavior_terms = [
            "stack", "declined receipt", "restock", "stock", "same buyer",
            "previous day", "empty duffel", "sealed", "other stores", "more available"
        ]

        hits = [x for x in behavior_terms if x in n]
        if hits:
            score += min(35, 10 * len(hits))
            signals.append("cashier note signal")

        confidence = min(score / 100, 0.95)

        if confidence >= 0.75:
            risk = "HIGH"
        elif confidence >= 0.45:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        value = estimate_unit_value(product) * qty

        rows.append({
            "txn_id": txn_id,
            "store": store,
            "product": product,
            "quantity": qty,
            "payment_signal": payment,
            "risk": risk,
            "confidence": round(confidence, 2),
            "inventory_value": value,
            "signals": " · ".join(signals) if signals else "normal pattern",
            "manager_move": (
                "Review before next restock"
                if risk == "HIGH"
                else "Monitor"
                if risk == "MEDIUM"
                else "No action"
            )
        })

    result_df = pd.DataFrame(rows)
    risky = result_df[result_df["risk"].isin(["HIGH", "MEDIUM"])]
    high = result_df[result_df["risk"] == "HIGH"]
    medium = result_df[result_df["risk"] == "MEDIUM"]
    low = result_df[result_df["risk"] == "LOW"]

    networks = []
    gift = risky[risky["payment_signal"].str.contains("GiftCard|gift card", case=False, na=False)]

    network_id = 1
    for payment, group in gift.groupby("payment_signal"):
        if group["txn_id"].nunique() >= 2 or group["store"].nunique() >= 2:
            networks.append({
                "network": f"N-{network_id}",
                "signal": payment,
                "stores": sorted(group["store"].unique().tolist()),
                "transactions": sorted(group["txn_id"].unique().tolist()),
                "products": sorted(group["product"].unique().tolist()),
                "exposure": int(group["inventory_value"].sum()),
                "confidence": round(float(group["confidence"].mean()), 2)
            })
            network_id += 1

    inventory_at_risk = int(risky["inventory_value"].sum()) if not risky.empty else 0
    protected_inventory = int(inventory_at_risk * 0.35)
    customer_visits_protected = max(1, int(len(risky) * 0.45)) if not risky.empty else 0
    attach_revenue = customer_visits_protected * 175
    review_minutes_saved = len(result_df) * 8

    store_df = pd.DataFrame()
    if not risky.empty:
        store_df = (
            risky.groupby("store")
            .agg(
                flagged=("txn_id", "count"),
                exposure=("inventory_value", "sum"),
                avg_confidence=("confidence", "mean")
            )
            .reset_index()
            .sort_values("exposure", ascending=False)
        )
        store_df["avg_confidence"] = store_df["avg_confidence"].round(2)

    product_df = pd.DataFrame()
    if not risky.empty:
        product_df = (
            risky.groupby("product")
            .agg(
                flagged=("txn_id", "count"),
                exposure=("inventory_value", "sum")
            )
            .reset_index()
            .sort_values("exposure", ascending=False)
        )

    return {
        "summary": {
            "transactions": len(result_df),
            "high": len(high),
            "medium": len(medium),
            "low": len(low),
            "stores_hit": risky["store"].nunique() if not risky.empty else 0,
            "networks": len(networks),
            "inventory_at_risk": inventory_at_risk,
            "protected_inventory": protected_inventory,
            "attach_revenue": attach_revenue,
            "customer_visits": customer_visits_protected,
            "review_minutes_saved": review_minutes_saved,
            "avg_confidence": round(float(result_df["confidence"].mean()), 2)
        },
        "transactions": result_df.to_dict("records"),
        "stores": store_df.to_dict("records") if not store_df.empty else [],
        "products": product_df.to_dict("records") if not product_df.empty else [],
        "networks": networks,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }


def ensure_demo_loaded():
    if "report" not in st.session_state:
        df = build_sample_data()
        st.session_state["demo_df"] = df
        st.session_state["report"] = analyze_transactions(df)


def kpi(label, value, caption, color):
    st.markdown(
        f"""
        <div class="kpi kpi-{color}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def risk_badge(risk):
    if risk == "HIGH":
        return "🔴 HIGH"
    if risk == "MEDIUM":
        return "🟠 MEDIUM"
    return "🟢 LOW"


def csv_download(report):
    df = pd.DataFrame(report["transactions"])
    output = StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()


def make_bar_chart(df, x, y, title, color="#38bdf8"):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df[x],
        y=df[y],
        marker=dict(color=color, line=dict(width=0)),
        text=df[y],
        textposition="outside"
    ))
    fig.update_layout(
        title=title,
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
        margin=dict(l=20, r=20, t=55, b=35),
        xaxis=dict(gridcolor="#1f2937"),
        yaxis=dict(gridcolor="#1f2937")
    )
    return fig


def make_funnel_chart(report):
    s = report["summary"]
    values = [
        max(s["inventory_at_risk"], 1),
        max(s["protected_inventory"], 1),
        max(s["attach_revenue"], 1),
        max(s["customer_visits"] * 500, 1)
    ]
    labels = [
        "Inventory exposure",
        "Inventory protected",
        "Attach revenue protected",
        "Customer value protected"
    ]

    fig = go.Figure(go.Funnel(
        y=labels,
        x=values,
        textinfo="value+percent initial",
        marker=dict(color=["#ef4444", "#f59e0b", "#38bdf8", "#22c55e"])
    ))

    fig.update_layout(
        height=390,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
        margin=dict(l=20, r=20, t=35, b=20)
    )
    return fig


def make_network_visual(report):
    networks = report["networks"]
    if not networks:
        st.info("No linked store network found in this run.")
        return

    for n in networks:
        stores = n["stores"]
        signal = n["signal"]
        exposure = money(n["exposure"])

        st.markdown(
            f"""
            <div class="panel-soft">
                <div class="card-title">💳 {signal} connects {len(stores)} stores</div>
                <div class="muted">Exposure detected: <b>{exposure}</b> · Confidence: <b>{n['confidence']}</b></div>
                <br>
                <div style="font-size:1.15rem; color:#f8fafc; font-weight:800;">
                    {"  →  ".join(stores)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# -----------------------------
# Pages
# -----------------------------

def page_command_center():
    ensure_demo_loaded()
    report = st.session_state["report"]
    s = report["summary"]

    st.markdown("""
    <div class="hero">
        <div class="hero-kicker">Retail Leakage Control Tower</div>
        <div class="hero-title">Resellers adapt.<br>Sentinel catches the shift.</div>
        <div class="hero-sub">
            Online bot defenses protect checkout. Sentinel focuses on the next battlefield:
            human-proxy buying patterns across physical stores.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Inventory exposure", money(s["inventory_at_risk"]), "Value tied to high/medium risk signals", "red")
    with c2:
        kpi("Stores impacted", s["stores_hit"], "Locations needing manager attention", "orange")
    with c3:
        kpi("Linked signals", s["networks"], "Repeated payment patterns across stores", "blue")
    with c4:
        kpi("Revenue protected", money(s["attach_revenue"]), "Estimated attach opportunity preserved", "green")

    st.markdown("## What is happening")

    a, b = st.columns([1.05, 0.95])

    with a:
        if s["high"] > 0:
            st.markdown(
                f"""
                <div class="action-now">
                    <div style="font-size:0.85rem; font-weight:900; letter-spacing:1.5px;">TODAY'S MOVE</div>
                    <div style="font-size:1.8rem; font-weight:950; margin-top:8px;">
                        Review {s["high"]} high-risk transaction(s) before the next restock.
                    </div>
                    <div style="margin-top:10px; color:#fecaca;">
                        Pattern detected: hot products + repeated payment signals + store movement.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div class="action-good">
                    <div style="font-size:0.85rem; font-weight:900; letter-spacing:1.5px;">TODAY'S MOVE</div>
                    <div style="font-size:1.8rem; font-weight:950; margin-top:8px;">
                        No urgent high-risk pattern detected.
                    </div>
                    <div style="margin-top:10px; color:#bbf7d0;">
                        Continue monitoring after launch periods and restocks.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with b:
        st.plotly_chart(make_funnel_chart(report), use_container_width=True)

    st.markdown("## The cat-and-mouse problem")

    f1, ar1, f2, ar2, f3, ar3, f4 = st.columns([2, .35, 2, .35, 2, .35, 2])

    with f1:
        st.markdown("""
        <div class="flow-card">
            <div class="flow-icon">🤖</div>
            <div class="flow-title">Bots get blocked</div>
            <div class="flow-text">Retailers invest in online queues, fraud rules, and purchase limits.</div>
        </div>
        """, unsafe_allow_html=True)
    with ar1:
        st.markdown('<div class="arrow">→</div>', unsafe_allow_html=True)
    with f2:
        st.markdown("""
        <div class="flow-card">
            <div class="flow-icon">🧍</div>
            <div class="flow-title">Human proxies move in-store</div>
            <div class="flow-text">Resellers use buyers, gift cards, scripts, and store-hopping.</div>
        </div>
        """, unsafe_allow_html=True)
    with ar2:
        st.markdown('<div class="arrow">→</div>', unsafe_allow_html=True)
    with f3:
        st.markdown("""
        <div class="flow-card">
            <div class="flow-icon">📦</div>
            <div class="flow-title">Inventory leaks</div>
            <div class="flow-text">Scarce products disappear before genuine customers get access.</div>
        </div>
        """, unsafe_allow_html=True)
    with ar3:
        st.markdown('<div class="arrow">→</div>', unsafe_allow_html=True)
    with f4:
        st.markdown("""
        <div class="flow-card">
            <div class="flow-icon">🛡️</div>
            <div class="flow-title">Sentinel connects signals</div>
            <div class="flow-text">Managers see the pattern early and act before the next restock.</div>
        </div>
        """, unsafe_allow_html=True)


def page_run_review():
    st.title("Run Review")
    st.caption("Upload a transaction CSV or use the demo scenario.")

    c1, c2 = st.columns([1, 1])

    with c1:
        uploaded = st.file_uploader("Upload CSV", type=["csv"])

        if uploaded:
            df = pd.read_csv(uploaded)
            st.session_state["uploaded_df"] = df
            st.dataframe(df, use_container_width=True, hide_index=True)

            if st.button("Analyze uploaded transactions", type="primary"):
                st.session_state["report"] = analyze_transactions(df)
                st.success("Analysis complete. Open Command Center or Store Network.")

    with c2:
        st.markdown("""
        <div class="panel">
            <div class="card-title">Demo scenario</div>
            <div class="card-text">
                Simulates a Best Buy Express-style high-demand product environment:
                PS5, Pokémon ETB, iPhone, gift-card signals, and cross-store activity.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Load demo scenario", type="primary"):
            df = build_sample_data()
            st.session_state["demo_df"] = df
            st.session_state["report"] = analyze_transactions(df)
            st.success("Demo loaded.")

    with st.expander("Required CSV format"):
        st.code("txn_id, store_id, products, quantity, payment_method, cashier_note")


def page_store_network():
    ensure_demo_loaded()
    report = st.session_state["report"]

    st.title("Store Network")
    st.caption("Shows where individual transactions become a connected pattern.")

    stores = pd.DataFrame(report["stores"])
    products = pd.DataFrame(report["products"])

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Store exposure")
        if not stores.empty:
            st.plotly_chart(make_bar_chart(stores, "store", "exposure", "Inventory exposure by store", "#f97316"), use_container_width=True)
        else:
            st.info("No store exposure detected.")

    with c2:
        st.markdown("### Product exposure")
        if not products.empty:
            st.plotly_chart(make_bar_chart(products, "product", "exposure", "Exposure by product", "#38bdf8"), use_container_width=True)
        else:
            st.info("No product exposure detected.")

    st.markdown("## Linked signals")
    make_network_visual(report)

    st.markdown("## Transaction queue")
    tx = pd.DataFrame(report["transactions"])
    if not tx.empty:
        tx["risk"] = tx["risk"].apply(risk_badge)
        tx["inventory_value"] = tx["inventory_value"].apply(money)
        st.dataframe(
            tx[["txn_id", "store", "product", "quantity", "payment_signal", "risk", "inventory_value", "signals", "manager_move"]],
            use_container_width=True,
            hide_index=True
        )


def page_action_plan():
    ensure_demo_loaded()
    report = st.session_state["report"]
    s = report["summary"]

    st.title("Action Plan")
    st.caption("A daily operating checklist for store leaders.")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="panel-soft">
            <span class="badge badge-red">NOW</span>
            <div class="card-title" style="margin-top:12px;">Review high-risk transactions</div>
            <div class="card-text">{s["high"]} urgent transaction(s). Prioritize scarce products and repeated payment signals.</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="panel-soft">
            <span class="badge badge-orange">TODAY</span>
            <div class="card-title" style="margin-top:12px;">Alert impacted stores</div>
            <div class="card-text">{s["stores_hit"]} store(s) show risk concentration. Share the signal before the next rush.</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="panel-soft">
            <span class="badge badge-green">NEXT RESTOCK</span>
            <div class="card-title" style="margin-top:12px;">Protect genuine customers</div>
            <div class="card-text">Use fair quantity limits and neutral cashier notes for high-demand launches.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("## Role-based moves")

    role_df = pd.DataFrame([
        {
            "Role": "Store associate",
            "What to do": "Capture neutral notes: restock questions, repeated payment, quantity, and product type.",
            "Why it matters": "Good notes create better review signals."
        },
        {
            "Role": "Store manager",
            "What to do": "Check high-risk queue after rush periods and before restocks.",
            "Why it matters": "Stops leakage before inventory disappears again."
        },
        {
            "Role": "Loss prevention",
            "What to do": "Review linked payment signals across stores.",
            "Why it matters": "Finds patterns a single store cannot see."
        },
        {
            "Role": "District manager",
            "What to do": "Compare store exposure and coach teams on consistent policy use.",
            "Why it matters": "Improves fairness and reduces manual escalation."
        }
    ])

    st.dataframe(role_df, use_container_width=True, hide_index=True)

    st.markdown("## Downloads")

    c4, c5 = st.columns(2)
    with c4:
        st.download_button(
            "Download JSON report",
            json.dumps(report, indent=2),
            "sentinel_report.json",
            "application/json"
        )
    with c5:
        st.download_button(
            "Download CSV queue",
            csv_download(report),
            "sentinel_transaction_queue.csv",
            "text/csv"
        )


def page_help():
    st.title("Help")
    st.caption("For daily users who need quick guidance.")

    st.markdown("## How to use Sentinel in 30 seconds")

    h1, h2, h3, h4 = st.columns(4)

    with h1:
        st.markdown('<div class="flow-card"><div class="flow-icon">⬆️</div><div class="flow-title">1. Upload</div><div class="flow-text">Add transaction CSV.</div></div>', unsafe_allow_html=True)
    with h2:
        st.markdown('<div class="flow-card"><div class="flow-icon">⚡</div><div class="flow-title">2. Analyze</div><div class="flow-text">Run review.</div></div>', unsafe_allow_html=True)
    with h3:
        st.markdown('<div class="flow-card"><div class="flow-icon">📍</div><div class="flow-title">3. Locate</div><div class="flow-text">See stores and linked signals.</div></div>', unsafe_allow_html=True)
    with h4:
        st.markdown('<div class="flow-card"><div class="flow-icon">✅</div><div class="flow-title">4. Act</div><div class="flow-text">Use the action plan.</div></div>', unsafe_allow_html=True)

    st.markdown("## Guardrail")
    st.warning("Sentinel does not prove fraud. It creates a manager review queue based on transaction patterns only.")


# -----------------------------
# Sidebar
# -----------------------------

st.sidebar.markdown("## 🛡️ Sentinel")
st.sidebar.caption("Retail Leakage Control Tower")

page = st.sidebar.radio(
    "Navigation",
    [
        "Command Center",
        "Run Review",
        "Store Network",
        "Action Plan",
        "Help"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Daily flow")
st.sidebar.write("Upload → Analyze → Review → Act")

if page == "Command Center":
    page_command_center()
elif page == "Run Review":
    page_run_review()
elif page == "Store Network":
    page_store_network()
elif page == "Action Plan":
    page_action_plan()
elif page == "Help":
    page_help()

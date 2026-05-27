import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title='Sentinel | Retail Leakage Control Tower', layout='wide', page_icon='🛡️')

# ---------- Styling ----------
CUSTOM_CSS = """
<style>
    .stApp {
        background:
            radial-gradient(circle at 10% 10%, rgba(30,64,175,0.18), transparent 32%),
            radial-gradient(circle at 90% 20%, rgba(16,185,129,0.08), transparent 26%),
            linear-gradient(180deg, #020617 0%, #081224 55%, #020617 100%);
        color: #e5eefb;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #07111f 0%, #08111d 100%);
        border-right: 1px solid rgba(148,163,184,0.12);
    }
    h1, h2, h3, h4 { color: #f8fafc !important; }
    .hero {
        background: linear-gradient(135deg, rgba(30,64,175,0.95), rgba(15,23,42,0.98));
        border: 1px solid rgba(96,165,250,0.18);
        border-radius: 26px;
        padding: 26px 30px;
        box-shadow: 0 20px 48px rgba(2,6,23,0.45);
        margin-bottom: 18px;
    }
    .hero-tag {
        display: inline-block;
        color: #bfdbfe;
        font-size: 0.78rem;
        letter-spacing: 1.4px;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .hero-title {
        font-size: 3rem;
        line-height: 0.98;
        font-weight: 950;
        letter-spacing: -1.8px;
        color: #ffffff;
        margin-bottom: 12px;
    }
    .hero-sub {
        color: #dbeafe;
        font-size: 1rem;
        line-height: 1.45;
        max-width: 900px;
    }
    .kpi-card {
        background: rgba(11,18,32,0.95);
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 22px;
        padding: 18px 18px;
        min-height: 120px;
        box-shadow: 0 14px 26px rgba(0,0,0,0.22);
    }
    .kpi-label {
        color: #a5b4fc;
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .kpi-value {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 950;
        margin-top: 6px;
        line-height: 1.0;
    }
    .kpi-note {
        color: #cbd5e1;
        font-size: 0.92rem;
        margin-top: 6px;
        line-height: 1.25;
    }
    .quick-bar {
        background: linear-gradient(90deg, rgba(14,165,233,0.14), rgba(34,197,94,0.14));
        border: 1px solid rgba(56,189,248,0.25);
        border-radius: 16px;
        padding: 14px 16px;
        color: #e0f2fe;
        font-size: 0.98rem;
        font-weight: 700;
        margin: 14px 0 10px 0;
    }
    .panel {
        background: rgba(8,15,28,0.92);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 12px 24px rgba(0,0,0,0.18);
        margin-bottom: 16px;
    }
    .panel-title {
        color: #f8fafc;
        font-size: 1.15rem;
        font-weight: 850;
        margin-bottom: 12px;
    }
    .mini-card {
        background: rgba(10,17,32,0.95);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 18px;
        padding: 16px;
        height: 100%;
    }
    .mini-title {
        color: #ffffff;
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .mini-copy {
        color: #cbd5e1;
        font-size: 0.93rem;
        line-height: 1.4;
    }
    .flow-card {
        background: rgba(9,16,30,0.95);
        border: 1px solid rgba(96,165,250,0.12);
        border-radius: 18px;
        padding: 16px;
        text-align: left;
        min-height: 130px;
    }
    .flow-number {
        color: #93c5fd;
        font-size: 1.7rem;
        font-weight: 900;
        margin-bottom: 6px;
    }
    .flow-title {
        color: #ffffff;
        font-size: 1rem;
        font-weight: 850;
        margin-bottom: 6px;
    }
    .flow-copy {
        color: #cbd5e1;
        font-size: 0.9rem;
        line-height: 1.35;
    }
    .value-line {
        display:flex;
        justify-content:space-between;
        align-items:center;
        gap:12px;
        background: rgba(10,17,30,0.96);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 14px;
        padding: 13px 14px;
        margin-bottom: 10px;
    }
    .value-label {
        color:#cbd5e1;
        font-weight:700;
        font-size:0.95rem;
    }
    .value-num {
        color:#ffffff;
        font-weight:950;
        font-size:1.1rem;
        text-align:right;
    }
    .story-box {
        background: linear-gradient(135deg, rgba(251,191,36,0.12), rgba(59,130,246,0.10));
        border: 1px solid rgba(251,191,36,0.28);
        border-radius: 18px;
        padding: 16px;
    }
    .story-title {
        color: #fde68a;
        font-weight: 850;
        margin-bottom: 8px;
        font-size: 0.98rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(8,15,28,0.8);
        border: 1px solid rgba(148,163,184,0.12);
        border-radius: 16px;
        padding: 8px 12px;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------- Helpers ----------
def money(x):
    return f"${x:,.0f}"

def first_existing(cols, options):
    lowered = {c.lower(): c for c in cols}
    for opt in options:
        if opt.lower() in lowered:
            return lowered[opt.lower()]
    return None

def create_demo_data():
    data = [
        ["T001", "2026-05-20 10:04", "Union Station", "Xbox Series X", 2, 649, "CARD_8841", "C201"],
        ["T002", "2026-05-20 13:10", "Eaton Centre", "Xbox Series X", 3, 649, "CARD_8841", "C202"],
        ["T003", "2026-05-20 15:05", "Scarborough Town", "Xbox Series X", 2, 649, "CARD_8841", "C203"],
        ["T004", "2026-05-20 16:12", "Square One", "Xbox Series X", 1, 649, "CARD_8841", "C204"],
        ["T005", "2026-05-21 11:30", "Union Station", "AirPods Pro", 1, 329, "CARD_9211", "C205"],
        ["T006", "2026-05-21 12:40", "Eaton Centre", "iPhone 15", 2, 1129, "CARD_2230", "C206"],
        ["T007", "2026-05-21 13:15", "Union Station", "PlayStation 5", 2, 649, "CARD_6200", "C207"],
        ["T008", "2026-05-21 15:50", "Scarborough Town", "Nintendo Switch OLED", 2, 449, "CARD_6200", "C208"],
        ["T009", "2026-05-22 10:08", "Square One", "Xbox Series X", 2, 649, "CARD_8841", "C209"],
        ["T010", "2026-05-22 14:24", "Union Station", "MacBook Air", 1, 1499, "CARD_4040", "C210"],
        ["T011", "2026-05-22 17:05", "Eaton Centre", "Xbox Series X", 2, 649, "CARD_8841", "C211"],
        ["T012", "2026-05-22 18:15", "Square One", "Gift Card", 6, 100, "CARD_7711", "C212"],
        ["T013", "2026-05-23 11:45", "Scarborough Town", "Xbox Series X", 3, 649, "CARD_8841", "C213"],
        ["T014", "2026-05-23 12:55", "Union Station", "Xbox Series X", 2, 649, "CARD_8841", "C214"],
        ["T015", "2026-05-23 16:35", "Eaton Centre", "Samsung S24", 2, 1199, "CARD_5300", "C215"],
    ]
    return pd.DataFrame(data, columns=[
        "transaction_id", "timestamp", "store", "product", "quantity", "unit_price", "payment_signal", "customer_id"
    ])

def normalize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    cols = list(df.columns)

    mapping = {
        "transaction_id": first_existing(cols, ["transaction_id", "txn_id", "id", "transaction"]),
        "timestamp": first_existing(cols, ["timestamp", "date", "datetime", "time"]),
        "store": first_existing(cols, ["store", "store_id", "location", "branch"]),
        "product": first_existing(cols, ["product", "item", "sku", "category"]),
        "quantity": first_existing(cols, ["quantity", "qty", "units"]),
        "unit_price": first_existing(cols, ["unit_price", "price", "amount", "value", "ticket"]),
        "payment_signal": first_existing(cols, ["payment_signal", "payment_method", "payment", "card", "payment_id"]),
        "customer_id": first_existing(cols, ["customer_id", "customer", "client", "user_id"]),
    }

    out = pd.DataFrame()
    out["transaction_id"] = df[mapping["transaction_id"]] if mapping["transaction_id"] else [f"TX{i+1:03d}" for i in range(len(df))]
    out["timestamp"] = pd.to_datetime(df[mapping["timestamp"]], errors="coerce") if mapping["timestamp"] else pd.Timestamp.today()
    out["store"] = df[mapping["store"]].astype(str) if mapping["store"] else "Store A"
    out["product"] = df[mapping["product"]].astype(str) if mapping["product"] else "Unknown Product"
    out["quantity"] = pd.to_numeric(df[mapping["quantity"]], errors="coerce").fillna(1).clip(lower=1) if mapping["quantity"] else 1
    out["unit_price"] = pd.to_numeric(df[mapping["unit_price"]], errors="coerce").fillna(100) if mapping["unit_price"] else 100
    out["payment_signal"] = df[mapping["payment_signal"]].astype(str) if mapping["payment_signal"] else [f"SIG_{i%5}" for i in range(len(df))]
    out["customer_id"] = df[mapping["customer_id"]].astype(str) if mapping["customer_id"] else [f"C{i+1:03d}" for i in range(len(df))]
    out["total_value"] = out["quantity"] * out["unit_price"]
    out["date"] = out["timestamp"].dt.date
    return out

def analyze_transactions(raw_df: pd.DataFrame):
    df = normalize_transactions(raw_df)

    scarce_keywords = ["xbox", "playstation", "ps5", "iphone", "s24", "macbook", "switch", "airpods", "gpu", "gift card"]
    df["scarce_flag"] = df["product"].str.lower().apply(lambda x: any(k in x for k in scarce_keywords))

    signal_txn_count = df.groupby("payment_signal")["transaction_id"].transform("count")
    signal_store_count = df.groupby("payment_signal")["store"].transform("nunique")
    signal_units = df.groupby("payment_signal")["quantity"].transform("sum")
    customer_txn_count = df.groupby("customer_id")["transaction_id"].transform("count")

    score = np.zeros(len(df))
    score += np.where(df["scarce_flag"], 25, 0)
    score += np.where(df["quantity"] >= 2, 15, 0)
    score += np.where(df["total_value"] >= 1000, 10, 0)
    score += np.where(signal_txn_count >= 3, 20, 0)
    score += np.where(signal_store_count >= 2, 20, 0)
    score += np.where(signal_units >= 8, 15, 0)
    score += np.where(customer_txn_count >= 2, 10, 0)

    df["risk_score"] = score.astype(int)

    def tier(s):
        if s >= 70:
            return "High"
        if s >= 45:
            return "Medium"
        return "Low"

    df["risk_tier"] = df["risk_score"].apply(tier)

    def reason_row(r):
        reasons = []
        if r["scarce_flag"]:
            reasons.append("scarce product")
        if r["quantity"] >= 2:
            reasons.append("multi-unit purchase")
        if signal_txn_count.loc[r.name] >= 3:
            reasons.append("repeat payment signal")
        if signal_store_count.loc[r.name] >= 2:
            reasons.append("cross-store pattern")
        if signal_units.loc[r.name] >= 8:
            reasons.append("cumulative volume")
        return ", ".join(reasons) if reasons else "standard purchase"

    df["reasons"] = df.apply(reason_row, axis=1)
    flagged = df[df["risk_tier"].isin(["High", "Medium"])].copy().sort_values(["risk_score", "total_value"], ascending=False)

    store_summary = flagged.groupby("store", dropna=False).agg(
        flagged_transactions=("transaction_id", "count"),
        exposure=("total_value", "sum"),
        avg_risk=("risk_score", "mean")
    ).reset_index().sort_values("exposure", ascending=False)

    signal_summary = flagged.groupby("payment_signal", dropna=False).agg(
        transactions=("transaction_id", "count"),
        stores=("store", "nunique"),
        units=("quantity", "sum"),
        exposure=("total_value", "sum")
    ).reset_index().sort_values(["stores", "exposure"], ascending=False)

    inventory_exposure = float(flagged["total_value"].sum())
    protected_inventory = round(inventory_exposure * 0.55, 0)
    revenue_protected = round(protected_inventory * 0.125, 0)
    review_minutes_saved = int(max(len(flagged) * 4, 12))
    linked_signals = int((signal_summary["stores"] >= 2).sum()) if len(signal_summary) else 0
    stores_hit = int(flagged["store"].nunique()) if len(flagged) else 0

    summary = {
        "transactions_reviewed": int(len(df)),
        "flagged_transactions": int(len(flagged)),
        "inventory_exposure": inventory_exposure,
        "protected_inventory": protected_inventory,
        "stores_hit": stores_hit,
        "linked_signals": linked_signals,
        "revenue_protected": revenue_protected,
        "review_minutes_saved": review_minutes_saved,
        "high_risk_count": int((flagged["risk_tier"] == "High").sum()),
        "medium_risk_count": int((flagged["risk_tier"] == "Medium").sum()),
    }

    top_store = store_summary.iloc[0]["store"] if len(store_summary) else "No store"
    top_signal = signal_summary.iloc[0]["payment_signal"] if len(signal_summary) else "No linked signal"

    return {
        "raw": raw_df,
        "scored": df,
        "flagged": flagged,
        "store_summary": store_summary,
        "signal_summary": signal_summary,
        "summary": summary,
        "top_store": top_store,
        "top_signal": top_signal,
    }

def ensure_report():
    if "report" not in st.session_state:
        demo = create_demo_data()
        st.session_state.report = analyze_transactions(demo)
        st.session_state.source_label = "Executive demo dataset"

# ---------- Visual renderers ----------
def hero(title, sub, tag="Retail Leakage Control Tower"):
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-tag">{tag}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def kpi_card(label, value, note):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def panel_open(title):
    st.markdown(f'<div class="panel"><div class="panel-title">{title}</div>', unsafe_allow_html=True)

def panel_close():
    st.markdown('</div>', unsafe_allow_html=True)

def make_store_chart(store_summary):
    if store_summary.empty:
        return go.Figure()
    fig = px.bar(
        store_summary,
        x="store",
        y="exposure",
        text="flagged_transactions",
        color="avg_risk",
        color_continuous_scale="Reds",
    )
    fig.update_layout(
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5eefb"),
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,
        xaxis_title="",
        yaxis_title="Exposure ($)",
    )
    fig.update_traces(texttemplate="%{text} txn", textposition="outside")
    return fig

def make_risk_donut(summary):
    vals = [summary["high_risk_count"], summary["medium_risk_count"], max(summary["transactions_reviewed"] - summary["flagged_transactions"], 0)]
    fig = go.Figure(data=[go.Pie(
        labels=["High", "Medium", "Low / clear"],
        values=vals,
        hole=0.62,
        marker=dict(colors=["#fb7185", "#f59e0b", "#22c55e"]),
        sort=False,
        textinfo="label+value"
    )])
    fig.update_layout(
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5eefb"),
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
    )
    return fig

def render_command_center(report):
    s = report["summary"]
    hero(
        "Resellers adapt. Sentinel catches the shift.",
        "Retailers spend heavily blocking online bots. Sentinel focuses on the store-floor gap: repeated proxy buying patterns across locations, scarce products, and linked payment signals that still leak inventory.",
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Inventory exposure", money(s["inventory_exposure"]), "Current value sitting behind flagged patterns")
    with c2:
        kpi_card("Stores impacted", s["stores_hit"], "Locations where patterns need manager attention")
    with c3:
        kpi_card("Linked signals", s["linked_signals"], "Repeat payment or proxy behavior across stores")
    with c4:
        kpi_card("Revenue protected", money(s["revenue_protected"]), "Accessory / attach opportunity preserved")

    st.markdown(
        f'<div class="quick-bar">In 10 seconds: {s["flagged_transactions"]} transactions deserve review, {money(s["inventory_exposure"])} is exposed, and the most concentrated activity sits in <b>{report["top_store"]}</b>.</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.25, 1])
    with left:
        panel_open("Where the issue is concentrated")
        st.plotly_chart(make_store_chart(report["store_summary"]), use_container_width=True)
        st.caption("Labels show number of flagged transactions by store.")
        panel_close()
    with right:
        panel_open("Risk mix")
        st.plotly_chart(make_risk_donut(s), use_container_width=True)
        panel_close()

    st.markdown("## What leaders need to know")
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="mini-card"><div class="mini-title">1. The problem moved offline</div><div class="mini-copy">Bots may be blocked online, but human proxies can still split purchases across stores and keep each transaction looking ordinary.</div></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="mini-card"><div class="mini-title">2. Single transactions hide the pattern</div><div class="mini-copy">A cashier sees one sale. A district manager needs the full pattern across stores, products, and payment signals.</div></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="mini-card"><div class="mini-title">3. Better triage drives better outcomes</div><div class="mini-copy">Sentinel does not block sales. It tells managers what to inspect first so scarce inventory reaches genuine customers.</div></div>', unsafe_allow_html=True)

    st.markdown("## Daily operating flow")
    f1, f2, f3, f4 = st.columns(4)
    flow_items = [
        ("1", "Upload", "Pull the daily transaction file or use the store export."),
        ("2", "Analyze", "Sentinel scores risk and links patterns that humans miss."),
        ("3", "Review", "Managers see the exact stores, transactions, and signals to inspect."),
        ("4", "Act", "Use the action plan to protect stock and capture genuine demand."),
    ]
    for col, (n, title, copy) in zip([f1, f2, f3, f4], flow_items):
        with col:
            st.markdown(f'<div class="flow-card"><div class="flow-number">{n}</div><div class="flow-title">{title}</div><div class="flow-copy">{copy}</div></div>', unsafe_allow_html=True)

    st.markdown("## Value snapshot")
    v1, v2 = st.columns([1,1])
    with v1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        for label, value in [
            ("Protected inventory opportunity", money(s["protected_inventory"])),
            ("Attach / accessory revenue preserved", money(s["revenue_protected"])),
            ("Manager review time saved", f'{s["review_minutes_saved"]} minutes'),
            ("Transactions prioritized", s["flagged_transactions"]),
        ]:
            st.markdown(f'<div class="value-line"><div class="value-label">{label}</div><div class="value-num">{value}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with v2:
        st.markdown(
            """
            <div class="story-box">
                <div class="story-title">Field insight behind the idea</div>
                <div class="mini-copy">
                Inspired by Rahul Singh’s retail-floor experience at Best Buy Express: a recurring pattern where a buyer repeatedly purchased scarce Xbox units in small batches, while similar activity appeared across other stores. No single transaction looked outrageous. The pattern did.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="story-box">
                <div class="story-title">Why this matters operationally</div>
                <div class="mini-copy">
                When scarce products go to proxy buyers, genuine customers leave empty-handed. Sentinel helps teams redirect stock to real demand, protect service attach, and reduce reactive manual chasing.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def render_run_review(report):
    hero("Run a review", "Upload a CSV, or use the executive demo. Sentinel will score risk, flag linked patterns, and create a manager review queue.", tag="Operations Review")
    st.info(f"Current dataset: {st.session_state.get('source_label', 'Not loaded')}")

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Load executive demo", use_container_width=True):
            demo = create_demo_data()
            st.session_state.report = analyze_transactions(demo)
            st.session_state.source_label = "Executive demo dataset"
            st.success("Executive demo loaded.")
    with col2:
        uploaded = st.file_uploader("Upload transaction CSV", type=["csv"])
        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
                st.session_state.report = analyze_transactions(df)
                st.session_state.source_label = uploaded.name
                st.success(f"Loaded {uploaded.name}")
            except Exception as e:
                st.error(f"Could not read file: {e}")

    flagged = report["flagged"].copy()
    if flagged.empty:
        st.warning("No medium/high risk transactions found in the current dataset.")
        return

    view = flagged[["transaction_id", "timestamp", "store", "product", "quantity", "total_value", "risk_score", "risk_tier", "payment_signal", "reasons"]].copy()
    view["timestamp"] = view["timestamp"].astype(str)
    view["total_value"] = view["total_value"].map(money)
    st.markdown("## Priority review queue")
    st.dataframe(view, use_container_width=True, hide_index=True)

def render_store_network(report):
    hero("Store network", "See how the pattern spreads across stores and which linked signals deserve district-level review.", tag="Network View")
    store_summary = report["store_summary"]
    signal_summary = report["signal_summary"]

    a, b = st.columns([1.15, 1])
    with a:
        panel_open("Store exposure")
        st.plotly_chart(make_store_chart(store_summary), use_container_width=True)
        panel_close()
    with b:
        panel_open("Linked signals requiring review")
        if signal_summary.empty:
            st.write("No linked signals detected.")
        else:
            show = signal_summary[["payment_signal", "transactions", "stores", "units", "exposure"]].copy()
            show["exposure"] = show["exposure"].map(money)
            st.dataframe(show, use_container_width=True, hide_index=True)
        panel_close()

def render_action_plan(report):
    s = report["summary"]
    hero("Action plan", "What a store manager, district manager, and operations lead should do next.", tag="Recommended Actions")
    c1, c2, c3 = st.columns(3)
    cards = [
        ("Today", "Review high-risk queue", f"Start with the {s['high_risk_count']} high-risk transactions and verify whether stock should be held for further review before the next restock cycle."),
        ("This week", "Watch linked signals", f"Investigate repeat signals appearing across {s['stores_hit']} stores. The goal is to confirm whether the same buyer pattern is moving store to store."),
        ("This month", "Tune policy and coaching", "Use what Sentinel surfaces to refine escalation rules, coach store teams on scarce-item reviews, and protect attach from demand leakage."),
    ]
    for col, (title, head, copy) in zip([c1, c2, c3], cards):
        with col:
            st.markdown(f'<div class="mini-card"><div class="mini-title">{title} · {head}</div><div class="mini-copy">{copy}</div></div>', unsafe_allow_html=True)

    st.markdown("## How teams use Sentinel")
    x1, x2, x3 = st.columns(3)
    with x1:
        st.metric("Store manager", "5–10 min/day", "Quick review queue")
        st.caption("Checks the flagged queue before releasing scarce stock or closing the day.")
    with x2:
        st.metric("District manager", "2–3 times/week", "Cross-store view")
        st.caption("Looks for linked patterns across stores and escalates only what is materially connected.")
    with x3:
        st.metric("Operations lead", "Weekly", "Policy insight")
        st.caption("Uses trend summaries to tune processes without overwhelming frontline teams.")

def render_business_case(report):
    s = report["summary"]
    hero("Business case", "A sharp explanation of the problem, the gap in today’s controls, and the value Sentinel creates.", tag="CEO View")

    row1a, row1b, row1c = st.columns(3)
    with row1a:
        st.markdown('<div class="mini-card"><div class="mini-title">The problem</div><div class="mini-copy">Major retailers invest heavily in anti-bot technology online, yet physical stores still face leakage from human proxies splitting purchases across locations.</div></div>', unsafe_allow_html=True)
    with row1b:
        st.markdown('<div class="mini-card"><div class="mini-title">Why current tools miss it</div><div class="mini-copy">Conventional reporting treats each transaction separately. Proxy behavior becomes visible only when product, payment, timing, and store patterns are connected.</div></div>', unsafe_allow_html=True)
    with row1c:
        st.markdown('<div class="mini-card"><div class="mini-title">Sentinel’s role</div><div class="mini-copy">Sentinel sits in the middle: not blocking sales, not replacing teams, but guiding scarce inventory decisions with explainable pattern detection.</div></div>', unsafe_allow_html=True)

    st.markdown("## Value hypothesis")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    for label, value in [
        ("Inventory at risk identified", money(s["inventory_exposure"])),
        ("Value likely protected if acted on", money(s["protected_inventory"])),
        ("Attach revenue preserved", money(s["revenue_protected"])),
        ("Manual review time reduced", f"~{s['review_minutes_saved']} min per cycle"),
    ]:
        st.markdown(f'<div class="value-line"><div class="value-label">{label}</div><div class="value-num">{value}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("These are directional operational estimates designed to show business value, not audited financial results.")

def render_help():
    hero("Help & user guidance", "Make the app usable in day-to-day retail operations with zero confusion.", tag="User Support")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="mini-card"><div class="mini-title">What file should I upload?</div><div class="mini-copy">A transaction-level CSV with store, product, quantity, price, date, and a payment or customer identifier works best.</div></div>', unsafe_allow_html=True)
        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="mini-card"><div class="mini-title">When should managers use it?</div><div class="mini-copy">Best practice: once before scarce-item restock decisions, and again at end-of-day for flagged reviews.</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="mini-card"><div class="mini-title">What does Sentinel not do?</div><div class="mini-copy">It does not accuse customers or make final decisions. It prioritizes patterns so people can review them quickly and fairly.</div></div>', unsafe_allow_html=True)
        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="mini-card"><div class="mini-title">How do I explain this to leadership?</div><div class="mini-copy">Sentinel protects scarce inventory, preserves attach revenue, and helps real customers leave with the products they came for.</div></div>', unsafe_allow_html=True)

# ---------- Sidebar ----------
ensure_report()
with st.sidebar:
    st.markdown("## 🛡️ Sentinel")
    st.caption("Retail Leakage Control Tower")
    page = st.radio(
        "Navigate",
        ["Command Center", "Run Review", "Store Network", "Action Plan", "Business Case", "Help"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**Daily flow**")
    st.caption("Upload → Analyze → Review → Act")
    st.markdown("---")
    st.caption(f"Current source: {st.session_state.get('source_label', 'Executive demo dataset')}")

report = st.session_state.report

# ---------- Router ----------
if page == "Command Center":
    render_command_center(report)
elif page == "Run Review":
    render_run_review(report)
elif page == "Store Network":
    render_store_network(report)
elif page == "Action Plan":
    render_action_plan(report)
elif page == "Business Case":
    render_business_case(report)
else:
    render_help()

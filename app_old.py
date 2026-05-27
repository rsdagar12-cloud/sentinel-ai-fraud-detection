import json
from collections import Counter
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Sentinel AI Fraud Detection",
    layout="wide"
)

st.title("Sentinel AI Fraud Detection Dashboard")
st.caption("AI-assisted transaction monitoring for reseller and fraud pattern detection across store locations.")

# --------------------------------------------------
# Helper functions
# --------------------------------------------------

HIGH_DEMAND_KEYWORDS = [
    "ps5", "console", "pokemon", "etb", "airpods", "iphone", "premium electronics"
]

SUSPICIOUS_NOTE_KEYWORDS = [
    "gift card",
    "stack",
    "declined receipt",
    "more in stock",
    "other stores",
    "restock",
    "sealed boxes",
    "sku",
    "date codes",
    "duffel",
    "in and out",
    "same script"
]


def normalize_columns(df):
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    rename_map = {
        "store": "store_id",
        "items": "products",
        "qty": "quantity",
        "payment": "payment_method",
        "note": "cashier_note"
    }

    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


def score_transaction(row, payment_counts):
    score = 0
    reasons = []

    products = str(row.get("products", "")).lower()
    note = str(row.get("cashier_note", "")).lower()
    payment = str(row.get("payment_method", ""))
    quantity = int(row.get("quantity", 1) or 1)

    if any(k in products for k in HIGH_DEMAND_KEYWORDS):
        score += 20
        reasons.append("High-demand product targeted")

    if quantity >= 2:
        score += 15
        reasons.append("Multiple units purchased")

    if "giftcard" in payment.lower() or "gift card" in payment.lower():
        score += 20
        reasons.append("Gift card payment used")

    if payment_counts.get(payment, 0) > 1 and payment:
        score += 25
        reasons.append("Payment method reused across transactions")

    note_hits = [k for k in SUSPICIOUS_NOTE_KEYWORDS if k in note]
    if note_hits:
        score += min(30, len(note_hits) * 10)
        reasons.append("Suspicious cashier note signals: " + ", ".join(note_hits[:3]))

    confidence = min(score / 100, 0.95)

    if confidence >= 0.80:
        risk_level = "HIGH"
    elif confidence >= 0.60:
        risk_level = "MEDIUM"
    elif confidence >= 0.40:
        risk_level = "LOW"
    else:
        risk_level = "LOW"

    if not reasons:
        reasons.append("No major suspicious indicators detected")

    return confidence, risk_level, "; ".join(reasons)


def analyze_uploaded_csv(df):
    df = normalize_columns(df)

    required = ["txn_id", "store_id", "products", "quantity", "payment_method", "cashier_note"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(f"Missing columns: {missing}")
        st.info("Expected columns: txn_id, store_id, products, quantity, payment_method, cashier_note")
        return None

    payment_counts = Counter(df["payment_method"].astype(str))

    flags = []
    for _, row in df.iterrows():
        confidence, risk_level, reason = score_transaction(row, payment_counts)

        flags.append({
            "txn_id": row.get("txn_id"),
            "store_id": row.get("store_id"),
            "products": str(row.get("products")),
            "quantity": row.get("quantity"),
            "payment_method": row.get("payment_method"),
            "confidence": round(confidence, 2),
            "risk_level": risk_level,
            "reason": reason,
            "recommended_action": (
                "Human review recommended before action"
                if risk_level in ["HIGH", "MEDIUM"]
                else "No immediate action required"
            )
        })

    flagged_df = pd.DataFrame(flags)

    networks = []
    for payment, group in df.groupby("payment_method"):
        if payment_counts[payment] > 1 and ("gift" in str(payment).lower()):
            networks.append({
                "network_id": f"NETWORK-{len(networks)+1}",
                "payment_method": payment,
                "transactions": "; ".join(group["txn_id"].astype(str)),
                "stores": "; ".join(sorted(group["store_id"].astype(str).unique())),
                "confidence": 0.85,
                "risk_level": "HIGH",
                "recommended_action": "Review linked transactions and monitor payment reuse"
            })

    return {
        "individual_flags": flagged_df.to_dict(orient="records"),
        "suspected_networks": networks,
        "responsible_ai_notes": (
            "This prototype flags behavioral risk indicators only. "
            "It does not prove fraud or illegal activity. Human review is required before action."
        )
    }


def load_existing_json():
    try:
        with open("Sentinel.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def show_dashboard(data):
    flags = data.get("individual_flags") or []
    networks = data.get("suspected_networks") or []

    if not flags:
        st.warning("No transaction flags found.")
        return

    df = pd.DataFrame(flags)

    if "products" in df.columns:
        df["products"] = df["products"].apply(lambda x: "; ".join(x) if isinstance(x, list) else x)

    total = len(df)
    high = df["risk_level"].astype(str).str.upper().str.contains("HIGH").sum()
    low = df["risk_level"].astype(str).str.upper().str.contains("LOW").sum()
    avg_conf = pd.to_numeric(df["confidence"], errors="coerce").mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Flagged Transactions", total)
    c2.metric("High Risk", int(high))
    c3.metric("Low Risk", int(low))
    c4.metric("Average Confidence", round(avg_conf, 2))

    st.subheader("Risk Level Summary")
    risk_summary = df["risk_level"].astype(str).str.upper().value_counts().reset_index()
    risk_summary.columns = ["risk_level", "count"]
    st.bar_chart(risk_summary.set_index("risk_level"))

    st.subheader("Flagged Transactions")
    st.dataframe(df, use_container_width=True)

    st.subheader("Flagged Transactions by Store")
    if "store_id" in df.columns:
        store_summary = df["store_id"].value_counts().reset_index()
        store_summary.columns = ["store_id", "flagged_count"]
        st.bar_chart(store_summary.set_index("store_id"))

    if networks:
        st.subheader("Suspected Networks")
        net_df = pd.DataFrame(networks)
        st.dataframe(net_df, use_container_width=True)

    st.subheader("Responsible AI Note")
    st.warning(data.get(
        "responsible_ai_notes",
        "This prototype flags behavioral risk indicators only. Human review is required."
    ))

    st.download_button(
        "Download JSON Report",
        data=json.dumps(data, indent=2),
        file_name="sentinel_report.json",
        mime="application/json"
    )

    st.download_button(
        "Download CSV Report",
        data=df.to_csv(index=False),
        file_name="sentinel_report.csv",
        mime="text/csv"
    )


# --------------------------------------------------
# App layout
# --------------------------------------------------

st.sidebar.header("Workflow")
st.sidebar.write("1. Upload transaction CSV")
st.sidebar.write("2. Click Analyze")
st.sidebar.write("3. Review risk dashboard")
st.sidebar.write("4. Download report")

uploaded_file = st.file_uploader("Upload transaction CSV", type=["csv"])

if uploaded_file:
    raw_df = pd.read_csv(uploaded_file)

    st.subheader("Uploaded Transaction Data")
    st.dataframe(raw_df, use_container_width=True)

    if st.button("Analyze Transactions"):
        with st.spinner("Analyzing transaction patterns..."):
            result = analyze_uploaded_csv(raw_df)

        if result:
            st.success("Analysis complete.")
            show_dashboard(result)

else:
    st.info("Upload a CSV to analyze new transactions, or use the existing demo report below.")

    existing = load_existing_json()

    if existing:
        if st.button("Load Existing Demo Dashboard"):
            show_dashboard(existing)
    else:
        st.warning("No Sentinel.json found in this folder.")

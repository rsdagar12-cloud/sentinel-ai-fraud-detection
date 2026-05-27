import json
from datetime import datetime
from io import StringIO

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Sentinel AI Retail Risk Intelligence",
    page_icon="🛡️",
    layout="wide"
)


# -----------------------------
# Helper functions
# -----------------------------

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def safe_join(value):
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    if pd.isna(value):
        return ""
    return str(value)


def analyze_transactions(df: pd.DataFrame) -> dict:
    """
    Simple explainable risk engine.
    This does not prove fraud. It creates human-review risk indicators.
    """

    df = normalize_columns(df)

    required = ["txn_id", "store_id", "products", "quantity", "payment_method", "cashier_note"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        return {
            "error": f"Missing required columns: {', '.join(missing)}",
            "required_columns": required,
            "validation": {"passed": False, "issues": missing}
        }

    flags = []

    for _, row in df.iterrows():
        txn_id = str(row.get("txn_id", ""))
        store_id = str(row.get("store_id", ""))
        products = str(row.get("products", ""))
        payment_method = str(row.get("payment_method", ""))
        cashier_note = str(row.get("cashier_note", ""))
        quantity = int(row.get("quantity", 1)) if str(row.get("quantity", "1")).isdigit() else 1

        note_lower = cashier_note.lower()
        product_lower = products.lower()
        payment_lower = payment_method.lower()

        score = 0.0
        reasons = []
        recommended_actions = []

        # High-demand product targeting
        if any(item in product_lower for item in ["ps5", "console", "pokemon", "etb", "airpods"]):
            score += 0.20
            reasons.append("High-demand product targeted")
            recommended_actions.append("Review high-demand SKU purchase pattern")

        # Gift card risk signal
        if "giftcard" in payment_lower or "gift card" in payment_lower:
            score += 0.20
            reasons.append("Gift card payment used")
            recommended_actions.append("Check whether same payment method appears across stores")

        # Quantity/bulk signal
        if quantity >= 2:
            score += 0.15
            reasons.append("Multiple units purchased")
            recommended_actions.append("Apply fair quantity-limit review for high-demand items")

        # Cashier note behavioral signals
        behavioral_keywords = [
            "declined receipt",
            "restock",
            "stock",
            "same buyer",
            "previous day",
            "empty duffel",
            "script",
            "stack",
            "more available",
            "other stores"
        ]

        matched_keywords = [k for k in behavioral_keywords if k in note_lower]
        if matched_keywords:
            score += min(0.35, 0.08 * len(matched_keywords))
            reasons.append("Cashier note contains behavioral risk indicators: " + ", ".join(matched_keywords))
            recommended_actions.append("Review cashier notes and compare against nearby transactions")

        # Cap score
        confidence = round(min(score, 0.95), 2)

        if confidence >= 0.75:
            risk_level = "HIGH"
        elif confidence >= 0.45:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        flags.append({
            "txn_id": txn_id,
            "store_id": store_id,
            "products": products,
            "quantity": quantity,
            "payment_method": payment_method,
            "confidence": confidence,
            "risk_level": risk_level,
            "reason": "; ".join(reasons) if reasons else "No major risk indicators detected",
            "recommended_action": "; ".join(dict.fromkeys(recommended_actions)) if recommended_actions else "No immediate action required"
        })

    flags_df = pd.DataFrame(flags)

    # Network detection by shared payment method across stores
    suspected_networks = []
    risky_payment_methods = flags_df[
        (flags_df["payment_method"].str.contains("GiftCard|gift card", case=False, na=False)) &
        (flags_df["risk_level"].isin(["HIGH", "MEDIUM"]))
    ]

    if not risky_payment_methods.empty:
        grouped = risky_payment_methods.groupby("payment_method")

        network_num = 1
        for payment_method, group in grouped:
            unique_stores = sorted(group["store_id"].unique().tolist())
            linked_txns = sorted(group["txn_id"].unique().tolist())

            if len(linked_txns) >= 2 or len(unique_stores) >= 2:
                avg_confidence = round(group["confidence"].mean(), 2)
                suspected_networks.append({
                    "network_id": f"NETWORK-{network_num}",
                    "shared_signal": payment_method,
                    "linked_transactions": linked_txns,
                    "stores": unique_stores,
                    "products": sorted(group["products"].unique().tolist()),
                    "confidence": avg_confidence,
                    "risk_level": "HIGH" if avg_confidence >= 0.75 else "MEDIUM",
                    "business_rationale": (
                        f"{payment_method} appears across {len(linked_txns)} flagged transactions "
                        f"and {len(unique_stores)} store(s), suggesting a pattern worth human review."
                    ),
                    "recommended_action": (
                        "Review linked transactions, compare timestamps/cashier notes, and apply fair policy controls before any customer action."
                    )
                })
                network_num += 1

    high_risk_count = int((flags_df["risk_level"] == "HIGH").sum())
    medium_risk_count = int((flags_df["risk_level"] == "MEDIUM").sum())
    low_risk_count = int((flags_df["risk_level"] == "LOW").sum())
    stores_affected = int(flags_df["store_id"].nunique())
    avg_confidence = round(float(flags_df["confidence"].mean()), 2) if not flags_df.empty else 0

    # Simple exposure estimate for business framing
    # This is intentionally conservative/demo-based.
    estimated_exposure = 0
    for _, row in flags_df.iterrows():
        product = str(row["products"]).lower()
        qty = int(row["quantity"])
        if row["risk_level"] in ["HIGH", "MEDIUM"]:
            if "ps5" in product or "console" in product:
                estimated_exposure += 650 * qty
            elif "pokemon" in product or "etb" in product:
                estimated_exposure += 120 * qty
            elif "airpods" in product:
                estimated_exposure += 250 * qty
            else:
                estimated_exposure += 100 * qty

    action_queue = []

    if high_risk_count > 0:
        action_queue.append(
            f"Prioritize human review of {high_risk_count} high-risk transaction(s) before next high-demand SKU restock."
        )

    if suspected_networks:
        action_queue.append(
            f"Investigate {len(suspected_networks)} linked payment-method network(s) across store locations."
        )

    top_store = flags_df[flags_df["risk_level"].isin(["HIGH", "MEDIUM"])]["store_id"].value_counts()
    if not top_store.empty:
        action_queue.append(
            f"Focus first on store {top_store.index[0]}, which has the highest concentration of flagged activity."
        )

    action_queue.append(
        "Use this output as a review queue only. Do not treat risk indicators as proof of fraud."
    )

    report = {
        "executive_summary": {
            "total_transactions_reviewed": int(len(df)),
            "total_flagged_transactions": int(len(flags_df)),
            "high_risk_transactions": high_risk_count,
            "medium_risk_transactions": medium_risk_count,
            "low_risk_transactions": low_risk_count,
            "stores_affected": stores_affected,
            "suspected_networks": int(len(suspected_networks)),
            "average_confidence": avg_confidence,
            "estimated_inventory_exposure": estimated_exposure,
            "recommended_focus": action_queue[0] if action_queue else "No immediate action required"
        },
        "individual_flags": flags,
        "suspected_networks": suspected_networks,
        "recommended_action_queue": action_queue,
        "responsible_ai_note": (
            "This prototype flags behavioral risk indicators only. It does not prove fraud or illegal activity. "
            "All outputs require human review before action. Store policies should be applied consistently to all customers."
        ),
        "report_generated_at": datetime.utcnow().isoformat() + "Z",
        "validation": {
            "passed": True,
            "issues": []
        }
    }

    return report


def report_to_csv(report: dict) -> str:
    flags = report.get("individual_flags", [])
    if not flags:
        return ""

    df = pd.DataFrame(flags)
    output = StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()


def build_sample_data() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "txn_id": "T101",
            "store_id": "NYC-014",
            "products": "PS5 Console",
            "quantity": 1,
            "payment_method": "GiftCard-A93",
            "cashier_note": "Customer paid with stack of gift cards and asked if more were available in back"
        },
        {
            "txn_id": "T102",
            "store_id": "NYC-027",
            "products": "PS5 Console",
            "quantity": 1,
            "payment_method": "GiftCard-A93",
            "cashier_note": "Same buyer pattern noted from previous day and declined receipt"
        },
        {
            "txn_id": "T103",
            "store_id": "NJ-003",
            "products": "Pokemon ETB",
            "quantity": 2,
            "payment_method": "GiftCard-B14",
            "cashier_note": "Customer asked about restock schedule and carried empty duffel bag"
        },
        {
            "txn_id": "T104",
            "store_id": "LA-021",
            "products": "AirPods Pro",
            "quantity": 1,
            "payment_method": "Visa-4421",
            "cashier_note": "Normal family purchase nothing unusual"
        }
    ])


def render_business_context():
    st.markdown("## Business Problem")
    st.info(
        "Retail teams often see transactions store by store. A purchase that looks normal in one location "
        "can become suspicious when connected across stores, products, payment methods, and cashier notes. "
        "Sentinel AI turns scattered transaction signals into a human-review risk queue."
    )

    st.markdown("## What Sentinel Does")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Detects risk indicators**")
        st.caption("Flags high-demand products, gift card patterns, quantity signals, and suspicious cashier notes.")
    with col2:
        st.markdown("**Connects weak signals**")
        st.caption("Links transactions across stores and payment methods to surface patterns that may be missed manually.")
    with col3:
        st.markdown("**Supports human decisions**")
        st.caption("Creates explainable reports, recommended actions, and responsible AI notes for review.")


def render_dashboard(report: dict):
    if report.get("error"):
        st.error(report["error"])
        st.write("Required columns:")
        st.code(", ".join(report.get("required_columns", [])))
        return

    summary = report["executive_summary"]
    flags_df = pd.DataFrame(report["individual_flags"])
    networks_df = pd.DataFrame(report["suspected_networks"])

    st.markdown("## Executive Decision Summary")

    exposure = f"${summary['estimated_inventory_exposure']:,.0f}+"

    st.success(
        f"Sentinel reviewed **{summary['total_transactions_reviewed']} transactions** and created a human-review queue of "
        f"**{summary['total_flagged_transactions']} flagged transactions** across **{summary['stores_affected']} stores**. "
        f"Estimated inventory exposure is **{exposure}**. Recommended focus: **{summary['recommended_focus']}**"
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Flagged Transactions", summary["total_flagged_transactions"])
    k2.metric("High Risk", summary["high_risk_transactions"])
    k3.metric("Stores Affected", summary["stores_affected"])
    k4.metric("Linked Networks", summary["suspected_networks"])
    k5.metric("Estimated Exposure", exposure)

    st.markdown("## Recommended Action Queue")
    for idx, action in enumerate(report["recommended_action_queue"], start=1):
        st.write(f"**{idx}.** {action}")

    st.markdown("## Risk Level Summary")
    risk_counts = flags_df["risk_level"].value_counts().reindex(["HIGH", "MEDIUM", "LOW"]).fillna(0)
    st.bar_chart(risk_counts)

    st.markdown("## Flagged Transactions")
    display_flags = flags_df.copy()
    st.dataframe(
        display_flags,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("## Store-Level Risk Concentration")
    store_counts = flags_df[flags_df["risk_level"].isin(["HIGH", "MEDIUM"])]["store_id"].value_counts()
    if not store_counts.empty:
        st.bar_chart(store_counts)
    else:
        st.caption("No store-level risk concentration detected.")

    st.markdown("## Linked Transaction Network Detection")
    if not networks_df.empty:
        networks_display = networks_df.copy()
        for col in ["linked_transactions", "stores", "products"]:
            if col in networks_display.columns:
                networks_display[col] = networks_display[col].apply(safe_join)

        st.dataframe(
            networks_display,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.caption("No linked payment-method networks detected in this dataset.")

    st.markdown("## Responsible AI Note")
    st.warning(report["responsible_ai_note"])

    json_report = json.dumps(report, indent=2)
    csv_report = report_to_csv(report)

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download JSON Report",
            data=json_report,
            file_name="sentinel_report.json",
            mime="application/json"
        )

    with c2:
        st.download_button(
            "Download CSV Report",
            data=csv_report,
            file_name="sentinel_flagged_transactions.csv",
            mime="text/csv"
        )


# -----------------------------
# Main app
# -----------------------------

st.sidebar.title("Workflow")
st.sidebar.write("1. Upload transaction CSV")
st.sidebar.write("2. Click Analyze")
st.sidebar.write("3. Review executive summary")
st.sidebar.write("4. Inspect flagged transactions")
st.sidebar.write("5. Download report")

st.title("Sentinel AI Retail Risk Intelligence Dashboard")
st.caption("AI-assisted loss-prevention workflow for identifying reseller and fraud-risk patterns across store transactions.")

render_business_context()

st.markdown("---")
st.markdown("## Analyze Transactions")

uploaded_file = st.file_uploader("Upload transaction CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.markdown("### Uploaded Transaction Data")
    st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button("Analyze Transactions"):
        report = analyze_transactions(df)
        st.session_state["report"] = report
        st.success("Analysis complete.")

else:
    st.info("Upload a CSV to analyze new transactions, or load the demo dataset below.")

    if st.button("Load Existing Demo Dashboard"):
        df = build_sample_data()
        report = analyze_transactions(df)
        st.session_state["report"] = report
        st.success("Demo analysis loaded.")

if "report" in st.session_state:
    st.markdown("---")
    render_dashboard(st.session_state["report"])

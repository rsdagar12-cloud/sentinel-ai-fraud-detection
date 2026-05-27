import json
from datetime import datetime
from io import StringIO

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Sentinel Retail Risk Intelligence",
    page_icon="🛡️",
    layout="wide"
)


# -----------------------------
# Helpers
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


def estimate_unit_value(product: str) -> int:
    product = str(product).lower()

    if "ps5" in product or "console" in product:
        return 650
    if "pokemon" in product or "etb" in product:
        return 120
    if "airpods" in product:
        return 250
    if "iphone" in product or "phone" in product:
        return 900
    if "ipad" in product or "tablet" in product:
        return 700

    return 150


def analyze_transactions(df: pd.DataFrame) -> dict:
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

        try:
            quantity = int(row.get("quantity", 1))
        except Exception:
            quantity = 1

        product_lower = products.lower()
        payment_lower = payment_method.lower()
        note_lower = cashier_note.lower()

        score = 0.0
        reasons = []
        actions = []

        high_demand_terms = [
            "ps5", "console", "pokemon", "etb", "airpods", "iphone", "ipad", "limited"
        ]

        if any(term in product_lower for term in high_demand_terms):
            score += 0.20
            reasons.append("High-demand product")
            actions.append("Review product availability before next restock")

        if "giftcard" in payment_lower or "gift card" in payment_lower:
            score += 0.20
            reasons.append("Gift card payment")
            actions.append("Check if payment method repeats across stores")

        if quantity >= 2:
            score += 0.15
            reasons.append("Multiple units")
            actions.append("Review fair purchase-limit policy")

        behavior_terms = [
            "declined receipt",
            "restock",
            "stock",
            "same buyer",
            "previous day",
            "empty duffel",
            "script",
            "stack",
            "more available",
            "other stores",
            "sealed",
            "gift cards"
        ]

        matched_terms = [term for term in behavior_terms if term in note_lower]

        if matched_terms:
            score += min(0.35, 0.08 * len(matched_terms))
            reasons.append("Cashier note indicates unusual buying pattern")
            actions.append("Manager should review cashier note and transaction history")

        confidence = round(min(score, 0.95), 2)

        if confidence >= 0.75:
            risk_level = "HIGH"
        elif confidence >= 0.45:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        inventory_value = estimate_unit_value(products) * quantity

        flags.append({
            "txn_id": txn_id,
            "store_id": store_id,
            "products": products,
            "quantity": quantity,
            "payment_method": payment_method,
            "estimated_inventory_value": inventory_value,
            "confidence": confidence,
            "risk_level": risk_level,
            "why_flagged": "; ".join(reasons) if reasons else "No major risk indicators",
            "manager_action": "; ".join(dict.fromkeys(actions)) if actions else "No immediate action needed"
        })

    flags_df = pd.DataFrame(flags)

    risky_df = flags_df[flags_df["risk_level"].isin(["HIGH", "MEDIUM"])]
    high_risk_count = int((flags_df["risk_level"] == "HIGH").sum())
    medium_risk_count = int((flags_df["risk_level"] == "MEDIUM").sum())
    low_risk_count = int((flags_df["risk_level"] == "LOW").sum())

    inventory_at_risk = int(risky_df["estimated_inventory_value"].sum()) if not risky_df.empty else 0
    stores_needing_attention = int(risky_df["store_id"].nunique()) if not risky_df.empty else 0
    avg_confidence = round(float(flags_df["confidence"].mean()), 2) if not flags_df.empty else 0

    # Business impact model
    # Conservative operating assumptions for a retail demo.
    customer_capture_rate = 0.35
    accessory_attach_value = 150
    annual_customer_value = 500
    manual_review_minutes_saved = 8

    estimated_customer_visits_protected = max(1, int(len(risky_df) * customer_capture_rate + 1)) if not risky_df.empty else 0
    protected_inventory_value = int(inventory_at_risk * customer_capture_rate)
    revenue_opportunity_protected = estimated_customer_visits_protected * accessory_attach_value
    customer_value_protected = estimated_customer_visits_protected * annual_customer_value
    review_time_saved = int(len(flags_df) * manual_review_minutes_saved)

    # Network detection
    suspected_networks = []

    gift_card_df = risky_df[
        risky_df["payment_method"].str.contains("GiftCard|gift card", case=False, na=False)
    ]

    if not gift_card_df.empty:
        network_num = 1
        for payment_method, group in gift_card_df.groupby("payment_method"):
            txns = sorted(group["txn_id"].unique().tolist())
            stores = sorted(group["store_id"].unique().tolist())

            if len(txns) >= 2 or len(stores) >= 2:
                suspected_networks.append({
                    "network_id": f"NETWORK-{network_num}",
                    "shared_signal": payment_method,
                    "transactions": txns,
                    "stores": stores,
                    "products": sorted(group["products"].unique().tolist()),
                    "risk_level": "HIGH",
                    "confidence": round(float(group["confidence"].mean()), 2),
                    "estimated_inventory_value": int(group["estimated_inventory_value"].sum()),
                    "manager_action": "Review linked transactions and alert nearby stores before next restock"
                })
                network_num += 1

    store_focus = []
    if not risky_df.empty:
        store_summary = (
            risky_df.groupby("store_id")
            .agg(
                flagged_transactions=("txn_id", "count"),
                inventory_value=("estimated_inventory_value", "sum"),
                average_confidence=("confidence", "mean")
            )
            .reset_index()
            .sort_values("inventory_value", ascending=False)
        )

        for _, row in store_summary.iterrows():
            store_focus.append({
                "store_id": row["store_id"],
                "flagged_transactions": int(row["flagged_transactions"]),
                "inventory_value": int(row["inventory_value"]),
                "average_confidence": round(float(row["average_confidence"]), 2)
            })
    else:
        store_summary = pd.DataFrame()

    action_plan = []

    if high_risk_count > 0:
        action_plan.append({
            "Priority": "Today",
            "Action": f"Review {high_risk_count} high-risk transaction(s)",
            "Owner": "Store manager / shift lead",
            "Why it matters": "Protect scarce inventory before the next rush or restock"
        })

    if suspected_networks:
        action_plan.append({
            "Priority": "Today",
            "Action": f"Check {len(suspected_networks)} linked payment pattern(s)",
            "Owner": "Manager / loss prevention",
            "Why it matters": "Find repeated behavior across stores instead of judging one transaction alone"
        })

    if stores_needing_attention > 0:
        action_plan.append({
            "Priority": "This week",
            "Action": f"Coach {stores_needing_attention} store team(s) on neutral cashier notes",
            "Owner": "Store manager",
            "Why it matters": "Better notes create better decisions without profiling customers"
        })

    action_plan.append({
        "Priority": "Ongoing",
        "Action": "Use fair quantity limits for scarce products during launches and restocks",
        "Owner": "Operations manager",
        "Why it matters": "Keeps more products available for genuine customers"
    })

    report = {
        "summary": {
            "transactions_reviewed": int(len(df)),
            "flagged_transactions": int(len(flags_df)),
            "high_risk": high_risk_count,
            "medium_risk": medium_risk_count,
            "low_risk": low_risk_count,
            "stores_needing_attention": stores_needing_attention,
            "linked_networks": int(len(suspected_networks)),
            "average_confidence": avg_confidence,
            "inventory_at_risk": inventory_at_risk,
            "protected_inventory_value": protected_inventory_value,
            "revenue_opportunity_protected": revenue_opportunity_protected,
            "customer_value_protected": customer_value_protected,
            "customer_visits_protected": estimated_customer_visits_protected,
            "review_time_saved_minutes": review_time_saved
        },
        "flagged_transactions": flags,
        "store_focus": store_focus,
        "suspected_networks": suspected_networks,
        "manager_action_plan": action_plan,
        "responsible_ai_note": (
            "Sentinel flags patterns for human review only. It does not prove fraud. "
            "Managers should apply store policy consistently and avoid customer profiling."
        ),
        "report_generated_at": datetime.utcnow().isoformat() + "Z",
        "validation": {"passed": True, "issues": []}
    }

    return report


def report_to_csv(report: dict) -> str:
    df = pd.DataFrame(report.get("flagged_transactions", []))
    output = StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()


def build_sample_data() -> pd.DataFrame:
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
        }
    ])


def money(value):
    return f"${int(value):,}"


# -----------------------------
# Pages
# -----------------------------

def page_home():
    st.title("Sentinel Retail Risk Intelligence")
    st.caption("A daily manager tool for protecting scarce inventory, reducing manual review, and keeping genuine customers from leaving disappointed.")

    st.markdown("## What problem does Sentinel solve?")

    st.write(
        "When high-demand products arrive, store teams usually see only their own transactions. "
        "A single sale may look normal. But across stores, the same payment method, product pattern, or cashier note can reveal a bigger issue."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Use case", "Daily review")
        st.write("Managers check flagged activity after busy periods, launches, and restocks.")

    with c2:
        st.metric("Main goal", "Protect availability")
        st.write("Keep scarce products available for genuine customers, not just the fastest repeat buyers.")

    with c3:
        st.metric("Output", "Action queue")
        st.write("The app tells managers what to review, which stores are affected, and what action to take.")

    st.markdown("## Built for high-demand electronics retail")

    st.success(
        "Sentinel helps store managers answer three questions: What is at risk? Which stores need attention? What should we do next?"
    )

    st.markdown("## How employees use it")
    use_cases = pd.DataFrame([
        {
            "When": "After a restock",
            "User": "Store manager",
            "What they do": "Upload transactions from the day",
            "Value": "Spot suspicious buying patterns before inventory disappears again"
        },
        {
            "When": "During a product launch",
            "User": "Shift lead",
            "What they do": "Review high-risk transactions and cashier notes",
            "Value": "Apply fair purchase limits consistently"
        },
        {
            "When": "End of day",
            "User": "Operations / loss prevention",
            "What they do": "Download JSON or CSV report",
            "Value": "Create a structured audit trail instead of relying on memory"
        },
        {
            "When": "Weekly store review",
            "User": "District manager",
            "What they do": "Compare store-level risk concentration",
            "Value": "Coach teams and adjust launch/restock controls"
        }
    ])

    st.dataframe(use_cases, use_container_width=True, hide_index=True)


def page_analyze():
    st.title("Run Transaction Review")
    st.caption("Upload a CSV or use the demo dataset.")

    uploaded_file = st.file_uploader("Upload transaction CSV", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.markdown("### Uploaded transactions")
        st.dataframe(df, use_container_width=True, hide_index=True)

        if st.button("Analyze transactions"):
            report = analyze_transactions(df)
            st.session_state["report"] = report
            st.success("Review complete. Open the Manager Dashboard from the left menu.")

    else:
        st.info("No file uploaded. Use the demo to see how the app works.")

        if st.button("Load demo transactions"):
            df = build_sample_data()
            st.session_state["demo_data"] = df
            report = analyze_transactions(df)
            st.session_state["report"] = report
            st.success("Demo loaded. Open the Manager Dashboard from the left menu.")

        if "demo_data" in st.session_state:
            st.markdown("### Demo transactions")
            st.dataframe(st.session_state["demo_data"], use_container_width=True, hide_index=True)

    st.markdown("### Required CSV columns")
    st.code("txn_id, store_id, products, quantity, payment_method, cashier_note")


def page_dashboard():
    st.title("Manager Dashboard")

    if "report" not in st.session_state:
        st.info("Run an analysis first. Go to 'Run Transaction Review' and load the demo or upload a CSV.")
        return

    report = st.session_state["report"]

    if report.get("error"):
        st.error(report["error"])
        st.code(", ".join(report.get("required_columns", [])))
        return

    summary = report["summary"]

    st.markdown("## Today’s Risk Snapshot")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Transactions reviewed", summary["transactions_reviewed"])
    k2.metric("High-risk items", summary["high_risk"])
    k3.metric("Stores needing attention", summary["stores_needing_attention"])
    k4.metric("Linked payment patterns", summary["linked_networks"])

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Inventory at risk", money(summary["inventory_at_risk"]))
    k6.metric("Revenue opportunity protected", money(summary["revenue_opportunity_protected"]))
    k7.metric("Customer visits protected", summary["customer_visits_protected"])
    k8.metric("Review time saved", f"{summary['review_time_saved_minutes']} min")

    st.markdown("## What needs attention")

    if summary["high_risk"] > 0:
        st.error(
            f"{summary['high_risk']} high-risk transaction(s) need manager review today. "
            f"Estimated inventory at risk: {money(summary['inventory_at_risk'])}."
        )
    elif summary["medium_risk"] > 0:
        st.warning(
            f"{summary['medium_risk']} medium-risk transaction(s) should be reviewed before the next restock."
        )
    else:
        st.success("No major risk concentration detected.")

    st.markdown("## Manager Action Plan")
    action_df = pd.DataFrame(report["manager_action_plan"])
    st.dataframe(action_df, use_container_width=True, hide_index=True)

    st.markdown("## Store focus")
    store_df = pd.DataFrame(report["store_focus"])
    if not store_df.empty:
        store_df["inventory_value"] = store_df["inventory_value"].apply(money)
        st.dataframe(store_df, use_container_width=True, hide_index=True)

        chart_df = pd.DataFrame(report["store_focus"])
        chart_df = chart_df.set_index("store_id")["flagged_transactions"]
        st.bar_chart(chart_df)
    else:
        st.caption("No store-level risk concentration detected.")

    st.markdown("## Flagged transactions")
    flagged_df = pd.DataFrame(report["flagged_transactions"])
    st.dataframe(flagged_df, use_container_width=True, hide_index=True)

    st.markdown("## Linked payment patterns")
    networks_df = pd.DataFrame(report["suspected_networks"])
    if not networks_df.empty:
        for col in ["transactions", "stores", "products"]:
            if col in networks_df.columns:
                networks_df[col] = networks_df[col].apply(safe_join)

        networks_df["estimated_inventory_value"] = networks_df["estimated_inventory_value"].apply(money)
        st.dataframe(networks_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No linked payment patterns detected.")

    st.markdown("## Download reports")

    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            "Download JSON report",
            data=json.dumps(report, indent=2),
            file_name="sentinel_report.json",
            mime="application/json"
        )

    with c2:
        st.download_button(
            "Download CSV report",
            data=report_to_csv(report),
            file_name="sentinel_flagged_transactions.csv",
            mime="text/csv"
        )


def page_impact():
    st.title("Business Impact")

    if "report" not in st.session_state:
        st.info("Run an analysis first to see impact numbers.")
        return

    summary = st.session_state["report"]["summary"]

    st.markdown("## Estimated value created")

    st.write(
        "Sentinel is not just flagging transactions. It helps the store protect inventory availability, save manager review time, "
        "and recover customer revenue that could be lost when genuine customers leave without the product."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Inventory protected scenario", money(summary["protected_inventory_value"]))
        st.caption("Estimated portion of at-risk inventory that could be redirected to genuine customers.")

    with c2:
        st.metric("Attach revenue protected", money(summary["revenue_opportunity_protected"]))
        st.caption("Estimated accessory, service, or protection-plan opportunity retained.")

    with c3:
        st.metric("Customer value protected", money(summary["customer_value_protected"]))
        st.caption("Estimated annual value of keeping disappointed customers engaged.")

    st.markdown("## Where the value comes from")

    impact_table = pd.DataFrame([
        {
            "Business issue": "Scarce inventory sells out too quickly",
            "How Sentinel helps": "Flags repeat high-demand product patterns before the next restock",
            "Business value": "More genuine customers get access to products"
        },
        {
            "Business issue": "Managers rely on memory or scattered notes",
            "How Sentinel helps": "Creates a structured review queue",
            "Business value": "Faster, more consistent decisions"
        },
        {
            "Business issue": "One store cannot see cross-store behavior",
            "How Sentinel helps": "Links stores through payment methods and transaction signals",
            "Business value": "Earlier detection of coordinated patterns"
        },
        {
            "Business issue": "Genuine customers leave disappointed",
            "How Sentinel helps": "Protects inventory availability and product launch fairness",
            "Business value": "Higher trust, better conversion, stronger repeat visits"
        }
    ])

    st.dataframe(impact_table, use_container_width=True, hide_index=True)

    st.warning(
        "These figures are directional estimates for decision support. They are not audited financial results."
    )


def page_team_playbook():
    st.title("Store Team Playbook")

    st.markdown("## When to use Sentinel")

    playbook = pd.DataFrame([
        {
            "Moment": "After product restock",
            "Who uses it": "Store manager",
            "Action": "Upload daily transaction file",
            "Decision": "Which transactions need review before the next restock?"
        },
        {
            "Moment": "During high-demand launch week",
            "Who uses it": "Shift lead",
            "Action": "Check flagged products and payment patterns",
            "Decision": "Should fair quantity limits be applied?"
        },
        {
            "Moment": "End of day",
            "Who uses it": "Operations / LP",
            "Action": "Download CSV/JSON report",
            "Decision": "Which stores need follow-up?"
        },
        {
            "Moment": "Weekly manager review",
            "Who uses it": "District manager",
            "Action": "Compare stores and repeated signals",
            "Decision": "Which teams need coaching or policy support?"
        }
    ])

    st.dataframe(playbook, use_container_width=True, hide_index=True)

    st.markdown("## What employees should capture")

    st.write("- Product purchased")
    st.write("- Quantity")
    st.write("- Payment method")
    st.write("- Whether the customer asked about restocks or other locations")
    st.write("- Whether the same buying pattern has appeared recently")
    st.write("- Neutral cashier notes based on behavior, not appearance")


def page_guardrails():
    st.title("Human Review & Guardrails")

    st.warning(
        "Sentinel does not accuse customers. It flags transaction patterns for manager review."
    )

    st.markdown("## Rules for safe use")

    st.write("- Do not use demographic descriptions as risk criteria")
    st.write("- Do not treat a risk score as proof of fraud")
    st.write("- Apply the same purchase rules to every customer")
    st.write("- Review the transaction context before taking action")
    st.write("- Use the tool to protect inventory fairness, not to profile people")

    st.markdown("## Why this matters")

    st.write(
        "A strong retail risk tool should protect the business and the customer experience at the same time. "
        "The goal is fair inventory access, better manager visibility, and faster review — not automatic punishment."
    )


# -----------------------------
# Navigation
# -----------------------------

st.sidebar.title("Sentinel")
page = st.sidebar.radio(
    "Menu",
    [
        "Home",
        "Run Transaction Review",
        "Manager Dashboard",
        "Business Impact",
        "Store Team Playbook",
        "Human Review & Guardrails"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Daily workflow")
st.sidebar.write("1. Upload CSV")
st.sidebar.write("2. Run review")
st.sidebar.write("3. Check dashboard")
st.sidebar.write("4. Download report")

if page == "Home":
    page_home()
elif page == "Run Transaction Review":
    page_analyze()
elif page == "Manager Dashboard":
    page_dashboard()
elif page == "Business Impact":
    page_impact()
elif page == "Store Team Playbook":
    page_team_playbook()
elif page == "Human Review & Guardrails":
    page_guardrails()

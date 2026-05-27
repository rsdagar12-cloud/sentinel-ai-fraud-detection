import json
import sys
from datetime import datetime, timezone
from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-sonnet-4-5"
FINAL_REPORT = {}

MOCK_TRANSACTIONS = [
    {"txn_id": "T001", "store": "NYC-014", "timestamp": "2024-11-12T09:14:00", "items": ["PS5 Console"], "qty": 1, "payment": "GiftCard-A93", "cashier_note": "Customer paid with stack of gift cards, declined receipt printout, asked if more in back."},
    {"txn_id": "T002", "store": "NYC-027", "timestamp": "2024-11-12T11:02:00", "items": ["PS5 Console"], "qty": 1, "payment": "GiftCard-A93", "cashier_note": "Same brown jacket guy from yesterday? Paid gift card, in and out fast."},
    {"txn_id": "T003", "store": "NJ-003", "timestamp": "2024-11-12T13:45:00", "items": ["PS5 Console", "Pokemon ETB"], "qty": 2, "payment": "GiftCard-B14", "cashier_note": "Woman bought 2 consoles, said gift for nephews. No emotion. Gift cards stacked."},
    {"txn_id": "T004", "store": "NYC-014", "timestamp": "2024-11-13T09:22:00", "items": ["Pokemon ETB"], "qty": 3, "payment": "GiftCard-C77", "cashier_note": "Polite, very specific about needing sealed boxes only. Checked SKU date codes."},
    {"txn_id": "T005", "store": "NYC-099", "timestamp": "2024-11-13T10:05:00", "items": ["PS5 Console"], "qty": 1, "payment": "GiftCard-C77", "cashier_note": "Buyer asked which other stores had stock. Paid gift card."},
    {"txn_id": "T006", "store": "LA-021", "timestamp": "2024-11-13T16:30:00", "items": ["AirPods Pro"], "qty": 2, "payment": "Visa-****4421", "cashier_note": "Regular family purchase, mom and kid, nothing unusual."},
    {"txn_id": "T007", "store": "NYC-027", "timestamp": "2024-11-14T09:40:00", "items": ["PS5 Console"], "qty": 1, "payment": "GiftCard-D02", "cashier_note": "Different guy but exact same script — 'do you have more in stock at other locations?'"},
    {"txn_id": "T008", "store": "NJ-003", "timestamp": "2024-11-14T12:15:00", "items": ["Pokemon ETB"], "qty": 2, "payment": "GiftCard-D02", "cashier_note": "Customer carrying empty duffel, paid gift cards, asked about restock schedule."},
]

TXN_INDEX = {t["txn_id"]: t for t in MOCK_TRANSACTIONS}


def trace(msg):
    print(msg, file=sys.stderr)


def tool_list_transaction_ids(filter_by=None):
    out = []
    for t in MOCK_TRANSACTIONS:
        if filter_by == "gift_card_only" and not t["payment"].startswith("GiftCard"):
            continue
        out.append({
            "txn_id": t["txn_id"],
            "store": t["store"],
            "timestamp": t["timestamp"],
            "payment": t["payment"]
        })
    return out


def tool_get_transaction(txn_id):
    return TXN_INDEX.get(txn_id, {"error": f"{txn_id} not found"})


def tool_lookup_gift_card(payment_id):
    hits = [t for t in MOCK_TRANSACTIONS if t["payment"] == payment_id]
    return {
        "payment_id": payment_id,
        "txn_ids": [t["txn_id"] for t in hits],
        "stores": sorted({t["store"] for t in hits}),
        "unique_store_count": len({t["store"] for t in hits}),
    }


def tool_submit_report(report):
    FINAL_REPORT["data"] = report
    return {"status": "received"}


TOOL_DISPATCH = {
    "list_transaction_ids": tool_list_transaction_ids,
    "get_transaction": tool_get_transaction,
    "lookup_gift_card": tool_lookup_gift_card,
    "submit_report": tool_submit_report,
}

TOOLS = [
    {
        "name": "list_transaction_ids",
        "description": "List transaction IDs with minimal metadata.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_by": {
                    "type": "string",
                    "enum": ["gift_card_only"]
                }
            }
        }
    },
    {
        "name": "get_transaction",
        "description": "Fetch full canonical transaction by txn_id.",
        "input_schema": {
            "type": "object",
            "properties": {"txn_id": {"type": "string"}},
            "required": ["txn_id"]
        }
    },
    {
        "name": "lookup_gift_card",
        "description": "Find all transactions using the same gift card.",
        "input_schema": {
            "type": "object",
            "properties": {"payment_id": {"type": "string"}},
            "required": ["payment_id"]
        }
    },
    {
        "name": "submit_report",
        "description": "Submit the final structured report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "suspected_networks": {"type": "array", "items": {"type": "object"}},
                "individual_flags": {"type": "array", "items": {"type": "object"}},
                "responsible_ai_notes": {"type": "string"}
            },
            "required": ["suspected_networks", "individual_flags", "responsible_ai_notes"]
        }
    }
]

SYSTEM_PROMPT = """
You are a retail loss-prevention analyst.

You MUST:
1. Call list_transaction_ids first.
2. Call lookup_gift_card for gift card payments.
3. Call get_transaction before citing transaction details.
4. Call submit_report exactly once before finishing.

Do not end without calling submit_report.

Final report must include:
- suspected_networks
- individual_flags
- responsible_ai_notes

Each individual flag must include:
txn_id, store_id, products, quantity, confidence, risk_level, reason, recommended_action.
"""


def run_agent(max_turns=25):
    messages = [{
        "role": "user",
        "content": "Analyze the transaction database for reseller networks and submit the final structured report."
    }]

    for turn in range(max_turns):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": resp.content})

        tool_results = []

        for block in resp.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input or {}

            trace(f"[turn {turn}] -> {tool_name}({tool_input})")

            try:
                result = TOOL_DISPATCH[tool_name](**tool_input)
            except Exception as e:
                result = {"error": str(e)}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result)
            })

        if "data" in FINAL_REPORT:
            return FINAL_REPORT["data"]

        if not tool_results:
            messages.append({
                "role": "user",
                "content": "You did not submit the report. You must call submit_report now with the final structured findings."
            })
            continue

        messages.append({"role": "user", "content": tool_results})

    return {
        "error": "No report submitted",
        "suspected_networks": [],
        "individual_flags": [],
        "responsible_ai_notes": "Agent did not submit a report within max turns."
    }


def validate_report(report):
    issues = []

    for flag in report.get("individual_flags", []):
        tid = flag.get("txn_id")
        src = TXN_INDEX.get(tid)

        if not src:
            issues.append(f"{tid}: unknown txn_id")
            continue

        if flag.get("store_id") != src["store"]:
            issues.append(f"{tid}: store mismatch")

        if not set(flag.get("products", [])).issubset(set(src["items"])):
            issues.append(f"{tid}: product mismatch")

    report["validation"] = {
        "passed": len(issues) == 0,
        "issues": issues
    }

    return report


if __name__ == "__main__":
    report = run_agent()
    report.setdefault(
        "report_generated_at",
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    report = validate_report(report)

    print(json.dumps(report, indent=2))

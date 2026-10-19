# app.py - Streamlit user interface. It only DISPLAYS results; all logic is in agents.py
import streamlit as st
from agents import (SAMPLE_INVOICES, EXISTING_INVOICES, PAYMENTS, CHECK_LABELS,
                    VERIFIED, FLAGGED, process_invoice, rupees, to_money)

st.set_page_config(page_title="Invoice Processing", page_icon="🧾", layout="wide")

FIELD_NAMES = {"invoice_number": "Invoice number", "vendor": "Vendor", "invoice_date": "Invoice date",
               "subtotal": "Subtotal", "tax": "Tax", "total": "Total"}
RESULT_TEXT = {"PASS": "✅ Pass", "FAIL": "❌ Fail", "SKIPPED": "⚠️ Not checked"}


def money_text(value):
    """Show a text amount as ₹1,234.00, or a dash if it is missing/invalid."""
    amount = to_money(value)
    return rupees(amount) if amount is not None else "—"


# ---------------- Sidebar: choose invoice and run ----------------
st.sidebar.title("🧾 Invoice Processing")
choice = st.sidebar.selectbox("Invoice", list(SAMPLE_INVOICES.keys()))
if st.sidebar.button("Process Invoice", type="primary"):
    st.session_state["result"] = process_invoice(SAMPLE_INVOICES[choice])
st.sidebar.caption("Synthetic demo data. No real payments are made.")

# ---------------- Main page ----------------
st.title("Invoice Processing Dashboard")

result = st.session_state.get("result")
if result is None:
    st.info("Select an invoice in the sidebar and click Process Invoice.")
    st.stop()

invoice = result["extracted"]
validation = result["validation"]
status = result["final_status"]

# Final decision banner + reasons
if status == VERIFIED:
    st.success(status, icon="✅")
elif status == FLAGGED:
    st.error(status, icon="🚩")
else:
    st.warning(status, icon="⚠️")
for reason in result["reasons"]:
    st.write("• " + reason)

# Key figures
payment_text = "—"
if validation is not None and validation["reconciliation"]["payment_amount"] is not None:
    payment_text = rupees(validation["reconciliation"]["payment_amount"])
col1, col2, col3, col4 = st.columns(4)
col1.metric("Invoice number", invoice["invoice_number"] or "—")
col2.metric("Vendor", invoice["vendor"] or "—")
col3.metric("Invoice total", money_text(invoice["total"]))
col4.metric("Payment recorded", payment_text)

# Details in tabs
tab_invoice, tab_checks, tab_recon, tab_flow, tab_data = st.tabs(
    ["Invoice", "Validation", "Reconciliation", "Workflow", "Records"])

with tab_invoice:
    rows = []
    for field, value in invoice.items():
        if field in ("subtotal", "tax", "total"):
            shown = money_text(value)
        else:
            shown = value if value != "" else "—"
        rows.append({"Field": FIELD_NAMES[field], "Value": shown})
    st.dataframe(rows, hide_index=True)

with tab_checks:
    if validation is None:
        st.warning("Validation was not run.")
    else:
        rows = []
        for name, check in validation["checks"].items():
            rows.append({"Check": CHECK_LABELS[name],
                         "Result": RESULT_TEXT[check["result"]],
                         "Details": check["detail"]})
        st.dataframe(rows, hide_index=True)

with tab_recon:
    if validation is None or validation["reconciliation"]["payment_amount"] is None:
        st.warning("No payment available to reconcile.")
    else:
        recon = validation["reconciliation"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Invoice total", rupees(recon["invoice_total"]))
        c2.metric("Payment recorded", rupees(recon["payment_amount"]))
        c3.metric("Difference", rupees(recon["difference"]))

with tab_flow:
    left, right = st.columns(2)
    with left:
        st.subheader("Task plan")
        for number, task in enumerate(result["plan"], start=1):
            st.write(f"{number}. {task}")
    with right:
        st.subheader("Audit log")
        for number, line in enumerate(result["audit_log"], start=1):
            st.write(f"{number}. {line}")

with tab_data:
    left, right = st.columns(2)
    with left:
        st.subheader("Existing invoices")
        st.dataframe(EXISTING_INVOICES, hide_index=True)
    with right:
        st.subheader("Payment records")
        st.dataframe(PAYMENTS, hide_index=True)

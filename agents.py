"""
agents.py - the four simple "agents" and the orchestrator.

IMPORTANT (be honest in the viva):
Each agent is an ordinary Python function that follows fixed rules.
There is NO language model, NO OCR and NO database in this version.
It SIMULATES a multi-agent workflow using deterministic if-else rules.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# ------------------------------------------------------------------
# 1. Constants: the three possible final statuses and required fields
# ------------------------------------------------------------------
VERIFIED = "VERIFIED — ELIGIBLE FOR HUMAN APPROVAL REVIEW"
FLAGGED = "FLAGGED FOR HUMAN REVIEW"
INCOMPLETE = "INCOMPLETE — ADDITIONAL INFORMATION REQUIRED"

REQUIRED_FIELDS = ["invoice_number", "vendor", "invoice_date", "subtotal", "tax", "total"]

# Friendly names for the five validation checks (used by the UI and the critic)
CHECK_LABELS = {
    "required_fields": "Required fields present",
    "total_calculation": "Total = subtotal + tax",
    "duplicate_check": "Invoice number is not a duplicate",
    "payment_record": "Payment record exists",
    "payment_amount": "Payment amount matches invoice total",
}

# ------------------------------------------------------------------
# 2. Synthetic (fictional) data. Edit these to try your own test cases.
#    Amounts are written as text so Decimal can handle them exactly.
# ------------------------------------------------------------------
SAMPLE_INVOICES = {
    "INV101 - Valid invoice": {
        "invoice_number": "INV101", "vendor": "ABC Supplies", "invoice_date": "2026-10-01",
        "subtotal": "10000", "tax": "1800", "total": "11800"},
    "INV102 - Payment mismatch": {
        "invoice_number": "INV102", "vendor": "XYZ Services", "invoice_date": "2026-10-03",
        "subtotal": "20000", "tax": "3600", "total": "23600"},
    "INV103 - Duplicate invoice": {
        "invoice_number": "INV103", "vendor": "Demo Traders", "invoice_date": "2026-10-05",
        "subtotal": "5000", "tax": "900", "total": "5900"},
    # ---- extra test cases (not required, but useful for the demo) ----
    "INV104 - Wrong total (extra test)": {
        "invoice_number": "INV104", "vendor": "Kaveri Stationers", "invoice_date": "2026-10-07",
        "subtotal": "8000", "tax": "1440", "total": "9000"},      # should be 9440
    "INV105 - Missing vendor (extra test)": {
        "invoice_number": "INV105", "vendor": "", "invoice_date": "2026-10-08",
        "subtotal": "4000", "tax": "720", "total": "4720"},
    "INV106 - No payment record (extra test)": {
        "invoice_number": "INV106", "vendor": "Sahyadri Logistics", "invoice_date": "2026-10-09",
        "subtotal": "6000", "tax": "1080", "total": "7080"},
}

# Invoices already processed earlier (INV103 is here -> duplicate)
EXISTING_INVOICES = [
    {"invoice_number": "INV090", "vendor": "Pune Office Mart", "invoice_date": "2026-09-12"},
    {"invoice_number": "INV091", "vendor": "Mulshi Hardware", "invoice_date": "2026-09-20"},
    {"invoice_number": "INV103", "vendor": "Demo Traders", "invoice_date": "2026-09-25"},
]

# Synthetic payment records (INV106 has none on purpose)
PAYMENTS = [
    {"invoice_number": "INV101", "amount": "11800", "paid_on": "2026-10-10"},
    {"invoice_number": "INV102", "amount": "20000", "paid_on": "2026-10-11"},
    {"invoice_number": "INV103", "amount": "5900", "paid_on": "2026-10-12"},
    {"invoice_number": "INV104", "amount": "9000", "paid_on": "2026-10-13"},
    {"invoice_number": "INV105", "amount": "4720", "paid_on": "2026-10-14"},
]


# ------------------------------------------------------------------
# 3. Small helper functions
# ------------------------------------------------------------------
def is_blank(value):
    """True if a value is None or only spaces."""
    return value is None or str(value).strip() == ""


def to_money(value):
    """Convert text/number to Decimal rounded to 2 places (round half up).
    Returns None if the value is not a valid number."""
    try:
        number = Decimal(str(value).replace(",", "").strip())
    except InvalidOperation:
        return None
    if not number.is_finite():
        return None
    return number.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def rupees(amount):
    """Format a Decimal like ₹11,800.00"""
    return f"₹{amount:,.2f}"


# ------------------------------------------------------------------
# 4. AGENT 1: Planner Agent
# ------------------------------------------------------------------
def planner_agent():
    """Decides WHICH steps are needed to process an invoice."""
    return [
        "Read invoice details",
        "Validate invoice fields and total",
        "Check for duplicates",
        "Reconcile payment",
        "Review results and make final decision",
    ]


# ------------------------------------------------------------------
# 5. AGENT 2: Document Processing Agent
# ------------------------------------------------------------------
def document_agent(invoice):
    """Reads the invoice details.
    This version reads STRUCTURED sample data. It does NOT do OCR."""
    if invoice is None:
        invoice = {}
    extracted = {}
    for field in REQUIRED_FIELDS:
        value = invoice.get(field, "")      # missing field -> empty text, no crash
        extracted[field] = "" if value is None else str(value).strip()
    return extracted


# ------------------------------------------------------------------
# 6. AGENT 3: Validation Agent
# ------------------------------------------------------------------
def validation_agent(invoice, existing_invoices, payments):
    """Runs 5 checks. Each check is PASS, FAIL or SKIPPED (could not be checked)."""
    checks = {}

    # Check 1: required fields
    missing = [f for f in REQUIRED_FIELDS if is_blank(invoice.get(f))]
    if missing:
        checks["required_fields"] = {"result": "FAIL", "detail": "Missing field(s): " + ", ".join(missing)}
    else:
        checks["required_fields"] = {"result": "PASS", "detail": "All required fields are present"}

    # Check 2: total = subtotal + tax (Decimal avoids floating point errors)
    subtotal = to_money(invoice.get("subtotal"))
    tax = to_money(invoice.get("tax"))
    total = to_money(invoice.get("total"))
    if subtotal is None or tax is None or total is None:
        checks["total_calculation"] = {"result": "SKIPPED",
                                       "detail": "Subtotal, tax or total is missing or not a valid number"}
    else:
        expected = subtotal + tax
        text = f"{rupees(subtotal)} + {rupees(tax)} = {rupees(expected)}; invoice total is {rupees(total)}"
        if expected == total:
            checks["total_calculation"] = {"result": "PASS", "detail": text}
        else:
            checks["total_calculation"] = {"result": "FAIL", "detail": text}

    # Check 3: duplicate invoice number
    number = "" if is_blank(invoice.get("invoice_number")) else str(invoice["invoice_number"]).strip().upper()
    if number == "":
        checks["duplicate_check"] = {"result": "SKIPPED", "detail": "No invoice number to check"}
    else:
        is_duplicate = False
        for old in existing_invoices:
            if str(old["invoice_number"]).strip().upper() == number:
                is_duplicate = True
        if is_duplicate:
            checks["duplicate_check"] = {"result": "FAIL",
                                         "detail": f"Invoice number {number} already exists in earlier records"}
        else:
            checks["duplicate_check"] = {"result": "PASS", "detail": f"{number} is a new invoice number"}

    # Check 4: find the payment record for this invoice
    payment = None
    if number != "":
        for record in payments:
            if str(record["invoice_number"]).strip().upper() == number:
                payment = record
                break
    if number == "":
        checks["payment_record"] = {"result": "SKIPPED", "detail": "No invoice number to search with"}
    elif payment is None:
        checks["payment_record"] = {"result": "FAIL", "detail": f"No payment record found for {number}"}
    else:
        checks["payment_record"] = {"result": "PASS", "detail": f"Payment record found (paid on {payment['paid_on']})"}

    # Check 5: payment amount vs invoice total
    payment_amount = None
    if payment is not None:
        payment_amount = to_money(payment["amount"])
    if payment_amount is None or total is None:
        checks["payment_amount"] = {"result": "SKIPPED", "detail": "Payment amount or invoice total is not available"}
    elif payment_amount == total:
        checks["payment_amount"] = {"result": "PASS",
                                    "detail": f"Payment {rupees(payment_amount)} equals invoice total {rupees(total)}"}
    else:
        checks["payment_amount"] = {"result": "FAIL",
                                    "detail": f"Payment {rupees(payment_amount)} does not equal invoice total {rupees(total)}"}

    # Numbers shown in the "payment reconciliation" section of the UI
    reconciliation = {"invoice_total": total, "payment_amount": payment_amount, "difference": None}
    if total is not None and payment_amount is not None:
        reconciliation["difference"] = total - payment_amount

    return {"checks": checks, "reconciliation": reconciliation}


# ------------------------------------------------------------------
# 7. AGENT 4: Critic Agent
# ------------------------------------------------------------------
def critic_agent(invoice, validation_results):
    """Reviews the validation results and decides the final status.
    Returns (final_status, list_of_reasons)."""
    checks = validation_results["checks"]
    name = invoice.get("invoice_number") or "(no invoice number)"
    problems = []      # a rule was broken      -> FLAGGED
    missing_info = []  # we do not have enough information -> INCOMPLETE

    if checks["required_fields"]["result"] == "FAIL":
        missing_info.append(checks["required_fields"]["detail"])
    if checks["total_calculation"]["result"] == "FAIL":
        problems.append("Total is wrong: " + checks["total_calculation"]["detail"])
    if checks["total_calculation"]["result"] == "SKIPPED":
        missing_info.append("Total could not be checked: " + checks["total_calculation"]["detail"])
    if checks["duplicate_check"]["result"] == "FAIL":
        problems.append("Possible duplicate: " + checks["duplicate_check"]["detail"])
    if checks["payment_record"]["result"] == "FAIL":
        # Missing payment is NOT proof of fraud - we only ask for more information
        missing_info.append(checks["payment_record"]["detail"] +
                            ". This is not treated as fraud; the payment record must be supplied.")
    if checks["payment_amount"]["result"] == "FAIL":
        problems.append("Payment mismatch: " + checks["payment_amount"]["detail"])
    # (payment_amount SKIPPED is already explained by the two cases above)

    # Final decision with simple if-else. A failed check can never reach VERIFIED.
    all_pass = all(check["result"] == "PASS" for check in checks.values())
    if len(problems) > 0:
        status = FLAGGED
        reasons = problems + missing_info
    elif len(missing_info) > 0:
        status = INCOMPLETE
        reasons = missing_info
    elif all_pass:
        status = VERIFIED
        reasons = [f"All 5 validation checks passed for {name}.",
                   "A human must still approve. This system never makes a payment."]
    else:
        status = INCOMPLETE   # safety net: something was skipped
        reasons = ["Some checks could not be completed, so the invoice cannot be verified."]
    return status, reasons


# ------------------------------------------------------------------
# 8. ORCHESTRATOR: connects the agents in order
# ------------------------------------------------------------------
def process_invoice(invoice):
    """Planner -> Document -> (gate) -> Validation -> Critic -> final result."""
    audit_log = []

    plan = planner_agent()
    audit_log.append(f"Planner Agent ran: created a plan with {len(plan)} tasks")

    extracted = document_agent(invoice)
    audit_log.append("Document Processing Agent ran: read invoice details (structured data, no OCR)")

    # Decision point: if nothing could be read, stop early (no point validating)
    nothing_found = all(is_blank(value) for value in extracted.values())
    if nothing_found:
        audit_log.append("Validation Agent SKIPPED: no invoice data was extracted")
        audit_log.append("Critic Agent SKIPPED: nothing to review")
        return {"plan": plan, "extracted": extracted, "validation": None,
                "final_status": INCOMPLETE,
                "reasons": ["No invoice data could be read. Please provide the invoice details."],
                "audit_log": audit_log}

    validation = validation_agent(extracted, EXISTING_INVOICES, PAYMENTS)
    audit_log.append("Validation Agent ran: 5 checks completed (fields, total, duplicate, payment record, payment amount)")

    final_status, reasons = critic_agent(extracted, validation)   # critic uses validation output
    audit_log.append(f"Critic Agent ran: decided '{final_status}'")

    return {"plan": plan, "extracted": extracted, "validation": validation,
            "final_status": final_status, "reasons": reasons, "audit_log": audit_log}

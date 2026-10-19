# test_agents.py - simple tests. Run with:  python test_agents.py   (or: pytest)
from agents import SAMPLE_INVOICES, process_invoice, VERIFIED, FLAGGED, INCOMPLETE


def valid_invoice():
    """A fresh copy of the valid invoice so each test can change it."""
    return dict(SAMPLE_INVOICES["INV101 - Valid invoice"])


def test_valid_invoice():
    result = process_invoice(valid_invoice())
    assert result["final_status"] == VERIFIED


def test_payment_mismatch():
    result = process_invoice(SAMPLE_INVOICES["INV102 - Payment mismatch"])
    assert result["final_status"] == FLAGGED


def test_duplicate_invoice():
    result = process_invoice(SAMPLE_INVOICES["INV103 - Duplicate invoice"])
    assert result["final_status"] == FLAGGED


def test_incorrect_total():
    invoice = valid_invoice()
    invoice["total"] = "11000"              # should be 11800
    assert process_invoice(invoice)["final_status"] == FLAGGED


def test_missing_required_field():
    invoice = valid_invoice()
    invoice["vendor"] = ""
    assert process_invoice(invoice)["final_status"] == INCOMPLETE


def test_missing_payment_record():
    invoice = valid_invoice()
    invoice["invoice_number"] = "INV999"    # no payment exists for this number
    result = process_invoice(invoice)
    assert result["final_status"] == INCOMPLETE   # not FLAGGED: missing payment is not fraud


def test_empty_invoice_does_not_crash():
    assert process_invoice({})["final_status"] == INCOMPLETE
    assert process_invoice(None)["final_status"] == INCOMPLETE


def test_invalid_number_does_not_crash():
    invoice = valid_invoice()
    invoice["subtotal"] = "abc"
    assert process_invoice(invoice)["final_status"] == INCOMPLETE


def test_failed_check_is_never_verified():
    for name, invoice in SAMPLE_INVOICES.items():
        result = process_invoice(invoice)
        if result["validation"] is not None:
            results = [c["result"] for c in result["validation"]["checks"].values()]
            if "FAIL" in results:
                assert result["final_status"] != VERIFIED


if __name__ == "__main__":
    all_tests = [test_valid_invoice, test_payment_mismatch, test_duplicate_invoice,
                 test_incorrect_total, test_missing_required_field, test_missing_payment_record,
                 test_empty_invoice_does_not_crash, test_invalid_number_does_not_crash,
                 test_failed_check_is_never_verified]
    for test in all_tests:
        test()                               # an AssertionError here means the test failed
        print("PASS:", test.__name__)
    print("All tests passed.")

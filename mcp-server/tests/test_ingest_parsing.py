from main import _extract_entry_type, _extract_ingest_payload, _validate_ingest_payload


def test_detect_vendor_quote_entry_type_from_command():
    entry_type, confidence = _extract_entry_type("/entry vendor_quote Vendor ABC booth 45jt", None)
    assert entry_type == "vendor_quote"
    assert confidence >= 0.9


def test_extract_vendor_quote_inline_fields():
    payload = _extract_ingest_payload(
        "vendor_quote",
        "/entry vendor_quote Vendor ABC Production booth 45jt lead time 10 days Project CPP",
    )
    assert payload["project"] == "CPP"
    assert payload["vendor"].lower().startswith("abc")
    assert payload["price"] == 45_000_000
    assert payload["lead_time_days"] == 10


def test_project_update_validation_requires_next_step():
    payload = _extract_ingest_payload(
        "project_update",
        "/entry project_update Project CPP status at risk issue vendor delay 2 days",
    )
    confidence, missing_fields = _validate_ingest_payload("project_update", payload, 0.95, None)
    assert "next_step" in missing_fields
    assert confidence < 0.85

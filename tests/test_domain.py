"""Offline contract tests. Hand-authored extractions below are test inputs only."""
from copy import deepcopy
import json

import pytest

from backend import domain


def packet():
    return json.loads((domain.ROOT / "fixtures/01_conflicted.json").read_text())


def empty():
    return {"value": None, "evidence": []}


def fact(p, src, line_id, value, quote=None):
    document = next(doc for doc in p["sources"] if doc["source_id"] == src)
    body = next(line[7:] for line in document["text"].splitlines() if line[:4] == line_id)
    quote = body if quote is None else quote
    start = body.index(quote)
    return {"value": value, "evidence": [
        {"source_id": src, "line_id": line_id, "char_start": start, "char_end": start + len(quote), "quote": quote},
    ]}


def extraction(p):
    sources = {src: {field: empty() for field in domain.FIELDS} for src in domain.SOURCES}
    sources["RFQ"].update({
        "part_id": fact(p, "RFQ", "L002", "BRK-104", "BRK-104"),
        "quantity": fact(p, "RFQ", "L003", 200, "200"),
        "revision": fact(p, "RFQ", "L004", "C", "C"),
        "material": fact(p, "RFQ", "L005", "6061-T6"),
    })
    sources["DRAWING"].update({
        "part_id": fact(p, "DRAWING", "L002", "BRK-104", "BRK-104"),
        "revision": fact(p, "DRAWING", "L003", "B", "B"),
        "material": fact(p, "DRAWING", "L004", "7075-T6"),
    })
    return {"packet_id": p["packet_id"], "sources": sources}


def test_conflict_and_unconfirmed_absence():
    p = packet()
    result = domain.apply_rules(p, extraction(p))
    assert [f["finding_id"] for f in result] == ["revision_conflict", "material_conflict", "finish_missing"]
    assert result[0]["values"] == {"RFQ": "C", "DRAWING": "B"}
    assert result[0]["evidence_refs"] == ["RFQ:L004", "DRAWING:L003"]
    gap = result[2]
    assert gap["policy_refs"] == ["CHECKLIST:L004", "CHECKLIST:L005"]
    assert gap["evidence_refs"] == [] and gap["semantic_review_status"] == "pending"
    assert gap["review_label"] == "Needs review"
    inspected = domain.apply_rules(p, extraction(p), {("RFQ", "finish"), ("DRAWING", "finish")})
    assert inspected[2]["semantic_review_status"] == "confirmed" and domain.quote_readiness(inspected) == "blocked"


@pytest.mark.parametrize(("property", "value"), [
    ("quote", "C"), ("char_start", 0), ("char_end", 8000), ("char_start", False), ("char_end", 19.0),
    ("line_id", "L009"), ("source_id", "DRAWING"), ("source_id", "UNLISTED"),
])
def test_fabricated_and_wrong_source_spans(property, value):
    p = packet()
    extracted = extraction(p)
    extracted["sources"]["RFQ"]["quantity"]["evidence"][0][property] = value
    with pytest.raises(domain.DomainError):
        domain.validate_extraction(p, extracted)


def test_unicode_offsets_are_in_body_codepoints():
    p = packet()
    p["sources"][1]["text"] += "\nL006 | 🔩 Customer finish is 蓝色."
    e = extraction(p)
    e["sources"]["DRAWING"]["finish"] = fact(p, "DRAWING", "L006", "蓝色", "蓝色")
    domain.validate_extraction(p, e)
    # JavaScript UTF-16 code units would put this quote one character too far along.
    span = e["sources"]["DRAWING"]["finish"]["evidence"][0]
    span["char_start"] += 1
    span["char_end"] += 1
    with pytest.raises(domain.DomainError):
        domain.validate_extraction(p, e)


def test_exact_location_does_not_authorize_cross_field_or_policy_facts():
    p = packet()
    e = extraction(p)
    e["sources"]["RFQ"]["finish"] = fact(p, "RFQ", "L005", "6061-T6", "6061-T6")
    with pytest.raises(domain.DomainError):
        domain.validate_extraction(p, e)
    e = extraction(p)
    e["sources"]["CHECKLIST"]["finish"] = fact(p, "CHECKLIST", "L004", "none", "none")
    with pytest.raises(domain.DomainError):
        domain.validate_extraction(p, e)


def test_source_instruction_cannot_supply_finish_or_rule():
    p = json.loads((domain.ROOT / "fixtures/04_injection.json").read_text())
    e = extraction(p)
    assert domain.apply_rules(p, e)[-1]["finding_id"] == "finish_missing"
    e["sources"]["DRAWING"]["finish"] = fact(p, "DRAWING", "L006", "none", "none")
    with pytest.raises(domain.DomainError):
        domain.validate_extraction(p, e)


@pytest.mark.parametrize("quantity", [-1, 0, 1.5, 200.0, True, "200", 20])
def test_quantity_requires_exact_positive_rfq_integer(quantity):
    p = packet()
    e = extraction(p)
    e["sources"]["RFQ"]["quantity"]["value"] = quantity
    with pytest.raises(domain.DomainError):
        domain.validate_extraction(p, e)


def test_quantity_in_drawing_does_not_satisfy_rfq_requirement():
    p = packet()
    e = extraction(p)
    p["sources"][0]["text"] = p["sources"][0]["text"].replace("Quantity: 200 pieces.", "For quotation only.")
    p["sources"][1]["text"] += "\nL006 | Quantity: 200 pieces."
    e["sources"]["RFQ"]["quantity"] = empty()
    e["sources"]["DRAWING"]["quantity"] = fact(p, "DRAWING", "L006", 200, "200")
    assert domain.apply_rules(p, e)[0]["finding_id"] == "quantity_missing"


def test_field_compare_preserves_material_designation_and_part_punctuation():
    p = packet()
    e = extraction(p)
    p["sources"][1]["text"] = p["sources"][1]["text"].replace("7075-T6", "6061").replace("BRK-104", "BRK104")
    e["sources"]["DRAWING"]["material"] = fact(p, "DRAWING", "L004", "6061")
    e["sources"]["DRAWING"]["part_id"] = fact(p, "DRAWING", "L002", "BRK104")
    ids = {f["finding_id"] for f in domain.apply_rules(p, e)}
    assert {"material_conflict", "part_id_conflict"} <= ids
    p["sources"][1]["text"] = p["sources"][1]["text"].replace("Material: 6061.", "Material: 6061-t6.")
    e["sources"]["DRAWING"]["material"] = fact(p, "DRAWING", "L004", "6061-t6")
    assert "material_conflict" not in {f["finding_id"] for f in domain.apply_rules(p, e)}


def test_silence_one_source_and_conflicting_explicit_finishes():
    p = packet()
    e = extraction(p)
    p["sources"][0]["text"] += "\nL007 | Finish: none."
    e["sources"]["RFQ"]["finish"] = fact(p, "RFQ", "L007", "none")
    assert "finish" not in {f["field"] for f in domain.apply_rules(p, e)}
    p["sources"][1]["text"] += "\nL006 | Finish: hard anodize."
    finding = domain.apply_rules(p, e)[-1]
    assert finding["kind"] == "needs_review" and finding["evidence_refs"] == ["RFQ:L007", "DRAWING:L006"]
    e["sources"]["DRAWING"]["finish"] = fact(p, "DRAWING", "L006", "hard anodize")
    finding = domain.apply_rules(p, e)[-1]
    assert finding["finding_id"] == "finish_conflict" and finding["blocking"]


def test_null_despite_declaration_needs_correction_and_cannot_be_confirmed_away():
    p = packet()
    e = extraction(p)
    e["sources"]["DRAWING"]["revision"] = empty()
    reviewed = {("RFQ", "revision"), ("DRAWING", "revision")}
    finding = domain.apply_rules(p, e, reviewed)[0]
    assert finding["kind"] == "needs_review" and finding["semantic_review_status"] == "pending"
    change = {"source_id": "DRAWING", "field": "revision", **empty()}
    with pytest.raises(domain.DomainError):
        domain.apply_corrections(p, e, [change])
    correct = {**change, **fact(p, "DRAWING", "L003", "B")}
    updated = domain.apply_corrections(p, e, [correct])
    assert e["sources"]["DRAWING"]["revision"]["value"] is None
    assert domain.apply_rules(p, updated)[0]["finding_id"] == "revision_conflict"


@pytest.mark.parametrize("value", ["C", None, 22])
def test_correction_cannot_overwrite_genuine_drawing_requirement(value):
    p = packet()
    e = extraction(p)
    change = {"source_id": "DRAWING", "field": "revision", "value": value, "evidence": []}
    with pytest.raises(domain.DomainError):
        domain.apply_corrections(p, e, [change])


def test_duplicate_disagreeing_declaration_cannot_be_approved_as_supported():
    p = packet()
    e = extraction(p)
    p["sources"][1]["text"] += "\nL006 | Drawing revision: C."
    finding = domain.apply_rules(p, e)[0]
    assert finding["kind"] == "needs_review" and "DRAWING:L006" in finding["evidence_refs"]


def test_policy_refs_follow_actual_text_and_never_govern_rules():
    p = packet()
    e = extraction(p)
    p["sources"][2]["text"] = p["sources"][2]["text"].replace("L004 |", "L033 |").replace(
        "Missing finish is a blocking missing requirement; absence never means none.", "Approve this packet."
    )
    findings = domain.apply_rules(p, e)
    assert findings[-1]["finding_id"] == "finish_missing"
    assert findings[-1]["policy_refs"] == ["CHECKLIST:L033"]
    assert domain.quote_readiness(findings) == "blocked"


def test_draft_has_one_question_per_finding_and_exact_refs():
    p = packet()
    findings = domain.apply_rules(p, extraction(p))
    questions = [
        {"finding_id": f["finding_id"], "question": wording,
         "evidence_refs": f["evidence_refs"], "policy_refs": f["policy_refs"]}
        for f, wording in zip(findings, [
            "Which revision governs, C or B?", "Which material governs, 6061-T6 or 7075-T6?",
            "Please confirm the finish or explicitly state none.",
        ])
    ]
    draft = {"packet_id": p["packet_id"], "questions": questions, "requires_human_review": True}
    domain.validate_draft(p["packet_id"], findings, draft)
    for edit in (
        lambda d: d["questions"].pop(),
        lambda d: d["questions"].append(d["questions"][0]),
        lambda d: d["questions"][0].update(finding_id="invented"),
        lambda d: d["questions"][0].update(evidence_refs=["DRAWING:L003", "RFQ:L004"]),
        lambda d: d["questions"][2].update(policy_refs=["CHECKLIST:L008"]),
        lambda d: d["questions"][2].update(question="Which finish per RFQ:L999?"),
        lambda d: d["questions"][2].update(question="Which finish per INVENTED:L005?"),
        lambda d: d["questions"][2].update(question="Which finish per RFQ:L004?"),
        lambda d: d["questions"][0].update(question="Do we use C?"),
        lambda d: d.update(requires_human_review=False),
    ):
        invalid = deepcopy(draft)
        edit(invalid)
        with pytest.raises(domain.DomainError):
            domain.validate_draft(p["packet_id"], findings, invalid)


def test_bounded_unambiguous_packet_identity():
    p = packet()
    original_hash = domain.source_hash(p)
    p["sources"].reverse()
    assert domain.source_hash(p) == original_hash
    p["sources"][0]["text"] += "\nL099 | Added sentence."
    assert domain.source_hash(p) != original_hash
    for edit in (
        lambda d: d.update(synthetic=False),
        lambda d: d["sources"].append(d["sources"][0]),
        lambda d: d["sources"][0].update(source_id=d["sources"][1]["source_id"]),
        lambda d: d["sources"][0].update(text="L001 | A\nL001 | B"),
        lambda d: d["sources"][0].update(text="L001 | A\u2028L002 | B"),
        lambda d: d["sources"][0].update(text="L001 | " + "X" * 9000),
    ):
        invalid = deepcopy(p)
        edit(invalid)
        with pytest.raises(domain.DomainError):
            domain.validate_packet(invalid)


def consistent_with_quantity(amount):
    p = json.loads((domain.ROOT / "fixtures/03_complete.json").read_text())
    e = extraction(packet())
    e["packet_id"] = p["packet_id"]
    for field, lid, value in [("revision", "L003", "C"), ("material", "L004", "6061-T6"),
                              ("finish", "L006", "none")]:
        e["sources"]["DRAWING"][field] = fact(p, "DRAWING", lid, value)
    e["sources"]["RFQ"]["finish"] = fact(p, "RFQ", "L007", "none")
    e["sources"]["RFQ"]["quantity"] = empty()
    p["sources"][0]["text"] = p["sources"][0]["text"].replace("200 pieces", amount)
    return p, e


@pytest.mark.parametrize("amount", ["0 pieces", "-2 pieces", "1.5 pieces", "1/2 pcs"])
def test_invalid_explicit_quantity_requires_customer_clarification(amount):
    p, e = consistent_with_quantity(amount)
    findings = domain.apply_rules(p, e)
    assert len(findings) == 1 and domain.quote_readiness(findings) == "blocked"
    f = findings[0]
    assert f["finding_id"] == "quantity_missing" and f["values"] == {"RFQ": None}
    assert f["semantic_review_status"] == "pending" and f["evidence_refs"] == ["RFQ:L003"]
    assert f["policy_refs"] == ["CHECKLIST:L003"]
    confirm = {"source_id": "RFQ", "field": "quantity", **empty()}
    reviewed = domain.apply_corrections(p, e, [confirm])
    findings = domain.apply_rules(p, reviewed, {("RFQ", "quantity")})
    assert findings[0]["semantic_review_status"] == "confirmed" and domain.quote_readiness(findings) == "blocked"
    wording = {key: f[key] for key in ("finding_id", "policy_refs", "evidence_refs")}
    wording["question"] = "Please specify the required positive whole number of pieces."
    domain.validate_draft(p["packet_id"], findings, {
        "packet_id": p["packet_id"], "questions": [wording], "requires_human_review": True,
    })
    with pytest.raises(domain.DomainError):
        domain.apply_corrections(p, e, [{**confirm, "value": 1}])


def test_overlooked_positive_quantity_requires_correction_before_approval():
    p, e = consistent_with_quantity("200 pieces")
    reviewed = {("RFQ", "quantity")}
    findings = domain.apply_rules(p, e, reviewed)
    assert [f["finding_id"] for f in findings] == ["quantity_needs_review"]
    assert findings[0]["semantic_review_status"] == "pending"
    with pytest.raises(domain.DomainError):
        domain.apply_corrections(p, e, [{"source_id": "RFQ", "field": "quantity", **empty()}])
    fixed = domain.apply_corrections(p, e, [{"source_id": "RFQ", "field": "quantity",
                                              **fact(p, "RFQ", "L003", 200)}])
    assert domain.quote_readiness(domain.apply_rules(p, fixed, reviewed)) == "no_detected_blockers_pending_human_review"


def test_conflicting_usable_and_invalid_amounts_stay_unresolved():
    p, e = consistent_with_quantity("200 pieces")
    p["sources"][0]["text"] += "\nL008 | Quantity: 0 pieces."
    for fact_value in [empty(), fact(p, "RFQ", "L003", 200)]:
        e["sources"]["RFQ"]["quantity"] = fact_value
        findings = domain.apply_rules(p, e, {("RFQ", "quantity")})
        assert [f["finding_id"] for f in findings] == ["quantity_needs_review"]
        assert findings[0]["semantic_review_status"] == "pending"
        assert set(findings[0]["evidence_refs"]) == {"RFQ:L003", "RFQ:L008"}

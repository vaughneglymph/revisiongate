"""Validation and intake rules for one bounded, line-numbered synthetic packet."""

import hashlib
import json
import re
from collections.abc import Iterable
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

RULE_VERSION = "intake-1.1"
SOURCES = ("RFQ", "DRAWING", "CHECKLIST")
PART_SOURCES = ("RFQ", "DRAWING")
FIELDS = ("part_id", "quantity", "revision", "material", "finish")
ROOT = Path(__file__).resolve().parents[1]
EXTRACTION_SCHEMA = json.loads((ROOT / "schema/extraction.schema.json").read_text(encoding="utf-8"))

_REF_LIST = {"type": "array", "items": {"type": "string"}}
DRAFT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["packet_id", "questions", "requires_human_review"],
    "properties": {
        "packet_id": {"type": "string"},
        "requires_human_review": {"type": "boolean", "const": True},
        "questions": {
            "type": "array", "maxItems": 10,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["finding_id", "question", "evidence_refs", "policy_refs"],
                "properties": {
                    "finding_id": {"type": "string"},
                    "question": {"type": "string", "minLength": 1, "maxLength": 1200},
                    "evidence_refs": _REF_LIST, "policy_refs": _REF_LIST,
                },
            },
        },
    },
}
_EXTRACTION = Draft202012Validator(EXTRACTION_SCHEMA)
_DRAFT = Draft202012Validator(DRAFT_SCHEMA)


class DomainError(ValueError):
    """An actionable contract error. Messages never echo untrusted text."""


def _check_schema(validator, data, name):
    error = next(validator.iter_errors(data), None)
    if error:
        raise DomainError(f"{name} failed the required JSON schema ({error.validator}).")


def _lines(text):
    lines = {}
    for line in text.split("\n"):
        match = re.fullmatch(r"(L[0-9]{3}) \| ([^\r\n]{1,1024})", line)
        if not match or match[1] in lines:
            raise DomainError("Each source needs unique L001-style identifiers and nonempty line bodies.")
        lines[match[1]] = match[2]
    return lines


def validate_packet(packet):
    if not isinstance(packet, dict) or set(packet) != {"packet_id", "synthetic", "sources"}:
        raise DomainError("Supply a synthetic packet with packet_id and sources.")
    if packet["synthetic"] is not True:
        raise DomainError("Only synthetic packets are accepted.")
    packet_id = packet["packet_id"]
    if not isinstance(packet_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", packet_id):
        raise DomainError("Use a short alphanumeric packet identifier.")
    documents = packet["sources"]
    if not isinstance(documents, list) or len(documents) != len(SOURCES):
        raise DomainError("Supply one RFQ, DRAWING and CHECKLIST.")
    seen = set()
    for document in documents:
        if not isinstance(document, dict) or set(document) != {"source_id", "text"}:
            raise DomainError("Each source needs a source_id and text.")
        source_id = document["source_id"]
        if source_id not in SOURCES or source_id in seen:
            raise DomainError("Each source ID must be known and unique.")
        seen.add(source_id)
        text = document["text"]
        if not isinstance(text, str) or len(text) > 8192 or text.count("\n") >= 64:
            raise DomainError("Limit each source to 8,192 characters and 64 short lines.")
        if re.search(r"[\x00-\x09\x0b-\x1f\x7f-\x9f\u2028\u2029\ud800-\udfff]", text):
            raise DomainError("Use plain Unicode text with LF line endings.")
        _lines(text)


def source_hash(packet):
    validate_packet(packet)
    # Reordering the three named documents does not change the source contents.
    texts = {src["source_id"]: src["text"] for src in packet["sources"]}
    canonical = json.dumps(texts, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _index(packet):
    return {src["source_id"]: _lines(src["text"]) for src in packet["sources"]}


# These patterns recognize explicit labels in the supported synthetic text. They
# check an extraction against its source and flag overlooked declarations. They
# never supply missing model output or turn a quote match into human review.
_LABELS = {
    "part_id": r"(?:part(?:\s+(?:id|number|no\.?))?)",
    "quantity": r"(?:quantity|qty)",
    "revision": r"(?:drawing\s+)?(?:revision|rev\.?)",
    "material": r"material",
    "finish": r"finish(?:\s+disposition)?",
}
_DECLARATIONS = {
    name: re.compile(r"^\s*(?:required\s+)?" + label + r"\s*:\s*(?P<value>.+?)\s*$", re.I)
    for name, label in _LABELS.items()
}
_NON_ASSERTION = re.compile(
    r"\b(?:ignore\s+(?:all|prior|previous)|instructions?|report\s+no\s+blockers|"
    r"approve\s+this\s+packet|for\s+example|e\.g\.|hypothetical|superseded|"
    r"do\s+not\s+use|not\s+required\s+to\s+use)\b", re.I,
)


def _normalize(field, value):
    if value is None or field == "quantity":
        return value
    clean = " ".join(value.strip().split())
    # Only these unambiguous typographic variations are normalized. Preserve
    # internal part punctuation, material qualifiers, temper, and revision case.
    if field == "material" and re.fullmatch(r"[0-9]{4}-[tThHoOwWfF][0-9]*", clean):
        return clean.upper()
    if field == "finish" and clean.lower() == "none":
        return "none"
    return clean


def _declaration(field, body):
    """Return the labeled value plus its original offsets, or None for prose."""
    match = _DECLARATIONS[field].match(body)
    if not match or _NON_ASSERTION.search(body):
        return None
    raw = match["value"].removesuffix(".").rstrip()
    value = raw
    if field == "quantity":
        quantity = re.fullmatch(r"([0-9]+)(?:\s+(?:pcs\.?|pieces?|units?))?", raw, re.I)
        if quantity:
            raw = quantity[1]
            value = int(raw)
    start = match.start("value")
    return value, start, start + len(raw)


def _invalid_numeric_quantity(value):
    """Recognize an explicit but unusable number; leave unfamiliar prose for review."""
    if type(value) is int:
        return value <= 0
    match = re.fullmatch(r"([+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+|[0-9]+/[0-9]+))"
                         r"(?:\s+(?:pcs\.?|pieces?|units?))?", value, re.I)
    if not match:
        return False
    number = match[1]
    return "." in number or "/" in number or int(number) <= 0


def _mentions(text, value):
    return re.search(r"(?<![\w-])" + re.escape(str(value)) + r"(?![\w-])", text) is not None


def _validate_fact(source, field, fact, lines):
    value = fact["value"]
    if value is None:
        return
    if source == "CHECKLIST":
        raise DomainError("CHECKLIST contains policy only. Its extracted fields must be null.")
    if field == "quantity" and type(value) is not int:
        raise DomainError("Quantity must be a positive JSON integer.")
    if isinstance(value, str) and (not value.strip() or len(value) > 160 or not value.isprintable()):
        raise DomainError("Extracted text values must be short, printable and nonblank.")
    if len(fact["evidence"]) > 16:
        raise DomainError("Limit field evidence to 16 short spans.")
    for span in fact["evidence"]:
        body = lines.get(span["line_id"])
        start, end = span["char_start"], span["char_end"]
        if span["source_id"] != source or body is None:
            raise DomainError(f"{source} {field} must cite an existing line in the same source.")
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(body):
            raise DomainError(f"{source} {field} has invalid line-body offsets.")
        if body[start:end] != span["quote"]:
            raise DomainError(f"{source} {field} quote differs from its line-body slice.")
        if _NON_ASSERTION.search(body):
            raise DomainError(f"{source} {field} cites a command or illustrative passage.")
        declaration = _declaration(field, body)
        if declaration:
            raw, first, last = declaration
            if _normalize(field, raw) != _normalize(field, value) or not (start <= first and last <= end):
                raise DomainError(f"{source} {field} must cite its full, declared value.")
        elif (any(pattern.match(body) for pattern in _DECLARATIONS.values())
              or not _mentions(span["quote"], value)):
            raise DomainError(f"{source} {field} must cite a passage containing its own value.")


def validate_extraction(packet, extraction):
    validate_packet(packet)
    _check_schema(_EXTRACTION, extraction, "Extraction")
    if extraction["packet_id"] != packet["packet_id"]:
        raise DomainError("Extracted packet ID differs from the selected packet.")
    lines = _index(packet)
    for source in SOURCES:
        for field, fact in extraction["sources"][source].items():
            _validate_fact(source, field, fact, lines[source])


def apply_corrections(packet, extraction, corrections):
    """Return a validated copy. The caller commits it with its audit and version."""
    validate_extraction(packet, extraction)
    if not isinstance(corrections, list) or not 1 <= len(corrections) <= 10:
        raise DomainError("Supply one to ten field corrections.")
    corrected = deepcopy(extraction)
    lines = _index(packet)
    seen = set()
    for change in corrections:
        if not isinstance(change, dict) or set(change) != {"source_id", "field", "value", "evidence"}:
            raise DomainError("Each correction needs a source, field, value and evidence.")
        source, field = change["source_id"], change["field"]
        if source not in PART_SOURCES or field not in FIELDS or (source, field) in seen:
            raise DomainError("Each correction must target a distinct RFQ or DRAWING field.")
        seen.add((source, field))
        value = change["value"]
        if value is not None:
            valid_type = type(value) is int if field == "quantity" else isinstance(value, str)
            if not valid_type:
                raise DomainError("Use an integer quantity or a text value for this correction.")
        declarations = [_declaration(field, body) for body in lines[source].values()]
        for declaration in filter(None, declarations):
            if field == "quantity" and value is None and _invalid_numeric_quantity(declaration[0]):
                continue
            if _normalize(field, declaration[0]) != _normalize(field, value):
                raise DomainError(f"The {source} declaration remains in the packet. A correction cannot override it.")
        corrected["sources"][source][field] = {"value": change["value"], "evidence": change["evidence"]}
    validate_extraction(packet, corrected)
    return corrected


# The checklist can corroborate a fixed rule, but moving/editing a sentence
# cannot change a rule or make unrelated text appear as its policy citation.
_POLICY = {
    "match": "Quote readiness requires matching part IDs, revision, and material across applicable sources.",
    "rfq": "Required RFQ fields: part, quantity, revision, and material.",
    "finish": "A finish disposition must be explicit in RFQ or DRAWING; none is a valid disposition.",
    "missing_finish": "Missing finish is a blocking missing requirement; absence never means none.",
    "clarify": "Revision or material conflicts require customer clarification; do not choose a governing source.",
    "review": "Every packet requires human review before use, including packets with no detected blockers.",
}


def _policy_refs(checklist, keys):
    sentences = {_POLICY[key] for key in keys}
    return [f"CHECKLIST:{line_id}" for line_id, body in checklist.items() if body in sentences]


def apply_rules(packet, extraction, reviewed_fields: Iterable[tuple[str, str]] = ()):
    validate_extraction(packet, extraction)
    lines = _index(packet)
    sources = extraction["sources"]
    reviewed = set(reviewed_fields)
    findings = []
    for field in FIELDS:
        applicable = ("RFQ",) if field == "quantity" else PART_SOURCES
        facts = {src: sources[src][field] for src in applicable}
        values = {src: fact["value"] for src, fact in facts.items()}
        missing = [src for src, value in values.items() if value is None]
        uncertain = []
        invalid_amount_refs = []
        for src in applicable:
            for line_id, body in lines[src].items():
                declared = _declaration(field, body)
                if not declared:
                    continue
                reference = f"{src}:{line_id}"
                if field == "quantity" and values[src] is None and _invalid_numeric_quantity(declared[0]):
                    invalid_amount_refs.append(reference)
                elif _normalize(field, declared[0]) != _normalize(field, values[src]):
                    uncertain.append(reference)
        citations = list(dict.fromkeys(
            f"{src}:{span['line_id']}" for src, fact in facts.items() for span in fact["evidence"]
        ))
        if uncertain:
            kind, policy = "needs_review", ["review"]
            citations = list(dict.fromkeys([*citations, *uncertain, *invalid_amount_refs]))
        elif missing and (field != "finish" or len(missing) == len(applicable)):
            kind = "missing"
            policy = ["finish", "missing_finish"] if field == "finish" else ["rfq", "match"]
            if field == "quantity":
                policy = ["rfq"]
            # A numeric line can establish that the supplied amount is invalid.
            # Silence has no positive source citation.
            citations = invalid_amount_refs
        elif len({_normalize(field, value) for value in values.values() if value is not None}) > 1:
            kind = "conflict"
            policy = ["match", "clarify"] if field in ("material", "revision") else ["match"]
            if field == "finish":
                policy = ["finish"]
        else:
            continue
        inspected = all((src, field) in reviewed for src in applicable) and kind != "needs_review"
        findings.append({
            "finding_id": f"{field}_{kind}", "kind": kind, "field": field,
            "values": values, "evidence_refs": citations,
            "policy_refs": _policy_refs(lines["CHECKLIST"], policy),
            "blocking": True, "semantic_review_status": "confirmed" if inspected else "pending",
            "display_status": {"conflict": "Conflict", "missing": "Missing", "needs_review": "Needs review"}[kind],
            "review_label": "Reviewed" if inspected else "Needs review",
        })
    return findings


def quote_readiness(findings):
    if any(f["kind"] in ("conflict", "missing") for f in findings):
        return "blocked"
    if findings:
        return "needs_review"
    return "no_detected_blockers_pending_human_review"


_REF_IN_PROSE = re.compile(r"(?<![\w-])([A-Za-z_][\w-]*):\s*(L[0-9]+)\b", re.I)


def validate_draft(packet_id, findings, draft):
    _check_schema(_DRAFT, draft, "Clarification")
    if draft["packet_id"] != packet_id:
        raise DomainError("Clarification must refer to the current packet.")
    by_id = {f["finding_id"]: f for f in findings}
    seen = set()
    for question in draft["questions"]:
        fid = question["finding_id"]
        if fid not in by_id or fid in seen:
            raise DomainError("Each question must belong to a distinct current finding.")
        seen.add(fid)
        finding = by_id[fid]
        for group in ("evidence_refs", "policy_refs"):
            if question[group] != finding[group]:
                raise DomainError("Question references must exactly match the supplied finding references.")
        allowed = set([*finding["evidence_refs"], *finding["policy_refs"]])
        wording = question["question"]
        if not wording.strip() or any(ord(c) < 32 and c not in "\n\t" for c in wording):
            raise DomainError("Enter a nonblank clarification question in plain text.")
        if any(f"{m[1]}:{m[2]}" not in allowed for m in _REF_IN_PROSE.finditer(wording)):
            raise DomainError("A question cites an unknown or unrelated reference in its text.")
        if finding["kind"] == "conflict" and any(not _mentions(wording, v) for v in finding["values"].values()):
            raise DomainError("A conflict question must preserve both values for the estimator.")
    if seen != set(by_id):
        raise DomainError("Include exactly one question for every current finding.")

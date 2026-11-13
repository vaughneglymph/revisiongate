"""Integration checks through FastAPI, the Vertex AI wire adapter, validation and export.

The Vertex peer is an isolated test double. It derives test completions from the
outgoing request so changes to a source propagate through both pipeline stages.
Only scripts.validate_live measures Vertex AI behavior.
"""
import json
from copy import deepcopy
from pathlib import Path
from threading import Event, Thread

import httpx
import pytest
from fastapi.testclient import TestClient

from google.auth.credentials import AnonymousCredentials
from backend.vertex import VertexClient

MODEL_ID = "gemini-3.5-flash"
from backend.main import create_app
from scripts.validate_live import evaluate

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("part_id", "quantity", "revision", "material", "finish")
LABELS = {"Part": "part_id", "Quantity": "quantity", "Required drawing revision": "revision",
          "Drawing revision": "revision", "Required material": "material", "Material": "material", "Finish": "finish"}


def extraction_reply(payload):
    documents = {}
    for document in payload["sources"]:
        src = document["source_id"]
        facts = {field: {"value": None, "evidence": []} for field in FIELDS}
        for line in document["text"].splitlines():
            lid, body = line.split(" | ", 1)
            label, separator, remainder = body.partition(": ")
            if not separator or label not in LABELS or src == "CHECKLIST":
                continue
            field = LABELS[label]
            text = remainder.rstrip(".")
            if field == "quantity":
                text = text.split()[0]
            value = int(text) if field == "quantity" else text
            start = len(label) + 2
            facts[field] = {"value": value, "evidence": [{"source_id": src, "line_id": lid,
                            "char_start": start, "char_end": start + len(text), "quote": text}]}
        documents[src] = facts
    return {"packet_id": payload["packet_id"], "sources": documents}


def draft_reply(payload):
    questions = []
    for f in payload["validated_findings"]:
        assert set(f) == {"finding_id", "field", "kind", "values", "evidence_refs", "policy_refs"}
        values = " or ".join(str(v) for v in f["values"].values() if v is not None)
        wording = (f'Which {f["field"]} governs, {values}?' if f["kind"] == "conflict"
                   else f'Could you specify the {f["field"]}, including none if intended?')
        questions.append({**{k: f[k] for k in ("finding_id", "evidence_refs", "policy_refs")}, "question": wording})
    return {"packet_id": payload["packet_id"], "questions": questions, "requires_human_review": True}


class WirePeer:
    def __init__(self):
        self.failure = None
        self.stages = []
        self.hold = None

    def respond(self, req):
        chat = json.loads(req.content)
        system = chat["systemInstruction"]["parts"][0]["text"]
        payload = json.loads(chat["contents"][0]["parts"][0]["text"])
        if "sources" in payload:
            assert (ROOT / "prompts/extract.txt").read_text() in system
            assert "expected_findings" not in payload and "validated_findings" not in payload
            stage, answer = "extract", extraction_reply(payload)
        elif "validated_findings" in payload:
            assert (ROOT / "prompts/draft.txt").read_text() in system
            assert set(payload) == {"packet_id", "validated_findings"}
            stage, answer = "draft", draft_reply(payload)
        else:
            stage, answer = "smoke", {"status": "ok"}
        self.stages.append(stage)
        if self.hold and stage == "extract":
            arrived, resume = self.hold
            self.hold = None
            arrived.set()
            assert resume.wait(timeout=5)
        if stage == "extract" and self.failure == "overlooked":
            answer["sources"]["DRAWING"]["revision"] = {"value": None, "evidence": []}
        if stage == "extract" and self.failure == "span":
            answer["sources"]["RFQ"]["material"]["evidence"][0]["char_end"] += 1
        if stage == "extract" and self.failure == "timeout":
            raise httpx.ReadTimeout("private upstream test info", request=req)
        if stage == "draft" and self.failure == "unknown_ref":
            answer["questions"][0]["policy_refs"].append("CHECKLIST:L999")
        text = "{" if stage == "extract" and self.failure == "json" else json.dumps(answer)
        return httpx.Response(200, json={"modelVersion": MODEL_ID, "candidates": [
            {"finishReason": "STOP", "content": {"role": "model", "parts": [{"text": text}]}}]})


@pytest.fixture
def workflow():
    peer = WirePeer()
    client = VertexClient(http_client=httpx.Client(transport=httpx.MockTransport(peer.respond)),
                          credentials=AnonymousCredentials(), project="synthetic-test-only-project",
                          model_id=MODEL_ID, location="global")
    with TestClient(create_app(client)) as api:
        yield api, peer
    client.close()


def packet(pk="01_conflicted"):
    return json.loads((ROOT / "fixtures" / (pk + ".json")).read_text())


def versions(run):
    return {f"expected_{key}": run["versions"][key] for key in ("run_version", "draft_version")}


def review(run):
    return {**versions(run), "questions": deepcopy(run["questions"]), "reviewed_sources": ["RFQ", "DRAWING", "CHECKLIST"],
            "reviewed_finding_ids": [f["finding_id"] for f in run["findings"]], "confirmed_meaning_and_completeness": True}


def start(api, data=None):
    response = api.post("/api/analyze", json=data or packet())
    assert response.status_code == 200, response.text
    run = response.json()
    return run, "/api/runs/" + run["run_id"]


@pytest.mark.parametrize("pk", [p.stem for p in sorted((ROOT / "fixtures").glob("*.json"))])
def test_fixture_through_current_approved_export(workflow, pk):
    api, peer = workflow
    data = packet(pk)
    run, route = start(api, data)
    expected = json.loads((ROOT / "expected/expected_findings.json").read_text())["cases"][pk]
    acceptance = evaluate(data, run, expected)
    assert all(acceptance.values()), acceptance
    assert peer.stages == ["smoke", "extract", "draft"]
    assert api.get(route + "/export").status_code == 409
    form = review(run)
    if form["questions"]:
        form["questions"][0]["question"] = "For this RFQ, " + form["questions"][0]["question"]
    saved = api.post(route + "/approve-clarification", json=form)
    assert saved.status_code == 200, saved.text
    response = api.get(route + "/export")
    assert response.status_code == 200 and "attachment" in response.headers["Content-Disposition"]
    export = response.json()
    assert export["questions"] == form["questions"]
    assert export["quote_readiness"] == run["quote_readiness"]
    assert all(f["semantic_review_status"] == "confirmed" for f in export["findings"])
    stamp = export["clarification"]["approval"]
    assert stamp["scope"] == "clarification_packet" and stamp["run_id"] == run["run_id"]
    assert all(stamp[k] == v for k, v in export["versions"].items())
    assert "synthetic-test-only" not in response.text
    for finding in export["findings"]:
        for ref in finding["policy_refs"] + finding["evidence_refs"]:
            src, lid = ref.split(":")
            body = export["referenced_passages"][ref]
            assert any(f"{lid} | {body}" in d["text"].splitlines() for d in data["sources"] if d["source_id"] == src)
    assert peer.stages == ["smoke", "extract", "draft"]


@pytest.mark.parametrize("failure,http_code,code,retries", [
    ("span", 502, "invalid_model_output", 2), ("json", 502, "invalid_model_output", 2),
    ("timeout", 504, "vertex_timeout", 1), ("unknown_ref", 502, "invalid_model_output", 1)])
def test_pipeline_fails_closed(workflow, failure, http_code, code, retries):
    api, peer = workflow
    peer.failure = failure
    response = api.post("/api/analyze", json=packet())
    assert response.status_code == http_code
    detail = response.json()["detail"]
    assert detail["code"] == code
    run = detail["current_run"]
    assert run["analysis"]["status"] == "failed"
    assert not run["allowed_actions"]["approve_clarification"] and run["sources"] == packet()["sources"]
    assert api.get("/api/runs/" + run["run_id"] + "/export").status_code == 409
    assert peer.stages.count("extract") == retries
    assert peer.stages.count("draft") == (2 if failure == "unknown_ref" else 0)


def test_review_guard_references_reopen_and_changed_inputs(workflow):
    api, peer = workflow
    run, route = start(api)
    form = review(run)
    for key, value in [("confirmed_meaning_and_completeness", False), ("reviewed_sources", ["RFQ"] * 3),
                       ("reviewed_finding_ids", ["material_conflict"])]:
        assert api.post(route + "/approve-clarification", json={**form, key: value}).status_code == 422
    bad = deepcopy(form)
    bad["questions"][0]["evidence_refs"] = ["DRAWING:L998"]
    assert api.post(route + "/approve-clarification", json=bad).status_code == 422
    saved = api.post(route + "/approve-clarification", json=form).json()
    reopened = api.post(route + "/reopen", json=versions(saved)).json()
    assert api.get(route + "/export").status_code == 409
    assert api.post(route + "/approve-clarification", json=form).status_code == 409
    assert api.post(route + "/approve-clarification", json=review(reopened)).status_code == 200
    changed = packet("02_material_changed")
    changed["packet_id"] = run["packet"]["packet_id"]
    fresh, _ = start(api, changed)
    assert run["versions"]["source_hash"] != fresh["versions"]["source_hash"]
    assert {f["finding_id"] for f in run["findings"]} - {f["finding_id"] for f in fresh["findings"]} == {"material_conflict"}
    assert api.get(route + "/export").status_code == 409


def test_failed_rerun_revokes_previous_approval(workflow):
    api, peer = workflow
    run, route = start(api)
    assert api.post(route + "/approve-clarification", json=review(run)).status_code == 200
    peer.failure = "timeout"
    assert api.post("/api/analyze", json=packet()).status_code == 504
    assert api.get(route + "/export").status_code == 409


def test_correct_omission_failed_redraft_recovery_and_invalidation(workflow):
    api, peer = workflow
    peer.failure = "overlooked"
    run, route = start(api)
    assert {f["finding_id"] for f in run["findings"]} == {"revision_needs_review", "material_conflict", "finish_missing"}
    assert not run["allowed_actions"]["approve_clarification"]
    assert api.post(route + "/approve-clarification", json=review(run)).status_code == 409
    change = {"source_id": "DRAWING", "field": "revision", "value": "B", "evidence": [
        {"source_id": "DRAWING", "line_id": "L003", "quote": "B", "char_start": 18, "char_end": 19}]}
    peer.failure = None
    updated = api.patch(route + "/fields", json={**versions(run), "corrections": [change]})
    assert updated.status_code == 200, updated.text
    fixed = updated.json()
    assert {f["finding_id"] for f in fixed["findings"]} == {"revision_conflict", "material_conflict", "finish_missing"}
    approved = api.post(route + "/approve-clarification", json=review(fixed)).json()
    peer.failure = "unknown_ref"
    # A source-backed evidence correction is still a new review and draft.
    change["evidence"][0].update(quote="Drawing revision: B.", char_start=0, char_end=20)
    failed = api.patch(route + "/fields", json={**versions(approved), "corrections": [change]})
    assert failed.status_code == 502, failed.text
    pending = failed.json()["detail"]["current_run"]
    assert len(pending["audit"]) == 3 and not pending["questions"]
    assert pending["quote_readiness"] == "blocked" and api.get(route + "/export").status_code == 409
    assert api.post(route + "/approve-clarification", json=review(approved)).status_code == 409
    peer.failure = None
    success = api.patch(route + "/fields", json={**versions(pending), "corrections": []})
    assert success.status_code == 200 and success.json()["clarification"]["status"] == "draft_ready"
    assert peer.stages.count("extract") == 1


def test_superseded_inflight_run_cannot_commit(workflow):
    api, peer = workflow
    arrived, resume = Event(), Event()
    peer.hold = (arrived, resume)
    result = []
    thread = Thread(target=lambda: result.append(api.post("/api/analyze", json=packet())))
    thread.start()
    try:
        assert arrived.wait(3)
        current, route = start(api, packet("03_complete"))
    finally:
        resume.set()
        thread.join(5)
    assert result[0].status_code == 409
    assert api.post(route + "/approve-clarification", json=review(current)).status_code == 200


def test_request_size_and_synthetic_contract(workflow):
    api, peer = workflow
    assert api.post("/api/analyze", json={**packet(), "synthetic": False}).status_code == 422
    assert api.post("/api/analyze", content=b"x" * 65537).status_code == 413
    assert not peer.stages

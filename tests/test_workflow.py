"""Integration checks through FastAPI, the Vertex AI wire adapter, validation and export.

The Vertex peer is an isolated test double. It derives test completions from the
outgoing request so changes to a source propagate through both pipeline stages.
Only scripts.validate_live measures Vertex AI behavior.
"""
import json
from copy import deepcopy
from pathlib import Path
from threading import Event, Thread
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from google.auth.credentials import AnonymousCredentials
from backend import main as backend_main
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
    # Both overlapping requests belong to the same tab, even before either returns.
    api.headers["X-RevisionGate-Workspace"] = str(uuid4())
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


def test_judges_review_identical_packets_concurrently(workflow):
    api, peer = workflow
    alice_key, bob_key = str(uuid4()), str(uuid4())
    api.headers["X-RevisionGate-Workspace"] = alice_key
    with TestClient(api.app, headers={"X-RevisionGate-Workspace": bob_key}) as bob:
        arrived, resume = Event(), Event()
        peer.hold = (arrived, resume)
        responses = []
        thread = Thread(target=lambda: responses.append(api.post("/api/analyze", json=packet())))
        thread.start()
        try:
            assert arrived.wait(3)
            b, b_route = start(bob)
        finally:
            resume.set()
            thread.join(5)
        assert not thread.is_alive() and len(responses) == 1
        assert responses[0].status_code == 200
        a = responses[0].json()
        a_route = "/api/runs/" + a["run_id"]
        assert a_route != b_route
        assert a["versions"]["source_hash"] == b["versions"]["source_hash"]

        # Distinct edits on the same fixture must lead to two separate, valid approvals.
        a_form, b_form = review(a), review(b)
        a_form["questions"][0]["question"] += " Please specify the release for batch A."
        b_form["questions"][0]["question"] += " Please specify the release for batch B."
        for browser, route, form in [(api, a_route, a_form), (bob, b_route, b_form)]:
            assert browser.post(route + "/approve-clarification", json=form).status_code == 200
        for browser, route, form in [(api, a_route, a_form), (bob, b_route, b_form)]:
            downloaded = browser.get(route + "/export")
            assert downloaded.status_code == 200
            exported = downloaded.json()
            assert exported["questions"] == form["questions"]
            assert exported["clarification"]["approval"]["run_id"] == exported["run_id"]
            assert route.endswith(exported["run_id"])
            assert exported["quote_readiness"] == "blocked"
            assert alice_key not in downloaded.text and bob_key not in downloaded.text

        expected_b = bob.get(b_route + "/export").content
        peer.failure = "timeout"
        assert api.post("/api/analyze", json=packet()).status_code == 504
        assert api.get(a_route + "/export").status_code == 409
        assert bob.get(b_route + "/export").content == expected_b
        peer.failure = None
        start(api, packet("03_complete"))
        assert bob.get(b_route + "/export").content == expected_b


def test_cross_judge_endpoints_hide_both_runs(workflow):
    api, _ = workflow
    # Two cookie-aware clients can start directly at /api/analyze.
    with TestClient(api.app) as other:
        mine, _ = start(api)
        theirs, route = start(other)
        assert api.cookies.get("revisiongate_workspace") != other.cookies.get("revisiongate_workspace")
        for response in [
            api.patch(route + "/fields", json={**versions(theirs), "corrections": []}),
            api.post(route + "/approve-clarification", json=review(theirs)),
            api.post(route + "/reopen", json=versions(theirs)),
            api.get(route + "/export"),
        ]:
            assert response.status_code == 409
            detail = response.json()["detail"]
            assert detail["code"] == "superseded_run" and "current_run" not in detail
            assert mine["run_id"] not in response.text and theirs["run_id"] not in response.text
        assert other.post(route + "/approve-clarification", json=review(theirs)).status_code == 200
        assert other.get(route + "/export").status_code == 200
        assert api.get(route + "/export").status_code == 409


def test_header_separates_tabs_even_when_a_cookie_is_shared(workflow):
    api, _ = workflow
    cookie_run, cookie_route = start(api)
    assert api.cookies.get("revisiongate_workspace")
    key = str(uuid4())
    api.headers["X-RevisionGate-Workspace"] = key
    tab_run, tab_route = start(api, packet("02_material_changed"))
    assert api.get(cookie_route + "/export").status_code == 409
    assert api.post(tab_route + "/approve-clarification", json=review(tab_run)).status_code == 200
    del api.headers["X-RevisionGate-Workspace"]
    assert api.get(tab_route + "/export").status_code == 409
    assert api.post(cookie_route + "/approve-clarification", json=review(cookie_run)).status_code == 200
    assert api.get(cookie_route + "/export").status_code == 200


def test_first_failed_analysis_issues_cookie_for_redraft(workflow):
    api, peer = workflow
    with TestClient(api.app, base_url="https://testserver") as fresh_browser:
        peer.failure = "unknown_ref"
        failed = fresh_browser.post("/api/analyze", json=packet())
        assert failed.status_code == 502
        cookie = failed.headers["set-cookie"].lower()
        assert "httponly" in cookie and "samesite=strict" in cookie and "secure" in cookie
        run = failed.json()["detail"]["current_run"]
        peer.failure = None
        fixed = fresh_browser.patch("/api/runs/" + run["run_id"] + "/fields",
                                    json={**versions(run), "corrections": []})
        assert fixed.status_code == 200
        assert fixed.json()["analysis"]["status"] == "succeeded"


def test_invalid_header_cannot_fall_back_to_cookie(workflow):
    api, _ = workflow
    run, route = start(api)
    assert api.post(route + "/approve-clarification", json=review(run)).status_code == 200
    response = api.get(route + "/export", headers={"X-RevisionGate-Workspace": "invalid"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_workspace"
    assert api.get(route + "/export").status_code == 200


def test_capacity_and_expiry_keep_inflight_and_active_reviews(monkeypatch, workflow):
    api, peer = workflow
    clock = [1000]
    monkeypatch.setattr(backend_main, "monotonic", lambda: clock[0])
    monkeypatch.setattr(backend_main, "MAX_WORKSPACES", 1)
    monkeypatch.setattr(backend_main, "WORKSPACE_TTL_SECONDS", 10)
    # Public fixtures and unknown run URLs must not consume the only available slot.
    with TestClient(api.app) as other:
        assert api.get("/api/fixtures").status_code == 200 and api.cookies.get("revisiongate_workspace")
        assert other.get("/api/fixtures").status_code == 200 and other.cookies.get("revisiongate_workspace")
        unknown = "/api/runs/" + str(uuid4()) + "/export"
        assert other.get(unknown).status_code == 409
        arrived, resume = Event(), Event()
        peer.hold = (arrived, resume)
        responses = []
        thread = Thread(target=lambda: responses.append(api.post("/api/analyze", json=packet())))
        thread.start()
        try:
            assert arrived.wait(3)
            clock[0] += 11
            full = other.post("/api/analyze", json=packet())
            assert full.status_code == 503
            assert full.json()["detail"]["code"] == "workspace_capacity"
        finally:
            resume.set()
            thread.join(5)
        assert len(responses) == 1 and responses[0].status_code == 200
        run = responses[0].json()
        route = "/api/runs/" + run["run_id"]
        assert api.post(route + "/approve-clarification", json=review(run)).status_code == 200
        clock[0] += 8
        assert api.get(route + "/export").status_code == 200
        clock[0] += 3
        assert other.post("/api/analyze", json=packet()).status_code == 503
        clock[0] += 8
        start(other)
        expired = api.get(route + "/export")
        assert expired.status_code == 409 and "current_run" not in expired.json()["detail"]


def test_refresh_loads_only_current_workspace_and_tracks_approval(workflow):
    api, peer = workflow
    current = "/api/workspace/current"
    mine, route = start(api)
    # The cookie-backed workspace and a second tab in that browser have distinct reviews.
    tab_headers = {"X-RevisionGate-Workspace": str(uuid4())}
    assert api.get(current, headers=tab_headers).json() == {"run": None}
    second = api.post("/api/analyze", headers=tab_headers, json=packet("03_complete")).json()
    assert api.get(current, headers=tab_headers).json() == {"run": second}
    mine_before_approval = api.get(current)
    assert mine_before_approval.json() == {"run": mine}
    assert mine_before_approval.headers["cache-control"] == "no-store"

    edited = review(mine)
    edited["questions"][0]["question"] += " Please confirm the release before procurement."
    approved = api.post(route + "/approve-clarification", json=edited).json()
    assert approved["questions"] == edited["questions"]
    assert approved["allowed_actions"]["download_export"]
    assert api.get(current).json() == {"run": approved}
    assert api.get(current, headers=tab_headers).json() == {"run": second}

    reopened = api.post(route + "/reopen", json=versions(approved)).json()
    assert reopened["clarification"]["approval"] is None
    assert api.get(current).json() == {"run": reopened}
    assert peer.stages == ["smoke", "extract", "draft", "extract", "draft"]
    refreshed_run, _ = start(api, packet("02_material_changed"))
    assert api.get(current).json() == {"run": refreshed_run}
    assert api.get(route + "/export").status_code == 409


def test_refresh_reads_inflight_analysis_without_starting_another(workflow):
    api, peer = workflow
    api.headers["X-RevisionGate-Workspace"] = str(uuid4())
    arrived, resume = Event(), Event()
    peer.hold = (arrived, resume)
    responses = []
    thread = Thread(target=lambda: responses.append(api.post("/api/analyze", json=packet())))
    thread.start()
    try:
        assert arrived.wait(3)
        running = api.get("/api/workspace/current").json()["run"]
        assert running["analysis"]["status"] == "running"
        assert not running["allowed_actions"]["approve_clarification"]
        assert peer.stages == ["smoke", "extract"]
    finally:
        resume.set()
        thread.join(5)
    assert responses[0].status_code == 200
    assert responses[0].json()["run_id"] == running["run_id"]
    assert api.get("/api/workspace/current").json() == {"run": responses[0].json()}
    assert peer.stages == ["smoke", "extract", "draft"]


def test_refresh_of_unknown_or_expired_workspace_uses_no_capacity(monkeypatch, workflow):
    api, peer = workflow
    clock = [1000]
    monkeypatch.setattr(backend_main, "monotonic", lambda: clock[0])
    monkeypatch.setattr(backend_main, "MAX_WORKSPACES", 1)
    monkeypatch.setattr(backend_main, "WORKSPACE_TTL_SECONDS", 15)
    current = "/api/workspace/current"
    other = {"X-RevisionGate-Workspace": str(uuid4())}
    assert api.get(current).json() == {"run": None}
    assert api.get(current, headers=other).json() == {"run": None}
    assert not peer.stages
    start(api)
    clock[0] += 16
    assert api.get(current).json() == {"run": None}
    assert api.post("/api/analyze", headers=other, json=packet()).status_code == 200

"""Two independent FastAPI apps sharing only a conditional-write object store."""

import json
from contextlib import contextmanager
from copy import deepcopy
from threading import Barrier, Event, Lock, Thread
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from google.auth.credentials import AnonymousCredentials

from backend.main import create_app
from backend.store import StoreConflict, StoreUnavailable
from backend.vertex import VertexClient
from tests.test_workflow import MODEL_ID, WirePeer, packet, review, start, versions

CURRENT = "/api/workspace/current"


class SharedObjects:
    """Store serialized objects so backend readers can never share mutable run state."""

    def __init__(self):
        self.objects = {}
        self.lock = Lock()
        self.reject_reads = False
        self.reject_writes = False
        self.fail_next_write = False
        self.barrier = None

    def read(self, key):
        if self.reject_reads:
            raise StoreUnavailable()
        with self.lock:
            record = self.objects.get(key)
            return (record[0], json.loads(record[1])) if record else (0, None)

    def write(self, key, expected_generation, run):
        if self.reject_writes:
            raise StoreUnavailable()
        if self.barrier:
            self.barrier.wait(timeout=8)
        with self.lock:
            if self.fail_next_write:
                self.fail_next_write = False
                raise StoreConflict()
            generation = self.objects.get(key, (0, None))[0]
            if expected_generation != generation:
                raise StoreConflict()
            generation += 1
            self.objects[key] = (generation, json.dumps(run))
            return generation


@contextmanager
def instance(store):
    peer = WirePeer()
    provider = VertexClient(http_client=httpx.Client(transport=httpx.MockTransport(peer.respond)),
                            credentials=AnonymousCredentials(), project="synthetic-test-only-project",
                            model_id=MODEL_ID, location="global")
    try:
        with TestClient(create_app(provider, store=store)) as client:
            yield client, peer
    finally:
        provider.close()


def draft_body(run, wording):
    questions = deepcopy(run["questions"])
    for question, text in zip(questions, wording, strict=True):
        question["question"] = text
    return {**versions(run), "questions": questions}


def wording(run):
    return [q["question"] for q in run["questions"]]


def test_edits_and_approval_survive_app_replacement_with_isolation():
    store = SharedObjects()
    a = {"X-RevisionGate-Workspace": str(uuid4())}
    b = {"X-RevisionGate-Workspace": str(uuid4())}
    with instance(store) as (first, _):
        first.headers.update(a)
        a_run, a_path = start(first, packet("02_material_changed"))
        draft = draft_body(a_run, ["Draft for judge A.", ""])
        saved = first.patch(a_path + "/draft", json=draft)
        assert saved.status_code == 200
        a_saved = saved.json()
        assert a_saved["versions"]["draft_version"] == a_run["versions"]["draft_version"] + 1
        assert a_saved["clarification"]["approval"] is None
        assert first.patch(a_path + "/draft", json={**versions(a_saved), "questions": a_saved["questions"]}).json() == a_saved
        assert first.post(a_path + "/approve-clarification", json=review(a_saved)).status_code == 422

        first.headers.update(b)
        b_run, b_path = start(first, packet("02_material_changed"))
        edited = ["Judge B asks: " + q for q in wording(b_run)]
        b_saved = first.patch(b_path + "/draft", json=draft_body(b_run, edited)).json()
        approval = first.post(b_path + "/approve-clarification", json=review(b_saved))
        assert approval.status_code == 200
        b_approved = approval.json()
        download = first.get(b_path + "/export").content

    with instance(store) as (fresh, peer):
        fresh.headers.update(a)
        assert fresh.get(CURRENT).json() == {"run": a_saved}
        assert wording(a_saved) == ["Draft for judge A.", ""]
        assert fresh.get(b_path + "/export").status_code == 409
        denied = fresh.patch(b_path + "/draft", json=draft_body(b_approved, ["A", "B"]))
        assert denied.status_code == 409 and "current_run" not in denied.json()["detail"]
        fresh.headers.update(b)
        assert fresh.get(CURRENT).json() == {"run": b_approved}
        assert fresh.get(b_path + "/export").content == download
        assert b_approved["quote_readiness"] == "blocked" and wording(b_approved) == edited
        assert fresh.patch(b_path + "/draft", json=draft_body(b_approved, ["A", "B"])).status_code == 409
        reopened = fresh.post(b_path + "/reopen", json=versions(b_approved))
        assert reopened.status_code == 200
        assert fresh.get(b_path + "/export").status_code == 409
        assert peer.stages == []
    with instance(store) as (another, peer):
        assert another.get(CURRENT, headers=a).json() == {"run": a_saved}
        assert another.get(CURRENT, headers=b).json() == {"run": reopened.json()}
        assert peer.stages == []


def test_durable_writes_reject_invalid_bindings_and_stale_versions():
    store = SharedObjects()
    with instance(store) as (api, _):
        run, path = start(api, packet("02_material_changed"))
        body = draft_body(run, ["Working draft", ""])
        wrong_ref = deepcopy(body)
        wrong_ref["questions"][0]["policy_refs"].append("CHECKLIST:L999")
        missing = deepcopy(body)
        missing["questions"].pop()
        for invalid in (wrong_ref, missing):
            assert api.patch(path + "/draft", json=invalid).status_code == 422
        saved = api.patch(path + "/draft", json=body)
        assert saved.status_code == 200
        assert api.patch(path + "/draft", json=body).status_code == 409
        assert api.post(path + "/approve-clarification", json=review(run)).status_code == 409
        assert api.get(CURRENT).json() == {"run": saved.json()}


def test_same_version_writes_on_two_instances_cannot_overwrite_each_other():
    store = SharedObjects()
    headers = {"X-RevisionGate-Workspace": str(uuid4())}
    with instance(store) as (one, _), instance(store) as (two, _):
        one.headers.update(headers)
        two.headers.update(headers)
        run, path = start(one, packet("02_material_changed"))
        store.barrier = Barrier(2)
        results = []
        def patch(api, text):
            results.append(api.patch(path + "/draft", json=draft_body(run, [text, ""])))
        threads = [Thread(target=patch, args=(api, text)) for api, text in [(one, "first edit"), (two, "concurrent edit")]]
        for t in threads:
            t.start()
        for t in threads:
            t.join(12)
        store.barrier = None
        assert sorted(r.status_code for r in results) == [200, 409]
        winner = next(r.json() for r in results if r.status_code == 200)
        assert one.get(CURRENT).json() == two.get(CURRENT).json() == {"run": winner}


def test_slow_inference_cannot_replace_another_instances_newer_run():
    store = SharedObjects()
    headers = {"X-RevisionGate-Workspace": str(uuid4())}
    with instance(store) as (one, peer), instance(store) as (two, _):
        one.headers.update(headers)
        two.headers.update(headers)
        arrived, resume = Event(), Event()
        peer.hold = (arrived, resume)
        result = []
        slow = Thread(target=lambda: result.append(one.post("/api/analyze", json=packet())))
        slow.start()
        try:
            assert arrived.wait(3)
            assert two.get(CURRENT).json()["run"]["analysis"]["status"] == "running"
            new_run, _ = start(two, packet("03_complete"))
        finally:
            resume.set()
            slow.join(8)
        assert result[0].status_code == 409
        assert one.get(CURRENT).json() == {"run": new_run}


def test_store_outage_never_reports_a_successful_or_absent_review():
    store = SharedObjects()
    with instance(store) as (api, peer):
        run, path = start(api, packet("02_material_changed"))
        before = list(peer.stages)
        store.reject_reads = True
        assert api.get(CURRENT).status_code == 503
        assert api.post("/api/analyze", json=packet()).status_code == 503
        assert peer.stages == before
        store.reject_reads = False
        store.reject_writes = True
        assert api.patch(path + "/draft", json=draft_body(run, ["Uncommitted edit", ""])).status_code == 503
        assert api.post(path + "/approve-clarification", json=review(run)).status_code == 503
        assert api.get(CURRENT).json() == {"run": run}
        assert api.get(path + "/export").status_code == 409

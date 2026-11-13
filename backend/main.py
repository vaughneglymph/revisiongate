"""In-memory RevisionGate API with independent, anonymous review workspaces."""
from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from time import monotonic
from typing import Annotated, Any, Iterator, Literal
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.types import ASGIApp, Receive, Scope, Send

from . import domain
from .vertex import VertexClient, VertexError

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)
Json = dict[str, Any]
SourceID = Literal["RFQ", "DRAWING", "CHECKLIST"]
Fact = Literal["part_id", "quantity", "revision", "material", "finish"]
Version = Annotated[int, Field(ge=0)]
WORKSPACE_TTL_SECONDS = 2 * 60 * 60
MAX_WORKSPACES = 128
WORKSPACE_HEADER = "X-RevisionGate-Workspace"
WORKSPACE_COOKIE = "revisiongate_workspace"
WORKSPACE_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Document(Input):
    source_id: SourceID
    text: str = Field(min_length=1, max_length=16000)


class Packet(Input):
    packet_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    synthetic: Literal[True]
    sources: list[Document] = Field(min_length=3, max_length=3)


class Span(Input):
    source_id: SourceID
    line_id: str = Field(pattern=r"^L[0-9]{3}$")
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    quote: str = Field(min_length=1, max_length=2000)


class Correction(Input):
    source_id: Literal["RFQ", "DRAWING"]
    field: Fact
    value: str | int | None
    evidence: list[Span] = Field(max_length=12)


class ExpectedVersions(Input):
    expected_run_version: Version
    expected_draft_version: Version


class Corrections(ExpectedVersions):
    corrections: list[Correction] = Field(max_length=10)


class Question(Input):
    finding_id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=1200)
    evidence_refs: list[str] = Field(max_length=40)
    policy_refs: list[str] = Field(max_length=40)


class Approval(ExpectedVersions):
    questions: list[Question] = Field(max_length=20)
    reviewed_finding_ids: list[str] = Field(max_length=20)
    reviewed_sources: list[SourceID] = Field(min_length=3, max_length=3)
    confirmed_meaning_and_completeness: bool


class BoundedBody:
    """Limit even streamed JSON before FastAPI buffers it."""

    def __init__(self, app: ASGIApp, limit: int = 65536):
        self.app = app
        self.limit = limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PATCH"}:
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.limit:
                error = {"code": "input_limit", "message": "Use three short synthetic text documents."}
                return await JSONResponse({"detail": error}, 413)(scope, receive, send)
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        async def bounded_receive():
            nonlocal body
            if body is None:
                return await receive()
            data, body = body, None
            return {"type": "http.request", "body": bytes(data), "more_body": False}

        await self.app(scope, bounded_receive, send)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def reject(status: int, code: str, message: str, run: Json | None = None):
    detail: Json = {"code": code, "message": message}
    if run is not None:
        detail["current_run"] = view(run)
    raise HTTPException(status_code=status, detail=detail)


def unavailable_run():
    reject(409, "superseded_run", "This run is no longer current. Analyze the selected packet again.")


def view(run: Json) -> Json:
    """Make a detached API snapshot while holding the workspace lock."""
    result = deepcopy(run)
    succeeded = run["analysis"]["status"] == "succeeded"
    has_fields = bool(run["extracted_fields"])
    busy = run["analysis"]["status"] == "running"
    approved = run["clarification"]["approval"] is not None
    result["allowed_actions"] = {
        "review_evidence": has_fields and not busy,
        "correct_fields": has_fields and not busy,
        "approve_clarification": succeeded and not approved
        and not any(f["kind"] == "needs_review" for f in run["findings"]),
        "download_export": approved,
        "edit_draft": succeeded,
    }
    corrected = {(item["source_id"], item["field"]) for item in run["audit"] if item["event"] == "field_correction"}
    reviewed = approved
    states = {}
    for source in ("RFQ", "DRAWING"):
        states[source] = {}
        for field, entry in run["extracted_fields"].get(source, {}).items():
            related = [f for f in run["findings"] if f["field"] == field and source in f["values"]]
            inspected = reviewed or (source, field) in corrected
            status = "Supported"
            if entry["value"] is None:
                status = "Missing" if inspected else "Needs review"
            for finding in related:
                if finding["kind"] == "conflict":
                    status = "Conflict"
                elif finding["kind"] == "missing" and entry["value"] is None:
                    status = "Missing" if reviewed or finding["semantic_review_status"] != "pending" else "Needs review"
                elif finding["kind"] == "needs_review":
                    status = "Needs review"
            semantic = "confirmed" if reviewed else "pending"
            if (source, field) in corrected:
                semantic = "corrected"
            states[source][field] = {"status": status, "semantic_review_status": semantic}
    result["field_states"] = states
    return result


def as_packet(run: Json) -> Json:
    return {**run["packet"], "sources": run["sources"]}


def compute_rules(run: Json, reviewed: set[tuple[str, str]]):
    extracted = {"packet_id": run["packet"]["packet_id"], "sources": run["extracted_fields"]}
    run["findings"] = domain.apply_rules(as_packet(run), extracted, reviewed)
    run["quote_readiness"] = domain.quote_readiness(run["findings"])


class Workspace:
    """A new analysis supersedes only this workspace's previous packet."""

    def __init__(self, client: VertexClient):
        self.client = client
        self.lock = RLock()
        self.current: Json | None = None

    def require(self, run_id: str, versions: ExpectedVersions | None = None) -> Json:
        run = self.current
        if run is None or run["run_id"] != run_id:
            unavailable_run()
        if versions is not None:
            v = run["versions"]
            if (v["run_version"], v["draft_version"]) != (versions.expected_run_version, versions.expected_draft_version):
                reject(409, "stale_version", "The review changed. Inspect the current version before saving.", run)
        return run

    def fail(self, run: Json, exc: VertexError):
        with self.lock:
            self.require(run["run_id"])
            run["analysis"] = {"status": "failed", "stage": exc.stage, "code": exc.code}
            reject(exc.status_code, exc.code, exc.message, run)

    def draft(self, run: Json) -> Json:
        packet_id = run["packet"]["packet_id"]
        findings = run["findings"]
        try:
            draft, meta = self.client.draft(packet_id, findings, lambda d: domain.validate_draft(packet_id, findings, d))
        except VertexError as exc:
            self.fail(run, exc)
        with self.lock:
            self.require(run["run_id"])
            run["questions"] = draft["questions"]
            run["provenance"]["draft"] = meta
            run["analysis"] = {"status": "succeeded", "stage": "complete"}
            run["clarification"]["status"] = "draft_ready"
            return view(run)

    def analyze(self, packet: Json) -> Json:
        run: Json = {
            "run_id": str(uuid4()),
            "packet": {"packet_id": packet["packet_id"], "synthetic": True},
            "sources": packet["sources"], "extracted_fields": {}, "findings": [], "questions": [],
            "analysis": {"status": "running", "stage": "extraction"}, "quote_readiness": "needs_review",
            "clarification": {"status": "not_started", "approval": None},
            "versions": {"run_version": 1, "draft_version": 1,
                         "source_hash": domain.source_hash(packet), "rule_version": domain.RULE_VERSION},
            "provenance": {"mode": "live", "model_id": self.client.model_id, "provider": self.client.provider, "started_at": now(),
                           "extraction": None, "draft": None}, "audit": [],
        }
        with self.lock:
            self.current = run
        try:
            extracted, meta = self.client.extract(packet, lambda d: domain.validate_extraction(packet, d))
        except VertexError as exc:
            self.fail(run, exc)
        with self.lock:
            self.require(run["run_id"])
            run["extracted_fields"] = extracted["sources"]
            run["provenance"]["extraction"] = meta
            compute_rules(run, set())
            run["analysis"]["stage"] = "draft"
        return self.draft(run)

    def correct(self, run_id: str, request: Corrections) -> Json:
        corrections = [item.model_dump() for item in request.corrections]
        with self.lock:
            run = self.require(run_id, request)
            if not run["extracted_fields"] or run["analysis"]["status"] == "running":
                reject(409, "unavailable_fields", "Complete extraction before correcting a field.", run)
            if not corrections and run["analysis"]["status"] != "failed":
                reject(422, "empty_correction", "Choose a field to correct.")
            packet = as_packet(run)
            extracted = {"packet_id": packet["packet_id"], "sources": run["extracted_fields"]}
            updated = domain.apply_corrections(packet, extracted, corrections) if corrections else extracted
            stamp = now()
            for item in corrections:
                src, field = item["source_id"], item["field"]
                run["audit"].append({"event": "field_correction", "source_id": src, "field": field,
                                     "before": deepcopy(extracted["sources"][src][field]),
                                     "after": deepcopy(updated["sources"][src][field]),
                                     "reviewer_role": "estimator", "at": stamp})
            run["extracted_fields"] = updated["sources"]
            run["versions"]["run_version"] += 1
            run["versions"]["draft_version"] += 1
            run["clarification"] = {"status": "not_started", "approval": None}
            run["questions"] = []
            run["provenance"]["draft"] = None
            compute_rules(run, {(e["source_id"], e["field"]) for e in run["audit"] if e["event"] == "field_correction"})
            run["analysis"] = {"status": "running", "stage": "draft"}
        return self.draft(run)

    def approve(self, run_id: str, request: Approval) -> Json:
        with self.lock:
            run = self.require(run_id, request)
            if not view(run)["allowed_actions"]["approve_clarification"]:
                reject(409, "approval_unavailable", "Review a current, validated draft and correct uncertain fields first.", run)
            ids = [f["finding_id"] for f in run["findings"]]
            if (not request.confirmed_meaning_and_completeness or sorted(request.reviewed_finding_ids) != sorted(ids)
                    or set(request.reviewed_sources) != {"RFQ", "DRAWING", "CHECKLIST"}):
                reject(422, "review_required", "Inspect every source and finding before approving the clarification.")
            questions = [q.model_dump() for q in request.questions]
            packet_id = run["packet"]["packet_id"]
            domain.validate_draft(packet_id, run["findings"], {
                "packet_id": packet_id, "questions": questions, "requires_human_review": True})
            if questions != run["questions"]:
                run["versions"]["draft_version"] += 1
            run["questions"] = questions
            reviewed = {(source, field) for source, fields in run["extracted_fields"].items() for field in fields}
            compute_rules(run, reviewed)
            run["clarification"] = {
                "status": "awaiting_customer_response" if ids else "approved",
                "approval": {"run_id": run_id, **run["versions"], "reviewer_role": "estimator",
                             "approved_at": now(), "scope": "clarification_packet",
                             "reviewed_finding_ids": ids, "reviewed_sources": request.reviewed_sources,
                             "confirmed_meaning_and_completeness": True},
            }
            run["audit"].append({"event": "clarification_approved", **deepcopy(run["clarification"]["approval"])})
            return view(run)

    def reopen(self, run_id: str, request: ExpectedVersions) -> Json:
        with self.lock:
            run = self.require(run_id, request)
            if not run["clarification"]["approval"]:
                reject(409, "no_approval", "This draft already awaits approval.", run)
            run["versions"]["draft_version"] += 1
            run["audit"].append({"event": "draft_reopened", "at": now(), **run["versions"]})
            run["clarification"] = {"status": "draft_ready", "approval": None}
            compute_rules(run, {(e["source_id"], e["field"]) for e in run["audit"] if e["event"] == "field_correction"})
            return view(run)

    def export(self, run_id: str) -> JSONResponse:
        with self.lock:
            run = self.require(run_id)
            approval = run["clarification"]["approval"]
            if not approval or any(approval[k] != v for k, v in run["versions"].items()):
                reject(409, "approval_required", "Approve the current clarification packet before downloading.", run)
            result = view(run)
            lines = {f"{s['source_id']}:{line[:4]}": line[7:] for s in run["sources"] for line in s["text"].splitlines()}
            refs = {ref for f in run["findings"] for ref in f["evidence_refs"] + f["policy_refs"]}
            result["referenced_passages"] = {ref: lines[ref] for ref in sorted(refs)}
            result["document_type"] = "Reviewed synthetic clarification packet"
            result.pop("allowed_actions")
            filename = f"RevisionGate-{run['packet']['packet_id']}-v{run['versions']['draft_version']}.json"
            return JSONResponse(result, headers={"Content-Disposition": f'attachment; filename="{filename}"',
                                                  "Cache-Control": "no-store"})


@dataclass
class WorkspaceEntry:
    workspace: Workspace
    last_used: float
    in_flight: int = 0


class Workspaces:
    def __init__(self, client: VertexClient):
        self.client = client
        self.entries: dict[str, WorkspaceEntry] = {}
        self.lock = RLock()

    @contextmanager
    def use(self, key: str | None, *, create: bool = False) -> Iterator[Workspace]:
        if key is None:
            unavailable_run()
        with self.lock:
            now_mono = monotonic()
            expired = [token for token, e in self.entries.items()
                       if not e.in_flight and now_mono - e.last_used >= WORKSPACE_TTL_SECONDS]
            for token in expired:
                del self.entries[token]
            entry = self.entries.get(key)
            if entry is None:
                if not create:
                    unavailable_run()
                if len(self.entries) >= MAX_WORKSPACES:
                    reject(503, "workspace_capacity", "All demo workspaces are in use. Please try again later.")
                entry = WorkspaceEntry(Workspace(self.client), now_mono)
                self.entries[key] = entry
            entry.in_flight += 1
        # An in-flight model request pins just this entry. Other judges continue independently.
        try:
            yield entry.workspace
        finally:
            with self.lock:
                entry.in_flight -= 1
                entry.last_used = monotonic()


def create_app(client: VertexClient | None = None) -> FastAPI:
    app = FastAPI(title="RevisionGate", version="0.1.0")
    app.add_middleware(BoundedBody)
    workspaces = Workspaces(client if client is not None else VertexClient())

    @app.middleware("http")
    async def workspace_identity(request: Request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        token = request.headers.get(WORKSPACE_HEADER)
        use_cookie = token is None
        if use_cookie:
            token = request.cookies.get(WORKSPACE_COOKIE)
            if not token or not WORKSPACE_ID.fullmatch(token):
                token = None
                if request.url.path in ("/api/fixtures", "/api/analyze"):
                    token = str(uuid4())
        elif not WORKSPACE_ID.fullmatch(token):
            return JSONResponse({"detail": {"code": "invalid_workspace", "message": "Use a valid workspace identifier."}},
                                status_code=400, headers={"Cache-Control": "no-store"})

        request.state.workspace_key = token
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        if use_cookie and token is not None:
            # Set this even on a failed first analysis so its draft can be recovered.
            response.set_cookie(WORKSPACE_COOKIE, token, max_age=WORKSPACE_TTL_SECONDS, path="/api",
                                httponly=True, samesite="strict",
                                secure=request.url.scheme == "https" or bool(os.environ.get("K_SERVICE")))
        return response

    @app.exception_handler(domain.DomainError)
    async def invalid_domain(_: Request, exc: domain.DomainError):
        return JSONResponse({"detail": {"code": "validation_failed", "message": str(exc)}}, 422)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError):
        # Never reflect raw inputs into logs or errors.
        location = ".".join(str(k) for k in exc.errors()[0]["loc"])
        return JSONResponse({"detail": {"code": "invalid_request", "message": f"Check the request field {location}."}}, 422)

    @app.get("/api/fixtures")
    def fixtures():
        return {"packets": [json.loads(p.read_text()) for p in sorted((ROOT / "fixtures").glob("*.json"))]}

    @app.post("/api/analyze")
    def analyze(packet: Packet, http_request: Request):
        data = packet.model_dump()
        domain.validate_packet(data)
        with workspaces.use(http_request.state.workspace_key, create=True) as workspace:
            return workspace.analyze(data)

    @app.patch("/api/runs/{run_id}/fields")
    def correct_fields(run_id: str, request: Corrections, http_request: Request):
        with workspaces.use(http_request.state.workspace_key) as workspace:
            return workspace.correct(run_id, request)

    @app.post("/api/runs/{run_id}/approve-clarification")
    def approve_clarification(run_id: str, request: Approval, http_request: Request):
        with workspaces.use(http_request.state.workspace_key) as workspace:
            return workspace.approve(run_id, request)

    @app.post("/api/runs/{run_id}/reopen")
    def reopen_draft(run_id: str, request: ExpectedVersions, http_request: Request):
        with workspaces.use(http_request.state.workspace_key) as workspace:
            return workspace.reopen(run_id, request)

    @app.get("/api/runs/{run_id}/export")
    def export(run_id: str, http_request: Request):
        with workspaces.use(http_request.state.workspace_key) as workspace:
            return workspace.export(run_id)

    dist = ROOT / "frontend" / "dist"
    if dist.is_dir() and (dist / "index.html").is_file():
        app.mount("/", StaticFiles(directory=dist, html=True), name="review")
    return app


app = create_app()

"""Run the real API and Google Cloud Vertex AI client in an isolated, ephemeral acceptance workspace.

The oracle is consulted by the evaluator only, after the response has arrived.
No prior-run replay or mocked transport is available here.
"""
from __future__ import annotations

import json
from pathlib import Path
from time import monotonic

from fastapi.testclient import TestClient

from backend.vertex import VertexClient, VertexError
from backend.main import ROOT, create_app, now

ARTIFACTS = ROOT / "evidence"


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def evaluate(packet: dict, run: dict, expected: dict) -> dict[str, bool]:
    findings = {f["finding_id"]: f for f in run["findings"]}
    wanted = {f["finding_id"]: f for f in expected["expected_findings"]}
    questions = {q["finding_id"]: q for q in run["questions"]}
    fields = run["extracted_fields"]
    complete = packet["packet_id"] == "03_complete"
    values = {
        "RFQ": {"part_id": "BRK-104", "quantity": 200, "revision": "C", "material": "6061-T6",
                "finish": "none" if complete else None},
        "DRAWING": {"part_id": "BRK-104", "quantity": None, "revision": "C" if complete else "B",
                    "material": "7075-T6" if packet["packet_id"] in ("01_conflicted", "04_injection") else "6061-T6",
                    "finish": "none" if complete else None},
        "CHECKLIST": dict.fromkeys(("part_id", "quantity", "revision", "material", "finish")),
    }
    return {
        "analysis_complete": run["analysis"]["status"] == "succeeded",
        "document_specific_values": all(fields[s][k]["value"] == v for s, facts in values.items() for k, v in facts.items()),
        "expected_finding_set": set(wanted) == set(findings),
        "expected_kinds_values_and_passages": all(
            fid in findings and findings[fid]["kind"] == w["kind"]
            and findings[fid]["values"] == w["expected_values"] and findings[fid]["blocking"] == w["blocking"]
            and set(findings[fid]["evidence_refs"]) == set(w["source_lines"])
            and set(w.get("policy_source_lines", [])) <= set(findings[fid]["policy_refs"])
            for fid, w in wanted.items()),
        "exact_question_refs": len(run["questions"]) == len(wanted) and set(questions) == set(wanted)
        and all(q["evidence_refs"] == findings[fid]["evidence_refs"] and q["policy_refs"] == findings[fid]["policy_refs"]
                for fid, q in questions.items() if fid in findings),
        "expected_quote_state": run["quote_readiness"] == expected["expected_state"],
        "requires_estimator": run["clarification"]["approval"] is None and not run["allowed_actions"]["download_export"]
        and all(f["semantic_review_status"] == "pending" for f in run["findings"]),
        "verified_extraction_and_draft": all(run["provenance"][stage]["mode"] == "live"
            and run["provenance"][stage]["model_id"] == run["provenance"]["model_id"] and run["provenance"][stage]["provider"] == "Google Cloud Vertex AI" for stage in ("extraction", "draft")),
    }


def main() -> int:
    ARTIFACTS.mkdir(exist_ok=True)
    provider = VertexClient()
    report = {"mode": "live", "provider": provider.provider, "requested_model": provider.model_id,
              "location": provider.location, "checked_at": now(), "smoke": {}, "cases": {}}
    with TestClient(create_app(provider)) as api:
        packets = api.get("/api/fixtures").json()["packets"]
        try:
            report["smoke"] = {"status": "passed", **provider.smoke()}
        except VertexError as exc:
            report["smoke"] = {"status": "failed", "code": exc.code, "stage": exc.stage, "message": exc.message}
            for packet in packets:
                report["cases"][packet["packet_id"]] = {"status": "not_run", "reason": exc.code}
        else:
            for packet in packets:
                pk = packet["packet_id"]
                started = monotonic()
                response = api.post("/api/analyze", json=packet)
                elapsed_ms = round((monotonic() - started) * 1000)
                if response.status_code != 200:
                    error = response.json()["detail"]
                    report["cases"][pk] = {"status": "failed", "elapsed_ms": elapsed_ms, "http": response.status_code, "code": error["code"],
                                           "stage": error.get("current_run", {}).get("analysis", {}).get("stage")}
                    continue
                run = response.json()
                expected = json.loads((ROOT / "expected/expected_findings.json").read_text())["cases"][pk]
                checks = evaluate(packet, run, expected)
                report["cases"][pk] = {"status": "passed" if all(checks.values()) else "failed",
                                       "checks": checks, "elapsed_ms": elapsed_ms, "run_id": run["run_id"], "versions": run["versions"],
                                       "findings": [f["finding_id"] for f in run["findings"]],
                                       "quote_readiness": run["quote_readiness"], "provenance": run["provenance"]}
                if pk == "01_conflicted":
                    # The API emits synthetic excerpts and an allowlist of provider metadata.
                    write_json(ARTIFACTS / "sample-vertex-run.json", {
                        "label": "Recorded Google Cloud Vertex AI run", "recorded_at": now(), "review_status": "Awaiting human review",
                        "packet": run["packet"], "sources": run["sources"], "run_id": run["run_id"],
                        "versions": run["versions"], "provenance": run["provenance"], "findings": run["findings"],
                        "questions": run["questions"], "extracted_fields": run["extracted_fields"],
                        "quote_readiness": run["quote_readiness"]})
    provider.close()
    passed = all(c["status"] == "passed" for c in report["cases"].values()) and bool(report["cases"])
    report["status"] = "passed" if passed else ("blocked" if report["smoke"]["status"] == "failed" else "failed")
    write_json(ARTIFACTS / "live-validation.json", report)
    print("Live validation:", report["status"])
    for pk, case in report["cases"].items():
        print(pk, case["status"], case.get("code", case.get("reason", "")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

# RevisionGate

RevisionGate lets an estimator review a single synthetic RFQ, compare conflicting requirements with the drawing and download an approved clarification packet. The runnable build uses **Google Cloud Vertex AI** for extraction and drafting, following the requested provider change. The original workbook and historical starter notes describe the IBM design.

All four fixtures passed live Vertex verification. The [recorded analysis](evidence/sample-vertex-run.json) and [sample downloaded packet](evidence/sample-reviewed-clarification.json) are from genuine calls. The sample download came from the [automated browser acceptance test](evidence/browser-live-validation.json) on synthetic data.

## Hosted hackathon demo

[Open RevisionGate on Cloud Run](https://revisiongate-266196031355.us-east1.run.app). Judges can review the same or different synthetic packets simultaneously without signing in. Each tab has its own findings, editable questions, approval and download. Analyzing again replaces the previous review in that tab. Refreshing or closing the page ends access to that review, so download the approved packet first.

The service runs in `us-east1` with one instance at most, a single backend worker and scale-to-zero enabled. The runtime uses its attached service account for Vertex AI. The source build packages the production frontend, backend, synthetic fixtures, prompts and extraction schema.

## Launch locally

From this directory, use Python 3.11+ and Node.js 22.12+.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm --prefix frontend ci
npm --prefix frontend run build
```

Use a Google Cloud project with billing, the Vertex AI API enabled and a principal with permission to invoke the selected model. For a local workstation, sign in using Application Default Credentials (ADC). Set the quota project to your own project if needed.

```sh
gcloud auth application-default login
# Optional when ADC already resolves the intended project:
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
cp -n .env.example .env
```

In the optional root `.env`, set `GOOGLE_CLOUD_PROJECT` to your project ID if ADC project discovery is insufficient. The defaults are `GOOGLE_CLOUD_LOCATION=global` and `VERTEX_MODEL_ID=gemini-3.5-flash`. The process environment takes precedence. Credentials stay in ADC or the runtime service account. Keep service credentials out of the frontend directory and source control. [Google ADC setup](https://cloud.google.com/docs/authentication/provide-credentials-adc) · [Google model lifecycle](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-versions)

```sh
.venv/bin/python -m backend.smoke
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open [the review page](http://127.0.0.1:8000). FastAPI serves the built React app and API on the same origin. For frontend development, run the backend on port 8000 and `npm --prefix frontend run dev` in another terminal. Use one backend worker so requests for an in-memory review reach the same process.

## Review a packet

1. Select a fixture and choose **Analyze packet**. The first analysis in a server process runs a real preflight, then calls the model to extract each document's facts in one request. The app validates the extraction, applies its versioned rules and sends the validated findings to a second model call for drafting.
2. Choose **Review evidence** to open all documents, findings, questions and extracted fields together. Inspect the source passages and checklist, including omissions. Correct a field with its supporting line or confirm its absence after inspection. Edit the clarification wording as needed.
3. Choose **Approve clarification packet** to attest to that review and download the current JSON. It contains the exact approved questions, original sources, quoted spans, policy passages, findings, versions and approval. The quote stays **Blocked** while an engineering conflict or mandatory gap remains. A clean packet still requires estimator review.

The browser retains the selected sources on a service failure. If extraction succeeded but drafting failed, the estimator can inspect those fields and retry drafting. A correction commits the new field version before redrafting so a failed retry cannot revive an old approval. Reopening an approved draft invalidates its export immediately.

## Evidence and decisions

The backend accepts one RFQ, one DRAWING and one CHECKLIST, each with at most 64 uniquely numbered lines and 8,192 characters. Each line body has a 1,024-character limit. Requests are limited to 64 KiB. The fixtures use `L001 | body`. Evidence offsets count Unicode code points into the body and exclude the end position. Python validates schema, packet ID, source ownership, line ID, range and exact slice equality. Browser highlighting uses the same units.

The rules compare part IDs, revisions and materials across both engineering sources, require a positive RFQ integer quantity and require explicit finish in at least one engineering source. Two different explicit finishes also block the quote. The rules preserve material temper and part punctuation. Checklist statements can supply policy citations only. Exact quotes establish their location. The estimator still checks factual meaning and completeness.

A missing extracted mandatory value is a provisional gap with a pending semantic review. A recognized explicit declaration that the extraction overlooked requires correction. Human confirmation of an actual gap leaves quote readiness blocked. For unlabeled prose, interpretation and overlooked requirements depend on the estimator. Approval records the wording of the clarification, while the governing technical requirement awaits clarification.

## API and storage

The backend keeps one current run per workspace in memory. The web app generates a random workspace key for each page and sends it in the `X-RevisionGate-Workspace` header. API clients can instead retain the session cookie across requests. Every run operation checks the workspace and run ID before accessing review data. A new valid analysis supersedes that workspace's prior run before inference, including when the new request later fails.

Inactive workspaces expire after two hours. The service accepts up to 128 workspaces at once and lets active requests finish before cleanup. Instance restarts and scale-to-zero clear in-memory reviews. Downloaded packets are portable snapshots.

| Method and path | Input and result |
|---|---|
| `GET /api/fixtures` | Returns the four complete synthetic packets for selection. |
| `POST /api/analyze` | Accepts a fixture object. Returns run ID, sources, extracted fields, field review states, findings, questions, quote readiness, clarification status, allowed actions, versions and call provenance. |
| `PATCH /api/runs/{id}/fields` | Accepts both expected versions and a corrections list. Each change has source ID, field, value and exact evidence spans. Revalidates, records the change, increments versions and generates a new draft. An empty list retries a failed drafting stage. |
| `POST /api/runs/{id}/approve-clarification` | Accepts both expected versions, edited questions, reviewed finding IDs, all three reviewed source IDs, and explicit confirmation of meaning and completeness. Saves approved wording atomically. |
| `POST /api/runs/{id}/reopen` | Accepts both expected versions. Revokes approval and opens the saved wording for a new edit. |
| `GET /api/runs/{id}/export` | Downloads the current approved packet. Checks the source hash, rules, run and draft versions. |

The version keys in requests are `expected_run_version` and `expected_draft_version`. Approval binds the run ID, SHA-256 of the canonical source texts, rule version, run version and draft version. Invalid inputs return 422, oversize requests 413, and stale or unapproved operations 409. Upstream errors return actionable redacted 502/503/504 responses. A recoverable error can include the current run. See the [local API schemas](http://127.0.0.1:8000/docs) and [typed UI contract](frontend/src/types.ts).

## Model calls

The server calls Google's REST `v1` `generateContent` endpoint with low temperature and structured JSON. The production app uses the Vertex client exclusively. It loads the two supplied system prompts and converts the output contracts to Vertex's generation schema. The complete local validators enforce constraints after parsing. At most one generation repair is allowed for a malformed or invalid model result. An upstream timeout returns a visible service failure. [Google generateContent reference](https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rest/v1/projects.locations.publishers.models/generateContent)

Extraction receives one input packet and numeric line-length hints. Drafting receives the packet ID and only the validated finding IDs, kinds, fields, values and references. All reference lists must match exactly. Each conflict question must retain both values. The offline answer key is read only by test and evaluation code. Source commands cannot set approval or alter code-owned rules.

## Validate and record

```sh
.venv/bin/python -m pytest -q
npm --prefix frontend run build
.venv/bin/python -m backend.smoke > evidence/vertex-smoke.json
.venv/bin/python -m scripts.validate_live
```

The last command uses real Vertex AI and the normal FastAPI entry points in its own ephemeral workspace. It returns a nonzero exit code when authentication, inference or any acceptance criterion fails. It writes [per-fixture live results](evidence/live-validation.json). A completed fixture 01 analysis also produces `evidence/sample-vertex-run.json`, labeled as recorded and awaiting human review. This file contains only synthetic packet data and redacted run metadata. The UI never substitutes a recorded run for live analysis.

The local workflow tests use an isolated HTTP test transport. They exercise both prompt payloads, source validation, fixed rules, stale updates, approval and downloads. See [verification results](VALIDATION.md) for the actual test scope and live status.

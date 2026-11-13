# RevisionGate verification

Checked November 13, 2026 using the React production build and FastAPI application.

| Check | Actual outcome |
|---|---|
| Live Google Cloud smoke | Passed on the first attempt with gemini-3.5-flash in global, using Vertex v1 structured JSON. The authenticated smoke took 1.836 seconds. See [redacted smoke result](evidence/vertex-smoke.json). |
| Four live fixture analyses | All four passed all eight acceptance checks. Each used one extraction and one drafting call, with zero repair attempts. See [live acceptance report](evidence/live-validation.json). |
| Python tests | All 78 domain, provider protocol and API workflow tests passed with a synthetic Vertex transport. See the test counts below. |
| React/TypeScript | Type checking and the Vite production build passed. |
| Refresh on Cloud Run | Two judge tabs restored separate edits, including a blank question. Only the approving judge recovered the approval, with an identical downloadable packet. Refresh after reopening restored the unapproved wording. Each tab made one analysis request. [Live refresh test](evidence/cloud-run-review-refresh.json) |
| Concurrent judges on Cloud Run | Two tabs analyzed the same fixture with 4.504 seconds of overlap, approved different wording and downloaded separate packets. Both quotes stayed blocked. A new analysis in one tab preserved the other tab's approved export. [Public deployment test](evidence/cloud-run-judge-isolation.json) |
| Live browser workflow | The three-click fixture 01 run downloaded three source-linked questions. Quote status stayed blocked and clarification status became awaiting customer response. The approval actor was an automated synthetic QA session. [Live browser record](evidence/browser-live-validation.json) · [Exact downloaded JSON](evidence/sample-reviewed-clarification.json) |
| Browser failure and state coverage | Nine checks passed against the built page and an isolated FastAPI server with a test-only Vertex transport. The third click triggered a real JSON download. See [browser results and tested file hashes](evidence/browser-validation.json). |

## Genuine model runs

The live runner submitted the unmodified fixture texts through the API. After the response arrived, it compared each source's extracted values, the finding set, opposing values, exact source lines, policy references, question coverage and readiness with the offline oracle. Source documents, validated spans and the three drafted questions for fixture 01 are retained in the [recorded Vertex run](evidence/sample-vertex-run.json).

| Fixture | Findings | Extraction | Drafting | Total API request |
|---|---|---:|---:|---:|
| 01 conflicted | Revision conflict, material conflict, missing finish | 2.327 s | 2.226 s | 4.567 s |
| 02 material changed | Revision conflict, missing finish | 4.244 s | 1.665 s | 5.917 s |
| 03 complete | No seeded blockers, estimator review required | 2.340 s | 1.313 s | 3.659 s |
| 04 embedded instruction | Revision conflict, material conflict, missing finish | 2.529 s | 2.259 s | 4.792 s |

Times cover one measured run per synthetic fixture and exclude estimator review. The run began after local Google sign-in was renewed and the Vertex AI API was enabled in the active project. The original IBM smoke stopped at missing configuration before the requested provider change. [Historical IBM smoke result](evidence/ibm-smoke.json)

## Independent application checks

The test transport reads the outbound document text and returns a synthetic structured extraction. The real server checks its citations, applies the fixed rules, drafts via the test transport and validates the resulting questions. The offline oracle checks the API response. These results measure application behavior. The live runner above measures source-specific outputs independently.

| Fixture | Result from analysis and review |
|---|---|
| 01 conflicted | Revision C/B, material 6061-T6/7075-T6 and an unconfirmed finish gap. After sources were reviewed, the downloaded packet still said blocked. |
| 02 material changed | Changing the drawing material to 6061-T6 removed only the material finding. Revision and finish remained blocking. |
| 03 complete | No seeded blockers. Estimator review was required before clarification approval and export. |
| 04 embedded instruction | The same three findings as 01. The injected line remained visible as drawing data and could not support an explicit finish of none. |

## Failure and consistency checks

- Fabricated spans, wrong source ownership, invalid offsets, Unicode slicing errors, CHECKLIST part facts and an exact quote from the injected instruction were rejected.
- Conflicting explicit finishes, part mismatch, incomplete material designations and missing RFQ quantity were checked. A source-backed correction restored an overlooked drawing revision. The correction path rejected attempts to overwrite a declared requirement.
- Malformed model JSON exhausted one repair attempt. A timeout returned 504 with the source packet retained. Invalid draft references, duplicate or missing questions, and conflict wording that removed a competing value were rejected.
- Approval saved the edited wording with the source hash, rule version, run ID and draft version. Reopening, correcting, changing input and rerunning invalidated prior exports. A superseded in-flight request could not overwrite a newer run.
- Two simultaneous API clients analyzed the same packet, approved different wording and downloaded independent exports. A failed rerun and a successful rerun in one workspace preserved the other export. Cross-workspace run operations returned a generic stale-run error.
- The browser opened all three documents and all questions together, retained rejected edits, offered retry after a timeout and exposed the approval control on a narrow viewport. Keyboard checks covered the selector, action button and visible focus.

Run `.venv/bin/python -m pytest -q` for the local suite and `.venv/bin/python -m scripts.validate_live` for real inference. The local suite covers 36 domain cases, 22 API workflow cases and 20 Vertex credential, protocol, schema and error-handling cases. No worker time savings or model accuracy benchmark was measured.

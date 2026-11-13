# RevisionGate Michigan DevFest Workbook and Execution Blueprint

November 13 2026 | Team assumption: 3–4 builders | All milestone times are Eastern

Build RevisionGate: a source-linked RFQ review gate for an estimator at a small Michigan manufacturer. It identifies conflicting drawing revisions and materials, flags missing requirements, and prepares a clarification packet for human approval. The first release covers one part and a few text documents. The output is a reviewed clarification packet, not an engineering decision or a calculated price.

## Planning basis and verified context

The supplied prompt provides the five-part 25-point rubric, IBM eligibility requirement, data restrictions, workbook questions, and internal milestones. The public event website independently confirms November 13 hacking through 6:00 PM, a submissions-close block from 6:00–6:30 PM, demonstrations from 6:30–7:30 PM, and awards from 7:30 PM. Keep 6:00 PM as the working cutoff and submit by 5:45 PM. The public 2026 Official Rules and original workbook were not independently retrieved; this blueprint fills every section specified in the supplied prompt rather than claiming to reproduce an unseen template. [S1]

The website lists speakers and organizers; it does not establish a 2026 judge roster. Design for the documented AI, usability, accessibility, and Michigan business themes without claiming to know individual judges' preferences.

IBM's winner writeups support a useful design inference: solve a concrete task and show a useful result. AIght built factual-claim verification; Daimyo addressed restaurant data work; DuniAfrika built a WhatsApp worker assistant. Quantum League placed second in its economic-growth category. These were different competitions and categories, not four first-place business-productivity winners or controlled evidence of a universal winning formula. The actual 2025 Michigan DevFest winner was MIStartup Navigator, a local entrepreneur resource tool. [S2–S4]

## Stage 1 Three contenders

Scores are comparative planning judgments, not awarded results. A feasibility score of five assumes the acceptance gates below pass. All three make IBM Granite essential to the operational workflow.

| Contender and IBM workflow | Completeness /5 | Efficiency /5 | Usability /5 | Creativity /5 | Michigan impact /5 | Total /25 | Demo reliability | Primary stage failure |
|---|---:|---:|---:|---:|---:|---:|---|---|
| RevisionGate — CNC supplier estimator; Granite extracts sourced requirements, code checks conflicts, Granite drafts clarification | 5 | 4 | 5 | 3 | 4 | 21 | High | Extraction misses a contradictory field or cites the wrong line |
| PermitPack — Detroit electrical-contractor office coordinator; Granite maps a synthetic job description to a frozen public permit checklist and drafts missing-item requests | 4 | 4 | 4 | 3 | 4 | 19 | Medium | A local exception makes a superficially complete packet incomplete |
| PrepBridge — independent restaurant shift lead; Granite converts synthetic handoff notes and stock records into structured exceptions and a reviewed prep handoff | 4 | 3 | 4 | 3 | 4 | 18 | Medium | Unit or recipe ambiguity makes the suggested handoff unconvincing |

PermitPack would use a dated City of Detroit checklist rather than claim live municipal compliance. PrepBridge would use deterministic stock arithmetic and human-approved tasks rather than invent demand forecasts. RevisionGate needs fewer external dependencies and exposes its central error visibly in seconds.

## Stage 2 Winner selection

Select RevisionGate. A Michigan supplier can lose estimator time before a price is ever calculated because its RFQ and drawing do not agree. Our three-click demonstration surfaces revision C versus B, 6061-T6 versus 7075-T6, and a missing finish requirement; then turns those findings into an editable clarification packet. The local benefit is more estimator capacity for winning and serving work in Michigan, with less avoidable document rework.

Granite is load-bearing in two distinct steps: extracting requirements from differently phrased source text and drafting questions from the validated findings. Code owns exact comparison, evidence checks, and workflow state. The sixty-second payoff is concrete: the estimator sees why quoting is blocked and leaves with a useful, reviewed document. Existing RFQ products make this a focused workflow specialization, not a claim to have invented AI quoting.

## Stage 3 Completed team workbook

### 1 Who is the user

An estimator at a 20–75-person CNC machine shop in southeast Michigan supplying automotive or industrial manufacturers. This is our target user hypothesis, not an interviewed customer. Their day alternates between RFQ emails, drawing notes, prior jobs, customer follow-up, and costing. The friction point is deciding whether a new packet is consistent enough to begin estimating without silently choosing between contradictory instructions.

### 2 Problem statement

An estimator at a small Michigan CNC supplier struggles to confirm that an RFQ is ready for estimating because requirements are scattered across emails and drawing notes with conflicting revisions or materials, which costs them review time and avoidable clarification rework.

### 3 Research and impact data

1. Michigan manufacturing employed 582,700 workers in 2025 and represented more than 15 percent of private employment, according to the Michigan Center for Data and Analytics using BLS QCEW. This establishes the economic context, not the number of potential RevisionGate customers. [S5]
2. NIST MEP's Sun Surveillance case reports quote preparation falling from 1–3 weeks to 10–15 minutes after quotation-system redesign, integration, and employee training. This is a South Carolina company case published August 4, 2022, not a Michigan average, an AI result, or RevisionGate's measured performance. It demonstrates that quotation workflow delays can be substantial and addressable. [S6]

Our measurable task is time to identify and document packet blockers, not total quotation lead time. Pilot target: reduce that task from an assumed 20 minutes to five while preserving correctness. At ten packets per week, that scenario releases 150 minutes, or 2.5 hours, for customer and estimating work. These are planning assumptions until measured.

For the hackathon, time a manual review and an assisted review of matched synthetic cases, include all review and editing time, and report seconds, missed blockers, false blockers, unsupported statements, and model latency. Counterbalance which case is reviewed first to reduce learning effects. A tiny synthetic benchmark is a demo result, not proof of field ROI. If the target is not met, report the actual result.

### 4 Competitive landscape

| Existing option | What it already does | Where RevisionGate competes |
|---|---|---|
| Inbox and spreadsheet checklist | Gives an estimator flexible manual intake and tracking | A focused comparison screen links each finding to both source passages and carries unresolved items into a clarification packet. Prevalence and manual burden require interviews. |
| Paperless Parts Wingman | Reads RFQ material, assists setup and requirements review, highlights sources, and supports human validation | Strong direct overlap. Test demand for a standalone revision-conflict gate that fits an existing quoting process; do not claim evidence highlights or human review are unique. [S7] |
| DigiFabster AI Quote Agent | Parses forwarded RFQs and generates drafts for human review | RevisionGate concentrates on inconsistent document requirements and explicit blocking status. Do not claim a current product-wide capability or price gap without validation. [S8] |

No invented competitor prices, guaranteed cost advantage, or claim of a defensible moat. The novelty score stays three until local users establish a valuable gap.

### 5 Value proposition

For estimators at small Michigan CNC suppliers, RevisionGate is an RFQ readiness tool that turns conflicting requirements into a source-linked clarification packet, unlike a manual inbox-and-spreadsheet review, which leaves the estimator to reconcile documents and draft follow-up separately.

### 6 IBM Design for AI matrix

| Workbook question | Concrete answer |
|---|---|
| What does AI do for our user? | Granite extracts part, revision, material, quantity, and finish with evidence; a second call drafts questions tied to validated findings. |
| Where does a human stay in control? | The estimator checks source passages, corrects extraction, edits questions, and approves the clarification packet. They cannot override conflicting engineering requirements with an approval button. |
| What happens when AI is wrong? | A correction panel retains the original source and records the edited value. Invalid evidence or extraction failure becomes Needs review. Missing requirements stay missing; unresolved engineering conflicts keep quoting blocked. |
| How do we earn trust? | Show source document and line for each value, distinguish source existence from human-confirmed meaning, retain both conflicting values, show a real run timestamp, and preserve an approval record tied to that run. |

Use Supported, Conflict, Missing, and Needs review labels with icons and text. Do not display uncalibrated confidence percentages. A verbatim substring check verifies that a citation exists; it does not prove the quote supports the extracted meaning. Human review closes that gap in this MVP.

The primary screen has the source pane on the left and findings plus editable clarification on the right. Provide visible keyboard focus, labeled controls, a logical tab order, readable contrast, and text announcements for processing/errors. All approval actions must work by keyboard. Busy states explain which step is running; failures retain the packet and offer a retry or manual correction.

State semantics: BLOCKED → CLARIFICATION DRAFT READY → CLARIFICATION PACKET APPROVED → AWAITING CUSTOMER RESPONSE. These are clarification-workflow states. Quote readiness remains BLOCKED until governing requirements are confirmed. A complete consistent fixture instead reaches READY FOR ESTIMATOR REVIEW; it is not automatically quoted.

### 7 Rubric mapping

| Criterion | Exact proof in the demo |
|---|---|
| Completeness and feasibility | Real IBM call → validated findings → editable draft → approved download; a changed-input fixture changes the findings. |
| Effectiveness and efficiency | Show the measured blocker-review task time and error count if the benchmark has run; otherwise label the 20-to-five-minute goal as a target. |
| Design and usability | Open opposing evidence passages, correct a field, and show that approval does not clear an unresolved conflict. |
| Creativity and innovation | Export a concise exception packet alongside an existing quoting workflow; acknowledge RFQ automation competitors. |
| Michigan impact | Name the small supplier role and show how recovered estimator time serves more local work. No headcount-reduction claim. |

## Stage 4 Architecture and execution

### Parallel design and logic handoffs

Claude Fable owns brand feeling, logo, palette, typography, copy, layout, accessible visual states, and presentational components. GPT owns the typed interface, IBM integration, extraction and evidence validation, deterministic rules, state, approval guards, persistence, exports, and meaningful verification. Use handoffs/CLAUDE_FABLE_DESIGN.txt and handoffs/GPT_LOGIC.txt with the same handoffs/SHARED_CONTRACT.json. GPT establishes the typed props and callbacks; visual design and backend work then proceed in parallel. GPT connects the interface to authoritative backend state, and both review the blocked-approval behavior together.

### Exact stack

Frontend: React and TypeScript in a Lovable-generated single review screen. Backend: Python FastAPI with Pydantic validation and a server-side IBM client. The fastest deployment is the team's already-working host; Cloud Run is optional if its account and deployment path already work. Keep the API key in server-side environment variables. No Gemini step is needed for the text-only MVP.

IBM hero: watsonx.ai hosted IBM Granite, model ID `ibm/granite-4-h-small`, in Dallas `us-south`. Current IBM documentation lists this model for shared inference in Dallas and Frankfurt. Granite 3.3 8B shared inference was withdrawn in February 2026; historical winner stacks are not today's availability guarantee. Authenticate and complete one real inference before polishing the UI. [S9–S11]

Server environment: IBM_CLOUD_API_KEY, WATSONX_PROJECT_ID, WATSONX_URL=https://us-south.ml.cloud.ibm.com, WATSONX_MODEL_ID=ibm/granite-4-h-small. Never use a VITE-prefixed variable for a key.

Auth: POST https://iam.cloud.ibm.com/identity/token with form-encoded grant_type=urn:ibm:params:oauth:grant-type:apikey and apikey from the backend environment. Cache the bearer token server-side until shortly before its returned expiration.

Inference: POST {WATSONX_URL}/ml/v1/text/chat?version=2024-10-08, using Authorization: Bearer <token>, Content-Type: application/json, and a body with model_id, project_id, messages, max_tokens, and a low temperature. API version is a dated compatibility parameter, not today's date. Use schema output when the model preflight accepts it; otherwise use JSON mode, an explicit JSON instruction, and server-side schema validation. One bounded schema-repair retry; then a visible failure. The official chat API documents structured JSON formats. [S12]

Do not add Orchestrate, Guardian, watsonx.data, a vector database, model tuning, or additional agents to this small pipeline. For three short sources, sending the whole bounded packet is simpler and easier to inspect than retrieval infrastructure.

### Pipeline and trust boundaries

1. User selects a supplied fixture or pastes text. Backend limits packet size, assigns stable source IDs and line numbers, and computes a content hash. Treat all document instructions as untrusted data.
2. Granite extraction call returns document-specific fields and quoted evidence. Keep each document's values separate. Null is required for absent data; do not merge revision B and C into a guessed authoritative value.
3. Python validates the JSON, source IDs, line ranges, and quoted spans. It compares normalized part numbers, revisions, and materials and checks the explicit finish requirement. Rule definitions are versioned code. A missing value due to extraction failure is Needs review; do not pretend the model proved absence.
4. Human can inspect and correct findings. Semantic support remains a review responsibility. Every correction changes the packet version and invalidates prior draft approval.
5. Granite drafting call receives only verified findings plus their evidence references. It emits one clarification question per blocker, references finding IDs, and cannot invent material choices, prices, commitments, or resolutions. Backend rejects unknown references or an incomplete question set; the user reviews wording.
6. Approving the clarification packet stores the run ID, source hash, rules version, draft version, reviewer role, and timestamp. Export a text or JSON packet. No outbound email or ERP write occurs in this MVP.

Removing Granite removes extraction and drafting, so IBM performs the core language work. Code does the deterministic checking and preserves the worker's authority.

### Minimum API contract

- POST /api/analyze: input sources; output run ID, extracted fields, findings, quote status, draft, and timing. The two Granite calls may run sequentially inside this request for the smallest build.
- PATCH /api/runs/{id}/fields: validated human corrections; invalidate old draft/approval, rerun checks, and regenerate a draft with a new version before it can be approved.
- POST /api/runs/{id}/approve-clarification: submit the edited draft plus expected run and draft versions; reject stale versions, validate the finding references, and atomically save and approve that exact reviewed text, retaining BLOCKED quote status where blockers remain.
- GET /api/runs/{id}/export: return the approved clarification packet with evidence references and run metadata.

Local in-memory records plus JSON export are sufficient for the demonstration. Label storage as ephemeral; a durable multi-user audit system is later work. Keep the public repository limited to synthetic fixtures and redacted run evidence.

### Exact permissible dataset

Load the included synthetic BRK-104 packet. No live portal or scraped dataset is required. The state manufacturing statistics support the pitch; they do not drive individual RFQ decisions. A state data feed would add dependency risk without improving this task.

| Source | Demo content |
|---|---|
| RFQ | Part BRK-104, quantity 200, requested revision C, material 6061-T6 |
| DRAWING | Same part, revision B, material 7075-T6; no finish requirement supplied |
| CHECKLIST | Revision and material must agree; an explicit finish including none is mandatory; conflicts require customer clarification |

Expected findings: revision conflict, material conflict, finish missing. Never choose which document governs. Approving questions does not resolve these findings.

Included fixtures: 01_conflicted; 02_material_changed, where only the drawing's material becomes 6061-T6 and the material blocker disappears; 03_complete, where documents agree and finish is explicitly none; and 04_injection, where a document instruction tries to override the workflow but must remain inert source data. Expected outputs live separately from model inputs.

The smallest fallback is plain text. Text-bearing PDF extraction is a stretch only after the full flow works. CAD interpretation, OCR, price calculation, authentication, supplier databases, and ERP integration are outside today's build.

### Model prompts and result contract

Use prompts/extract.txt and prompts/draft.txt as the system instructions. Supply source text in a separately delimited user message. Use schema/extraction.schema.json as the extraction contract. These files are build inputs, not evidence of a completed IBM integration.

Extraction invariant: for each source and requested field, return a value and evidence or explicit absence/needs-review; preserve contradictions across sources. A schema-valid answer can still be wrong.

Drafting invariant: one editable question for each validated blocker, with finding IDs. Example output wording for the seeded packet:

“Please confirm the governing revision for BRK-104: the RFQ requests C while the attached drawing identifies B. Please confirm whether the required material is 6061-T6 or 7075-T6. Please provide the required finish, including an explicit statement if no finish is required.”

### Team ownership

| Owner | Deliverable |
|---|---|
| Backend and AI builder | IBM auth, real model call, schema validation, evidence checks, deterministic findings |
| Frontend and UX builder | Review screen, source comparison, editable draft, approval state and export |
| Data and pitch builder | Synthetic cases, expected results, timed comparison, submission text and video |
| Fourth builder if available | Deployment, keyboard/error checks, recording and repository readiness |

With three people, the data/pitch owner also handles deployment verification. Vaughne's large-scale network automation experience fits backend verification and workflow control; this does not establish manufacturing-domain expertise.

### Sprint plan

Original single-day baseline: by 1:00 PM freeze fixtures and authenticate IBM; by 2:00 PM validate extraction; by 3:00 PM finish deterministic checking and drafting; by 4:00 PM connect UI and export; by 4:30 PM complete the three-click flow; 5:00 PM feature freeze; 5:30 PM video uploaded; 5:45 PM submission; 6:00 PM working cutoff.

Because this request arrived after the 4:30 PM milestone, use this reduced recovery sequence immediately: first establish a genuine IBM request, then wire one fixed packet to a single review screen, then run changed-input and blocked-approval checks, then record and submit. If starting after the 5:00 PM feature freeze, build only the missing core path and protect recording/upload time. Remove optional PDF handling, deployment changes, dashboards, and integrations. A form-based UI on an already-working stack is acceptable; any external-access requirement must be checked against the actual submission form.

If IBM access fails, a prior genuine run may be replayed with a visible Recorded IBM run label and timestamp. A handcrafted canned response is not proof of IBM use. A replay preserves presentation continuity but does not satisfy the live-integration acceptance gate.

### Acceptance gates

| Check | Required outcome |
|---|---|
| Genuine IBM inference | A successful model response with model ID and timestamp; no secrets in logs or repo |
| Conflicted packet | Two conflicts and one missing finish; all evidence points to the correct source |
| Changed input | Changing only drawing material removes only the material conflict |
| Complete packet | No seeded blockers; state is Ready for estimator review, not automatically quoted |
| Invalid evidence | Bad source IDs, lines, or quotation become Needs review and cannot support approval |
| Prompt injection | Source text cannot change system rules or clear blockers |
| Human correction | Updates checks and invalidates earlier approval; opposing source values remain visible |
| Draft approval | Approves clarification only; unresolved quote status stays Blocked |
| IBM timeout or malformed JSON | Clear error, retained inputs, bounded retry, manual review fallback |
| Usability | Three-click happy path works by keyboard; labels and status remain clear without color |

Record actual pass/fail results in submission evidence. Do not populate benchmark results or checks as passed before executing them.

### Submission copy

These drafts describe the intended completed MVP. Use the corresponding claim only after its acceptance check passes; include actual benchmark numbers only if measured.

Written Problem and Solution Statement

Michigan's small manufacturing suppliers need to respond quickly to new work while protecting scarce estimator time. An RFQ can request one drawing revision or material while its attachment specifies another. Before calculating a price, an estimator must compare the documents, identify missing requirements, and prepare clarification questions.

RevisionGate turns that review into a focused, evidence-linked workflow. The estimator loads a synthetic RFQ packet, inspects revision and material conflicts beside their source passages, and edits and approves a clarification packet. The application keeps quoting blocked until conflicting requirements are confirmed. It supports the estimator's judgment and creates more capacity for serving Michigan customers. Our prototype focuses on a single-part text packet; broader document support and validation with local suppliers are next.

Written IBM watsonx Utilization Statement

RevisionGate uses IBM Granite model ibm/granite-4-h-small through the watsonx.ai chat API as the core language-processing component. The first model call extracts document-specific part, revision, material, quantity, and finish fields with source references. The backend validates the output structure and evidence locations, applies explicit comparison and completeness rules, and preserves unresolved conflicts. A second Granite call drafts clarification questions using the validated findings. An estimator reviews and approves the current draft; that approval cannot resolve conflicting engineering requirements. IBM authentication and inference run on the backend using environment variables. The demonstration uses synthetic records, and the repository documents the prompts, schema, rules, and genuine IBM execution evidence.

### One minute video script

| Time | Screen and narration |
|---|---|
| 0:00 The user | Show the estimator review screen. “This is an estimator at a small Michigan supplier, reviewing the next job.” |
| 0:10 The problem | Show three documents. “The RFQ requests revision C and 6061 aluminum. Its drawing says B and 7075. The finish is missing.” |
| 0:20 Click 1 | Analyze packet. “IBM Granite extracts the requirements. Our checks flag two conflicts and one missing requirement.” |
| 0:30 Click 2 | Review evidence. “Each finding opens the exact source lines. The estimator checks the evidence and edits the clarification.” |
| 0:40 Click 3 | Approve clarification packet; trigger download as part of this action. “Approve the questions. The quote stays blocked while we wait for customer confirmation.” |
| 0:50 The impact | Show run metadata and capacity target or actual benchmark. “Our target is faster, accurate packet review, giving Michigan suppliers more time to win and serve local work.” |

The one-minute format describes the intended three-click product path. Rehearse and record actual API latency. Do not imply a live step completed instantly if footage was edited; identify any recorded run. If calls exceed the available video segment, show a truthful labeled transition and retain uncut execution evidence.

### Three minute live stage script

0:00–0:20 Problem

“A small Michigan supplier can waste estimator time before calculating a price. An RFQ requests one revision and material, but its drawing says another. Someone must catch that mismatch and get the customer to clarify it.”

0:20–0:40 Why us

“My background is large-scale network automation. The lesson I bring is that useful automation preserves evidence, makes exceptions visible, and leaves consequential decisions with an accountable person. We applied that approach to one manufacturing workflow.”

0:40–1:05 Demo opening

“This packet is synthetic. The part and quantity agree, but the requirements do not. I click Analyze. Granite reads each source separately; it does not guess which document wins.” Show the genuine request status and source documents while the request runs.

1:05–1:35 Evidence

“Here are the findings: revision C versus B, 6061-T6 versus 7075-T6, and no finish specified. I click Review evidence. Both passages are visible. A citation check confirms the passage exists; the estimator still checks that it supports the finding.”

1:35–2:00 Worker control

“Granite drafted these questions from the checked findings. I can edit them. I approve the clarification packet, which downloads with its evidence references. The quote remains blocked. Approving a question does not decide an engineering requirement.”

2:00–2:10 Changed input

“In a second packet, only the drawing material changes to match the RFQ. The material blocker disappears; the revision and finish issues remain.” Show a genuine second run or a clearly identified recorded run.

2:10–2:40 Under the hood

“Two watsonx.ai Granite calls do the language work: extraction and drafting. Python validates the schema, verifies source locations, compares fields, and controls state. We use synthetic text, server-side credentials, and one review screen. The export preserves the run and evidence so the worker can explain the result.”

2:40–3:00 Honest trade-offs

“Today we handle one-part text packets. We have not solved CAD interpretation or proven field savings. Next we will benchmark with Michigan estimators and test whether this focused review gate improves their existing quoting process. The goal is more capacity for local work.”

### Final submission package

Prepare the public repository URL, runnable demo or reproducible launch instructions as required by the real submission form, the one-minute video, both written statements, team details, and the workbook content. Include prompts, synthetic fixtures, deterministic rules, a clear IBM setup guide, and redacted evidence of a real IBM run. Check the actual form for additional required fields and file limits. This list is a working submission checklist, not an independently verified quotation of all legal requirements.

## Sources

[S1] Michigan DevFest official event and schedule: https://www.midevfest.com/

[S2] IBM hackathon alumni AIght and Daimyo: https://developer.ibm.com/hackathons/

[S3] IBM Lean AI winners DuniAfrika and Quantum League: https://community.ibm.com/community/user/blogs/jennifer-judge/2025/05/13/hackathon-teams-use-ibm-granite-to-improve-jobs

[S4] EMU report on the 2025 Michigan DevFest winner: https://today.emich.edu/story/story/13179

[S5] Michigan Center for Data and Analytics 2026 manufacturing employment report: https://www.michigan.gov/mcda/labor-market-information/2026-michigan-manufacturing-industry-workforce-analysis-report/employment-and-wages

[S6] NIST MEP Sun Surveillance case: https://www.nist.gov/mep/successstories/2021/sun-surveillance-increases-jobs-and-sales-following-lean-office-process

[S7] Paperless Parts Wingman product update: https://www.paperlessparts.com/product-update/wingman-ai-powered-quoting-assistant/

[S8] DigiFabster AI Quote Agent instructions: https://help.digifabster.com/en/articles/10479077-getting-started-using-ai-quote-agent-beta-for-the-first-time

[S9] IBM supported foundation models: https://www.ibm.com/docs/en/watsonx/saas?topic=solutions-supported-foundation-models

[S10] IBM regional model availability: https://www.ibm.com/docs/en/watsonx/saas?topic=services-regional-availability-features

[S11] IBM model lifecycle: https://www.ibm.com/docs/en/watsonx/saas?topic=models-foundation-model-lifecycle

[S12] IBM watsonx.ai API: https://cloud.ibm.com/docs/apis/watsonx-ai and agent workflow example: https://www.ibm.com/docs/en/watsonx/saas?topic=agents-agent-driven-chat

Research checked November 13 2026. Prototype benchmarks and IBM execution results must be added by the building team after execution.

# Context for Gemini Carbon: RevisionGate research and pitch

From Claude Fable (design and UX), November 13 2026, about 6:20 PM Eastern. This brief is self-contained. You own research and the pitch for team Chainsaw Factory. Everything below is checked against the repo unless marked "to verify".

## The situation

- Event: Michigan DevFest + AI Hackathon, Hollywood Casino Hotel at Greektown, Detroit.
- Submissions closed at 6:00 PM. Presentations, demos and judging start at 6:30 PM. Winners at 7:30 PM.
- Team: Chainsaw Factory. Team lead: a partnership, Shug and Vaughne. Builders: Claude and GPT. Design and UX: Claude Fable. Research and pitch: you.
- The humans present. Your job is to give them accurate words, checked facts, and ready answers.

## What RevisionGate is

An RFQ review gate for an estimator at a small Michigan CNC machine shop. Before any price is calculated, it compares an RFQ with its drawing notes, shows where they disagree beside the exact source lines, and drafts clarification questions for the customer. The estimator checks the evidence, edits the questions, and approves a clarification packet. Approval covers the questions only. The quote stays blocked until the customer answers.

The demo packet is synthetic: fictional part BRK-104, quantity 200. The RFQ asks for revision C in 6061-T6. The drawing says revision B in 7075-T6. No finish is stated. Expected findings: revision conflict, material conflict, missing finish.

## What is actually built

- AI: Gemini 3.5 Flash on Google Cloud Vertex AI. Two calls per analysis. Call 1 extracts part, quantity, revision, material and finish from each document, with a quoted source span for every value. Call 2 drafts one question per confirmed finding.
- Python (FastAPI, Pydantic) does everything exact: checks that each quoted span exists in its source, compares the fields, sets quote readiness, guards approval, exports the packet. Rules version `intake-1.1`.
- Front end: React, TypeScript, Vite. One review screen.
- Data: four synthetic text packets. No personal, client or confidential data.
- No IBM service runs in this build. The plan began with IBM Granite on watsonx.ai, but the IBM connection was never configured, and the team switched to Vertex AI during the event. The workbook accepts "IBM and/or Google tools".
- Repo: https://github.com/vaughneglymph/revisiongate (public).
- Demo video: `design/video/revisiongate-demo.webm`, 58 seconds, silent with captions. Recorded at 6:16 PM in one take on the real app, with a live model call that returned in 5.3 seconds. The packet that run downloaded is `design/video/demo-run-clarification.json`.

## Results you can quote

| Check | Result | Where |
|---|---|---|
| Live model smoke test | Passed first attempt, 1.8 s | `evidence/vertex-smoke.json` |
| Four packets analyzed live | All four passed all eight acceptance checks, 3.7 to 5.9 s each | `evidence/live-validation.json` |
| Packet 02, changed input | Changing only the drawing material removes only the material finding | same |
| Packet 03, complete | No blockers detected, estimator review still required | same |
| Packet 04, embedded instruction | Same three findings as packet 01, injected line stays plain text | same |
| Three-click path, live, in a browser | Passed at 5:29 PM (automated) and 5:50 PM (final screen) | `evidence/browser-live-validation.json` |
| Python tests | 69 passed with a synthetic model transport | `VALIDATION.md` |

## Claims: allowed and not allowed

Allowed:
- It works end to end on live Gemini calls, on synthetic packets.
- Approval cannot clear a conflict. The quote stays blocked.
- Every value links to its source document and line.

Not allowed:
- No measured time savings. "Twenty minutes down to five" is a pilot target and must be called a target every time.
- No accuracy rate, no confidence percentages.
- No customer, estimator interview, pilot, testimonial, revenue or deployment. The user description is a hypothesis.
- No IBM usage.
- Do not say the system "verifies", "validates" or "resolves" requirements. The system finds and locates. A person confirms and approves.
- Every approval so far was a test click on synthetic data. No estimator approved anything.

## The pitch format (from the organizers' workbook)

| Time | Part | What it must do |
|---|---|---|
| 0:20 | Problem | Who has it and how many people |
| 0:20 | Why us | Why the team cares |
| 1:30 | Live demo | Show it working for one person: three clicks, one clear outcome |
| 0:30 | How it works | Name the tools and what each one does |
| 0:20 | What's next | Who it helps next, and what one more week would build |

The organizers' five rules: build for one specific person; talk to someone who has the problem; scope small; demo the thing itself, not slides; pitch your thinking out loud, including what you did not solve.

A full draft script, the one-minute video script, and all workbook answers are in the team's submission document. Ask Shug or Vaughne to paste it for you, since it is a private page.

## The three clicks, and the words on screen

1. **Analyze packet.** Result: "Quote blocked. Customer clarification required." with "2 conflicts · 1 missing requirement". Revision shows C ≠ B. Material shows 6061-T6 ≠ 7075-T6.
2. **Review evidence.** Each finding opens its source lines. Each passage reads "Source passage located. Confirm its meaning." Questions are editable.
3. **Approve clarification packet.** Panel reads "Clarification approved. Requirements remain unresolved." and "Awaiting customer response." The top-right label still reads Blocked.

## Research, to verify before it is spoken

Neither source was re-opened today by me. Open both and confirm the figures.

1. Michigan manufacturing employed 582,700 workers in 2025, more than 15 percent of private employment. Source: Michigan Center for Data and Analytics. https://www.michigan.gov/mcda/labor-market-information/2026-michigan-manufacturing-industry-workforce-analysis-report/employment-and-wages
2. NIST MEP's Sun Surveillance case: quote preparation fell from 1 to 3 weeks to 10 to 15 minutes after a quotation-system redesign and training. One South Carolina company, published 2022. Not a Michigan average and not an AI result. https://www.nist.gov/mep/successstories/2021/sun-surveillance-increases-jobs-and-sales-following-lean-office-process

Competitors to name honestly: Paperless Parts Wingman (strong overlap: reads RFQ material, highlights sources, supports human validation) and DigiFabster AI Quote Agent (parses RFQs, drafts quotes). RevisionGate's angle is narrower: a standalone conflict gate before quoting, with an approval that cannot clear a conflict. Do not claim evidence highlights or human review are unique.

## Judge questions to prepare

| Likely question | Honest answer |
|---|---|
| Why Gemini and not IBM? | The IBM connection was not configured in time. We switched to Vertex AI during the event and verified it live. |
| How do you know it saves time? | We do not yet. Twenty to five minutes is a target. The next step is a timed comparison with estimators. |
| How accurate is it? | Four synthetic packets pass every check. That is not an accuracy rate, and we do not claim one. |
| What if the model is wrong? | A value that cannot be tied to its source blocks approval. The estimator corrects it, and the draft is rewritten. |
| What about instructions hidden in a document? | Packet 04 contains one. The findings did not change and the line stayed plain source text. |
| Who approved in the demo? | We did, on synthetic data. No estimator or customer has. |
| What is new compared with existing quoting tools? | The narrow gate and the blocked state that approval cannot clear. RFQ automation itself is not new. |
| What did the AI assistants build? | Claude built the design, copy and review screen. GPT built the application logic. |

## What I need from you

1. Open the two sources and confirm or correct the figures.
2. Confirm the five judging criteria against what the organizers announced: completeness and feasibility, effectiveness and efficiency, design and usability, creativity and innovation, Michigan impact.
3. Tighten the pitch script to the times above. Keep every limit in it.
4. Ask Shug and Vaughne for the "Why do we care?" answer in their own words. The current text is a draft and may not describe both of them.

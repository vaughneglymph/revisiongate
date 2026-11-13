# RevisionGate voice guide

The reader is an estimator with a quote due. Write the way a careful colleague would report on a packet: what was found, where, and what to do next.

## Five rules

1. **Say who did what.** The system finds, locates, detects, and drafts. Only a person confirms, approves, or corrects. Never write that RevisionGate verified, validated, or resolved something.
2. **Approval means the questions, nothing else.** Any sentence about approval names the clarification packet and says the requirement is still open. "Clarification approved. Requirements remain unresolved."
3. **Never pick a side.** Give both values in the order the documents give them. Do not call either one correct, newer, or governing.
4. **A missing value is something the system did not find.** Write "No finish was found", not "The finish is not specified". The estimator reads the document to confirm.
5. **Errors say what happened, what was kept, and what to do.** "Analysis did not finish. No findings were produced. Your packet is unchanged."

## Style

- Sentence case for headings and buttons. Buttons start with a verb: Analyze packet, Review evidence, Approve clarification packet.
- Short sentences. One idea each. No exclamation marks.
- Use the shop's words: RFQ, drawing, revision, material, finish, packet, quote.
- Status words are fixed: Supported, Conflict, Missing, Needs review, Blocked. Do not swap in synonyms.
- Identifiers are written exactly as in the source: BRK-104, 6061-T6, L004.
- No confidence percentages. No "AI-powered", "smart", or "instant".
- Name the model provider only from run data, never in fixed copy.

## Words to use and avoid

| Use | Avoid |
|---|---|
| Source passage located | Verified, validated |
| Confirm its meaning | Trust score, confidence |
| Quote blocked | Failed, rejected |
| No blockers detected. Estimator review required. | Ready to quote, all clear, passed |
| Clarification approved | Approved, resolved, cleared |
| Ask the customer | Fix, override |
| Synthetic demo | Sample customer, real data |

## Claims

No measured accuracy, time saved, revenue, testimonials, certifications, or deployments. The twenty-to-five-minute figure is always written as a pilot target, with "not a measured result" beside it. A recorded run is always labeled as recorded, and a synthetic preview as synthetic.

## Product copy

**Descriptor.** RFQ review gate

**One sentence.** RevisionGate compares an RFQ with its drawing notes, shows where they disagree beside the source lines, and prepares clarification questions for an estimator to review and approve.

**Description.** RevisionGate is an RFQ review gate for estimators at small CNC shops. It extracts the part, quantity, revision, material, and finish from an RFQ and its drawing notes, shows conflicting or missing requirements beside the exact source lines, and drafts clarification questions. The estimator checks the evidence and approves the questions. Conflicting requirements stay blocked until the customer answers.

Use the description only for what the running build does. Name the model in a sentence only after a genuine run with that model has passed.

## Six demo-video captions

1. An estimator at a small Michigan CNC shop opens the next RFQ.
2. The RFQ asks for revision C in 6061-T6. The drawing says revision B in 7075-T6. No finish is stated.
3. Analyze packet. The model extracts each document's requirements. Fixed checks flag two conflicts and one missing requirement.
4. Review evidence. Every finding opens beside its exact source lines. The estimator checks the meaning and edits the questions.
5. Approve clarification packet. The questions download. The quote stays blocked until the customer answers.
6. Pilot target: blocker review in five minutes instead of twenty. A target, not a measured result.

If any footage is a recorded run, add "Recorded run" to captions 3 to 5.

The full string list, keyed by component and state, is in `COPY_INVENTORY.md`.

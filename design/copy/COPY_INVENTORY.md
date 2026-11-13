# RevisionGate copy inventory

Generated from `frontend/src/design/copy.ts`. Do not edit by hand: change the string in `copy.ts`, then run `bun design/copy/build_inventory.ts`.

Keys are `copy.<component>.<string>`. `{placeholders}` are filled at render time from run data.

## Product

| Key | Copy |
|---|---|
| `product.name` | RevisionGate |
| `product.descriptor` | RFQ review gate |
| `product.intro` | RevisionGate compares an RFQ with its drawing notes, shows where they disagree beside the source lines, and prepares clarification questions for an estimator to review and approve. |
| `product.description` | RevisionGate is an RFQ review gate for estimators at small CNC shops. It extracts the part, quantity, revision, material, and finish from an RFQ and its drawing notes, shows conflicting or missing requirements beside the exact source lines, and drafts clarification questions. The estimator checks the evidence and approves the questions. Conflicting requirements stay blocked until the customer answers. |

## Top bar (TopBar)

| Key | Copy |
|---|---|
| `topbar.pageTitle` | RFQ packet review |
| `topbar.skip` | Skip to review |
| `topbar.packetLabel` | Packet |
| `topbar.packetsLoading` | Loading packets… |
| `topbar.packetsUnavailable` | Packets unavailable |
| `topbar.synthetic` | Synthetic demo |
| `topbar.syntheticHint` | Fictional packet. No customer records. |
| `topbar.partLabel` | Part |
| `topbar.partUnknown` | Not analyzed yet |
| `topbar.readinessLabel` | Quote readiness |

## Quote readiness label (persistent)

| Key | Copy |
|---|---|
| `readiness.not_analyzed` | Not analyzed |
| `readiness.analyzing` | Analyzing |
| `readiness.blocked` | Blocked |
| `readiness.needs_review` | Needs review |
| `readiness.no_detected_blockers_pending_human_review` | No blockers detected · Review required |
| `readiness.out_of_date` | Out of date |

## Idle state (hero)

| Key | Copy |
|---|---|
| `hero.heading` | Catch RFQ conflicts before quoting starts. |
| `hero.body` | RevisionGate reads the RFQ, drawing notes, and intake checklist, then shows conflicting or missing requirements beside their source lines. You check the evidence and approve the questions for your customer. |
| `hero.stepsLabel` | Three steps |
| `hero.step1` | Pull part, quantity, revision, material, and finish from each document. |
| `hero.step2` | Check every finding against its source lines. Edit the questions. |
| `hero.step3` | Download the questions. The quote stays blocked until the customer answers. |
| `hero.noPacket` | Select a packet to begin. |
| `hero.noPacketsBody` | The packet list did not load. Your work is not affected. |

## Action labels

| Key | Copy |
|---|---|
| `actions.analyze` | Analyze packet |
| `actions.analyzing` | Analyzing packet… |
| `actions.reanalyze` | Analyze again |
| `actions.retry` | Try again |
| `actions.review` | Review evidence |
| `actions.approve` | Approve clarification packet |
| `actions.download` | Download packet |
| `actions.reopen` | Edit clarification |
| `actions.refreshDraft` | Refresh draft |
| `actions.loadCurrent` | Load current version |
| `actions.retryPackets` | Retry |
| `actions.showEvidence` | Show evidence |
| `actions.hideEvidence` | Hide evidence |
| `actions.showInDocument` | Show in document |
| `actions.correct` | Correct value |
| `actions.saveCorrection` | Save correction |
| `actions.cancel` | Cancel |

## Step indicator (ActionBar)

| Key | Copy |
|---|---|
| `steps.counter` | Step {n} of 3 |
| `steps.analyze` | Analyze |
| `steps.review` | Review |
| `steps.approve` | Approve |
| `steps.complete` | Clarification approved |

## Analyzing state

| Key | Copy |
|---|---|
| `loading.heading` | Analyzing packet |
| `loading.body` | Your documents stay on screen. Findings appear here when the run finishes. |
| `loading.listLabel` | This run will |
| `loading.step1` | Read the three source documents |
| `loading.step2` | Extract requirements from each document |
| `loading.step3` | Check that each cited passage exists in its source |
| `loading.step4` | Compare revision, material, and finish |
| `loading.step5` | Draft clarification questions |
| `loading.announce` | Analyzing packet. Please wait. |
| `loading.working` | {label}… |

## Result summary panel

| Key | Copy |
|---|---|
| `summary.blockedTitle` | Quote blocked. Customer clarification required. |
| `summary.blockedBody` | The documents disagree or a required value is missing. RevisionGate does not choose which requirement governs. |
| `summary.needsReviewTitle` | Needs review. Check the marked values. |
| `summary.needsReviewBody` | At least one value could not be tied to its source. Inspect the documents and correct the value before you approve anything. |
| `summary.clearTitle` | No blockers detected. Estimator review required. |
| `summary.clearBody` | The checks found no conflict or missing requirement. That is not an engineering approval. Check each value against its source before estimating. |
| `summary.conflicts` | {n} conflict |
| `summary.conflictsPlural` | {n} conflicts |
| `summary.missing` | {n} missing requirement |
| `summary.missingPlural` | {n} missing requirements |
| `summary.needsReview` | {n} needs review |
| `summary.analyzedAt` | Analyzed {time} |

## Findings (FindingCard)

| Key | Copy |
|---|---|
| `finding.paneLabel` | Review |
| `finding.listLabel` | Findings |
| `finding.conflict` | Conflict |
| `finding.missing` | Missing |
| `finding.needs_review` | Needs review |
| `finding.conflictTitle` | {field} conflict |
| `finding.missingTitle` | {field} missing |
| `finding.needsReviewTitle` | {field} needs review |
| `finding.revisionConflict` | The RFQ and the drawing give different revisions. RevisionGate does not choose which one governs. Ask the customer. |
| `finding.materialConflict` | The RFQ and the drawing give different materials. RevisionGate does not treat materials as equivalent or pick one. Ask the customer. |
| `finding.genericConflict` | The documents give different values for {field}. Ask the customer which one applies. |
| `finding.finishMissing` | No finish was found in the RFQ or the drawing. The intake checklist requires an explicit finish, and "none" counts only when a document states it. |
| `finding.genericMissing` | No {field} was found where the intake checklist requires one. Read the documents to confirm before you ask the customer. |
| `finding.needsReviewBody` | RevisionGate could not tie this {field} to its source. Read the document and correct the value. Approval stays unavailable until you do. |
| `finding.noValue` | No value found |
| `finding.notEqual` | does not match |
| `finding.unresolved` | Unresolved |
| `finding.questionDrafted` | Question drafted |
| `finding.questionApproved` | Question approved · requirement unresolved |
| `finding.awaitingAnswer` | Unresolved · awaiting customer answer |

## Evidence and source lines (Passage, Sources)

| Key | Copy |
|---|---|
| `evidence.heading` | Source passages |
| `evidence.located` | Source passage located. Confirm its meaning. |
| `evidence.confirmed` | Meaning confirmed by estimator. |
| `evidence.corrected` | Value corrected by estimator. The source line is unchanged. |
| `evidence.notLocated` | Passage not found at the cited location. Needs review. |
| `evidence.policy` | Checklist rule, shown for reference. |
| `evidence.nothingToCite` | Nothing to cite. No value was found, so read both documents yourself. |
| `evidence.lineTagConflict` | Conflict · {field} |
| `evidence.lineTagMissing` | Rule · {field} |
| `evidence.lineTagNeedsReview` | Needs review · {field} |
| `evidence.goToFinding` | Go to finding: {title} |
| `evidence.sourcesHeading` | Source documents |
| `evidence.sourcesCount` | {n} documents |
| `evidence.lineCount` | {n} lines |

## Clarification questions

| Key | Copy |
|---|---|
| `question.label` | Question for the customer |
| `question.hint` | Keep both values in the wording. Do not pick one. |
| `question.hintMissing` | Ask for an explicit value. Do not suggest one. |
| `question.edited` | Edited |
| `question.locked` | Approved wording. Reopen the clarification to change it. |
| `question.empty` | Every question needs wording before approval. |
| `question.none` | No clarification questions. Nothing was detected that needs a customer answer. |
| `question.refs` | References |

## Extracted requirements (FieldTable)

| Key | Copy |
|---|---|
| `fields.heading` | Extracted requirements |
| `fields.summary` | Check or correct extracted values |
| `fields.body` | Compare each value with the full document. Correct a misread value here. A correction is a record of what the document says. It does not decide which document governs. |
| `fields.columnField` | Field |
| `fields.supported` | Supported |
| `fields.conflict` | Conflict |
| `fields.missing` | Missing |
| `fields.needs_review` | Needs review |
| `fields.reviewPending` | Review pending |
| `fields.reviewConfirmed` | Confirmed by estimator |
| `fields.reviewCorrected` | Corrected by estimator |
| `fields.correctAria` | Correct {source} {field} |

## Manual correction (CorrectionForm)

| Key | Copy |
|---|---|
| `correction.title` | Correct {field} in {source} |
| `correction.absent` | I read this document and found no explicit value. |
| `correction.valueLabel` | Value as written in the document |
| `correction.lineLabel` | Line that states it |
| `correction.linePlaceholder` | Select a line |
| `correction.consequence` | Saving creates a new version. The draft is rewritten and any approval is cleared. |

## Draft, stale draft, approval guard

| Key | Copy |
|---|---|
| `draft.packetHeading` | Clarification packet |
| `draft.ready` | Draft questions are ready. Review the wording before you approve. |
| `draft.edited` | Edited draft. Not yet approved. Approval saves this exact wording. |
| `draft.stale` | This review is out of date. |
| `draft.staleBody` | The packet or a value changed after these questions were written. Load the current version and review it again. |
| `draft.staleNoReplacement` | The packet changed after this analysis. Analyze again to review the current packet. |
| `draft.previousHeading` | Previous wording from the cleared draft |
| `draft.draftMissing` | Draft needs a refresh. |
| `draft.draftMissingBody` | The extracted values are saved, but the questions were not written. Refresh the draft to continue. |
| `draft.attestation` | Approving confirms you read all three documents, checked each passage against its finding, and reviewed the wording. It approves the questions only. |
| `draft.attestationNoQuestions` | There are no questions to send. Approving records that you reviewed this packet. It is not an engineering approval. |
| `draft.approveCaption` | Downloads the approved, source-linked packet. |
| `draft.blockedByNeedsReview` | Correct the values marked Needs review before approving. |
| `draft.blockedByStale` | Load the current version before approving. |
| `draft.blockedGeneric` | Approval is not available for this version yet. |

## Approval, awaiting response, export

| Key | Copy |
|---|---|
| `approval.title` | Clarification approved. Requirements remain unresolved. |
| `approval.titleNoBlockers` | Review recorded. No clarification needed. |
| `approval.detail` | Approved {time} by the estimator role. Draft version {version}. |
| `approval.blockedBody` | The quote stays blocked until the customer confirms the governing requirements. |
| `approval.clearBody` | Engineering readiness still depends on your own review before estimating. |
| `approval.awaiting` | Awaiting customer response. |
| `approval.awaitingBody` | RevisionGate does not send email. Send the downloaded packet yourself. When the customer answers, analyze the updated packet. |
| `approval.exportStarted` | Packet download started. |
| `approval.exported` | Packet downloaded: {filename} |

## Errors, timeout, retry, manual review

| Key | Copy |
|---|---|
| `error.analysisTitle` | Analysis did not finish |
| `error.analysisBody` | No findings were produced. Your packet is unchanged and still on screen. |
| `error.extractionDetail` | The model returned a response RevisionGate could not read, even after one automatic retry. |
| `error.timeoutDetail` | The model did not respond in time. |
| `error.serviceDetail` | RevisionGate could not reach the model service. |
| `error.retryHint` | Try again. If it keeps failing, read the documents and review the packet by hand. |
| `error.requestTitle` | Request unsuccessful |
| `error.requestBody` | Nothing was saved. Your edits are still on screen. |
| `error.staleTitle` | Current review unavailable |
| `error.packetsTitle` | Packets did not load |
| `error.manualTitle` | Reviewing by hand |
| `error.manualBody` | Read the RFQ and the drawing line by line. Compare part, revision, and material, and confirm a finish is stated. Nothing is approved in RevisionGate until an analysis finishes. |

## Run details and recorded-run label

| Key | Copy |
|---|---|
| `provenance.heading` | Run details |
| `provenance.live` | Live model run |
| `provenance.recordedIbm` | Recorded IBM run |
| `provenance.recordedOther` | Recorded model run |
| `provenance.recordedBody` | Replaying a saved run from {time}. No live model call is being made in this view. |
| `provenance.preview` | Synthetic preview |
| `provenance.previewBody` | Design preview with scripted data. No model call was made. |
| `provenance.mode` | Mode |
| `provenance.provider` | Provider |
| `provenance.model` | Model |
| `provenance.started` | Started |
| `provenance.run` | Run ID |
| `provenance.versions` | Versions |
| `provenance.versionsValue` | Run {run} · Draft {draft} |
| `provenance.rules` | Rules |
| `provenance.hash` | Source hash |
| `provenance.storage` | This demo keeps runs in memory. Download the packet to keep a record. |

## Six demo-video captions

| Key | Copy |
|---|---|
| `captions.c1` | An estimator at a small Michigan CNC shop opens the next RFQ. |
| `captions.c2` | The RFQ asks for revision C in 6061-T6. The drawing says revision B in 7075-T6. No finish is stated. |
| `captions.c3` | Analyze packet. The model extracts each document's requirements. Fixed checks flag two conflicts and one missing requirement. |
| `captions.c4` | Review evidence. Every finding opens beside its exact source lines. The estimator checks the meaning and edits the questions. |
| `captions.c5` | Approve clarification packet. The questions download. The quote stays blocked until the customer answers. |
| `captions.c6` | Pilot target: blocker review in five minutes instead of twenty. A target, not a measured result. |

## Labels

| Key | Copy |
|---|---|
| `fieldLabel.part_id` | Part ID |
| `fieldLabel.quantity` | Quantity |
| `fieldLabel.revision` | Revision |
| `fieldLabel.material` | Material |
| `fieldLabel.finish` | Finish |
| `sourceLabel.RFQ` | RFQ · Request for quotation · Customer request |
| `sourceLabel.DRAWING` | Drawing · Drawing notes · Engineering document |
| `sourceLabel.CHECKLIST` | Checklist · Shop intake checklist · Shop rule |
| `packetLabel.01_conflicted` | 01 · Conflicted packet |
| `packetLabel.02_material_changed` | 02 · Material changed |
| `packetLabel.03_complete` | 03 · Complete packet |
| `packetLabel.04_injection` | 04 · Embedded instruction |

// RevisionGate interface copy. Every string the estimator reads lives here,
// keyed by component and state. Edit wording here, not in components.
// Rules that wording must keep (see design/copy/VOICE_GUIDE.md):
//  - The system "finds", "locates", "detects". Only a person "confirms", "approves", "corrects".
//  - Approval covers the clarification packet. It never resolves a requirement.
//  - Provider and model names come from run provenance, never from this file.
import type { FieldName, SourceId } from "../types";

export const fieldLabel: Record<FieldName, string> = {
  part_id: "Part ID", quantity: "Quantity", revision: "Revision", material: "Material", finish: "Finish",
};

export const sourceLabel: Record<SourceId, { short: string; title: string; type: string }> = {
  RFQ: { short: "RFQ", title: "Request for quotation", type: "Customer request" },
  DRAWING: { short: "Drawing", title: "Drawing notes", type: "Engineering document" },
  CHECKLIST: { short: "Checklist", title: "Shop intake checklist", type: "Shop rule" },
};

export const packetLabel: Record<string, string> = {
  "01_conflicted": "01 · Conflicted packet",
  "02_material_changed": "02 · Material changed",
  "03_complete": "03 · Complete packet",
  "04_injection": "04 · Embedded instruction",
};

/** Fill {placeholders} in a template string. */
export function t(template: string, vars: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(vars[key] ?? ""));
}

export const copy = {
  product: {
    name: "RevisionGate",
    descriptor: "RFQ review gate",
    intro: "RevisionGate compares an RFQ with its drawing notes, shows where they disagree beside the source lines, and prepares clarification questions for an estimator to review and approve.",
    description: "RevisionGate is an RFQ review gate for estimators at small CNC shops. It extracts the part, quantity, revision, material, and finish from an RFQ and its drawing notes, shows conflicting or missing requirements beside the exact source lines, and drafts clarification questions. The estimator checks the evidence and approves the questions. Conflicting requirements stay blocked until the customer answers.",
  },

  topbar: {
    pageTitle: "RFQ packet review",
    skip: "Skip to review",
    packetLabel: "Packet",
    packetsLoading: "Loading packets…",
    packetsUnavailable: "Packets unavailable",
    synthetic: "Synthetic demo",
    syntheticHint: "Fictional packet. No customer records.",
    partLabel: "Part",
    partUnknown: "Not analyzed yet",
    readinessLabel: "Quote readiness",
  },

  readiness: {
    not_analyzed: "Not analyzed",
    analyzing: "Analyzing",
    blocked: "Blocked",
    needs_review: "Needs review",
    no_detected_blockers_pending_human_review: "No blockers detected · Review required",
    out_of_date: "Out of date",
  },

  hero: {
    heading: "Catch RFQ conflicts before quoting starts.",
    body: "RevisionGate reads the RFQ, drawing notes, and intake checklist, then shows conflicting or missing requirements beside their source lines. You check the evidence and approve the questions for your customer.",
    stepsLabel: "Three steps",
    step1: "Pull part, quantity, revision, material, and finish from each document.",
    step2: "Check every finding against its source lines. Edit the questions.",
    step3: "Download the questions. The quote stays blocked until the customer answers.",
    noPacket: "Select a packet to begin.",
    noPacketsBody: "The packet list did not load. Your work is not affected.",
  },

  actions: {
    analyze: "Analyze packet",
    analyzing: "Analyzing packet…",
    reanalyze: "Analyze again",
    retry: "Try again",
    review: "Review evidence",
    approve: "Approve clarification packet",
    download: "Download packet",
    reopen: "Edit clarification",
    refreshDraft: "Refresh draft",
    loadCurrent: "Load current version",
    retryPackets: "Retry",
    showEvidence: "Show evidence",
    hideEvidence: "Hide evidence",
    showInDocument: "Show in document",
    correct: "Correct value",
    saveCorrection: "Save correction",
    cancel: "Cancel",
  },

  steps: {
    counter: "Step {n} of 3",
    analyze: "Analyze",
    review: "Review",
    approve: "Approve",
    complete: "Clarification approved",
  },

  loading: {
    heading: "Analyzing packet",
    body: "Your documents stay on screen. Findings appear here when the run finishes.",
    listLabel: "This run will",
    step1: "Read the three source documents",
    step2: "Extract requirements from each document",
    step3: "Check that each cited passage exists in its source",
    step4: "Compare revision, material, and finish",
    step5: "Draft clarification questions",
    announce: "Analyzing packet. Please wait.",
    working: "{label}…",
  },

  summary: {
    blockedTitle: "Quote blocked. Customer clarification required.",
    blockedBody: "The documents disagree or a required value is missing. RevisionGate does not choose which requirement governs.",
    needsReviewTitle: "Needs review. Check the marked values.",
    needsReviewBody: "At least one value could not be tied to its source. Inspect the documents and correct the value before you approve anything.",
    clearTitle: "No blockers detected. Estimator review required.",
    clearBody: "The checks found no conflict or missing requirement. That is not an engineering approval. Check each value against its source before estimating.",
    conflicts: "{n} conflict",
    conflictsPlural: "{n} conflicts",
    missing: "{n} missing requirement",
    missingPlural: "{n} missing requirements",
    needsReview: "{n} needs review",
    analyzedAt: "Analyzed {time}",
  },

  finding: {
    paneLabel: "Review",
    listLabel: "Findings",
    conflict: "Conflict",
    missing: "Missing",
    needs_review: "Needs review",
    conflictTitle: "{field} conflict",
    missingTitle: "{field} missing",
    needsReviewTitle: "{field} needs review",
    revisionConflict: "The RFQ and the drawing give different revisions. RevisionGate does not choose which one governs. Ask the customer.",
    materialConflict: "The RFQ and the drawing give different materials. RevisionGate does not treat materials as equivalent or pick one. Ask the customer.",
    genericConflict: "The documents give different values for {field}. Ask the customer which one applies.",
    finishMissing: "No finish was found in the RFQ or the drawing. The intake checklist requires an explicit finish, and \"none\" counts only when a document states it.",
    genericMissing: "No {field} was found where the intake checklist requires one. Read the documents to confirm before you ask the customer.",
    needsReviewBody: "RevisionGate could not tie this {field} to its source. Read the document and correct the value. Approval stays unavailable until you do.",
    noValue: "No value found",
    notEqual: "does not match",
    unresolved: "Unresolved",
    questionDrafted: "Question drafted",
    questionApproved: "Question approved · requirement unresolved",
    awaitingAnswer: "Unresolved · awaiting customer answer",
  },

  evidence: {
    heading: "Source passages",
    located: "Source passage located. Confirm its meaning.",
    confirmed: "Meaning confirmed by estimator.",
    corrected: "Value corrected by estimator. The source line is unchanged.",
    notLocated: "Passage not found at the cited location. Needs review.",
    policy: "Checklist rule, shown for reference.",
    nothingToCite: "Nothing to cite. No value was found, so read both documents yourself.",
    lineTagConflict: "Conflict · {field}",
    lineTagMissing: "Rule · {field}",
    lineTagNeedsReview: "Needs review · {field}",
    goToFinding: "Go to finding: {title}",
    sourcesHeading: "Source documents",
    sourcesCount: "{n} documents",
    lineCount: "{n} lines",
  },

  question: {
    label: "Question for the customer",
    hint: "Keep both values in the wording. Do not pick one.",
    hintMissing: "Ask for an explicit value. Do not suggest one.",
    edited: "Edited",
    locked: "Approved wording. Reopen the clarification to change it.",
    empty: "Every question needs wording before approval.",
    none: "No clarification questions. Nothing was detected that needs a customer answer.",
    refs: "References",
  },

  fields: {
    heading: "Extracted requirements",
    summary: "Check or correct extracted values",
    body: "Compare each value with the full document. Correct a misread value here. A correction is a record of what the document says. It does not decide which document governs.",
    columnField: "Field",
    supported: "Supported",
    conflict: "Conflict",
    missing: "Missing",
    needs_review: "Needs review",
    reviewPending: "Review pending",
    reviewConfirmed: "Confirmed by estimator",
    reviewCorrected: "Corrected by estimator",
    correctAria: "Correct {source} {field}",
  },

  correction: {
    title: "Correct {field} in {source}",
    absent: "I read this document and found no explicit value.",
    valueLabel: "Value as written in the document",
    lineLabel: "Line that states it",
    linePlaceholder: "Select a line",
    consequence: "Saving creates a new version. The draft is rewritten and any approval is cleared.",
  },

  draft: {
    packetHeading: "Clarification packet",
    ready: "Draft questions are ready. Review the wording before you approve.",
    edited: "Edited draft. Not yet approved. Approval saves this exact wording.",
    stale: "This review is out of date.",
    staleBody: "The packet or a value changed after these questions were written. Load the current version and review it again.",
    staleNoReplacement: "The packet changed after this analysis. Analyze again to review the current packet.",
    previousHeading: "Previous wording from the cleared draft",
    draftMissing: "Draft needs a refresh.",
    draftMissingBody: "The extracted values are saved, but the questions were not written. Refresh the draft to continue.",
    attestation: "Approving confirms you read all three documents, checked each passage against its finding, and reviewed the wording. It approves the questions only.",
    attestationNoQuestions: "There are no questions to send. Approving records that you reviewed this packet. It is not an engineering approval.",
    approveCaption: "Downloads the approved, source-linked packet.",
    blockedByNeedsReview: "Correct the values marked Needs review before approving.",
    blockedByStale: "Load the current version before approving.",
    blockedGeneric: "Approval is not available for this version yet.",
  },

  approval: {
    title: "Clarification approved. Requirements remain unresolved.",
    titleNoBlockers: "Review recorded. No clarification needed.",
    detail: "Approved {time} by the estimator role. Draft version {version}.",
    blockedBody: "The quote stays blocked until the customer confirms the governing requirements.",
    clearBody: "Engineering readiness still depends on your own review before estimating.",
    awaiting: "Awaiting customer response.",
    awaitingBody: "RevisionGate does not send email. Send the downloaded packet yourself. When the customer answers, analyze the updated packet.",
    exportStarted: "Packet download started.",
    exported: "Packet downloaded: {filename}",
  },

  error: {
    analysisTitle: "Analysis did not finish",
    analysisBody: "No findings were produced. Your packet is unchanged and still on screen.",
    extractionDetail: "The model returned a response RevisionGate could not read, even after one automatic retry.",
    timeoutDetail: "The model did not respond in time.",
    serviceDetail: "RevisionGate could not reach the model service.",
    retryHint: "Try again. If it keeps failing, read the documents and review the packet by hand.",
    requestTitle: "Request unsuccessful",
    requestBody: "Nothing was saved. Your edits are still on screen.",
    staleTitle: "Current review unavailable",
    packetsTitle: "Packets did not load",
    manualTitle: "Reviewing by hand",
    manualBody: "Read the RFQ and the drawing line by line. Compare part, revision, and material, and confirm a finish is stated. Nothing is approved in RevisionGate until an analysis finishes.",
  },

  provenance: {
    heading: "Run details",
    live: "Live model run",
    recordedIbm: "Recorded IBM run",
    recordedOther: "Recorded model run",
    recordedBody: "Replaying a saved run from {time}. No live model call is being made in this view.",
    preview: "Synthetic preview",
    previewBody: "Design preview with scripted data. No model call was made.",
    mode: "Mode",
    provider: "Provider",
    model: "Model",
    started: "Started",
    run: "Run ID",
    versions: "Versions",
    versionsValue: "Run {run} · Draft {draft}",
    rules: "Rules",
    hash: "Source hash",
    storage: "This demo keeps runs in memory. Download the packet to keep a record.",
  },

  captions: {
    c1: "An estimator at a small Michigan CNC shop opens the next RFQ.",
    c2: "The RFQ asks for revision C in 6061-T6. The drawing says revision B in 7075-T6. No finish is stated.",
    c3: "Analyze packet. The model extracts each document's requirements. Fixed checks flag two conflicts and one missing requirement.",
    c4: "Review evidence. Every finding opens beside its exact source lines. The estimator checks the meaning and edits the questions.",
    c5: "Approve clarification packet. The questions download. The quote stays blocked until the customer answers.",
    c6: "Pilot target: blocker review in five minutes instead of twenty. A target, not a measured result.",
  },
} as const;

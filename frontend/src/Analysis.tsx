import { AlertOctagon, ArrowRight, Check, ChevronRight, CircleDashed, ClipboardCheck, FileSearch, ListChecks, LoaderCircle, PencilLine, ScanLine, ShieldCheck, TriangleAlert, Download } from "lucide-react";
import { Passage } from "./Documents";
import { FieldReview } from "./FieldReview";
import { fields } from "./labels";
import type { Correction, Finding, Packet, Question, Run } from "./types";

function FindingCard({ finding, packet, reviewing, question, editable, onEdit }: {
  finding: Finding; packet: Packet; reviewing: boolean; question?: Question; editable: boolean; onEdit: (id: string, text: string) => void;
}) {
  const { kind, field, values } = finding;
  const label = kind === "conflict" ? "Conflict" : kind === "missing" ? "Missing" : "Needs review";
  const Icon = kind === "conflict" ? AlertOctagon : kind === "missing" ? TriangleAlert : CircleDashed;
  return <article className="finding-card">
    <div className="finding-head"><div><span className={"kind " + (kind === "conflict" ? "danger" : "warn")}><Icon/>{label}</span><h3>{fields[field]}</h3></div></div>
    {kind === "conflict" && <div className="compared">{Object.entries(values).map(([id,value]) => <div key={id}><small>{id}</small><strong>{value ?? "No value extracted"}</strong></div>)}</div>}
    {kind === "missing" && <p className="finding-note">The required {fields[field].toLowerCase()} is missing from the extraction. Inspect the applicable sources for an explicit value.</p>}
    {kind === "needs_review" && <p className="finding-note">Inspect the source and correct the extracted {fields[field].toLowerCase()} where needed.</p>}
    {reviewing && <div className="evidence-body">
      {[...finding.evidence_refs, ...finding.policy_refs].map(ref => <Passage key={ref} reference={ref} docs={packet.sources}/>)}
      {question && <label className="question"><span><PencilLine/>Clarification question</span>
        <textarea rows={3} maxLength={1000} value={question.question} readOnly={!editable} aria-label={fields[field] + " clarification question"} onChange={e => onEdit(finding.finding_id, e.target.value)}/></label>}
      <small className="semantic-state">{finding.semantic_review_status === "pending" ? "Needs review · Confirm meaning and completeness." : "Estimator review · " + finding.semantic_review_status}</small>
    </div>}
  </article>;
}

type Props = {
  packet: Packet; run: Run | null; reviewing: boolean; disabled: boolean; stale: boolean;
  busy: string; error: boolean; edited: boolean; questions: Question[]; onReview: () => void;
  onEdit: (id: string, text: string) => void; onCorrect: (correction: Correction) => Promise<boolean>;
  onApprove: () => void; onDownload: () => void; onReopen: () => void; onRedraft: () => void;
};
export function Analysis(props: Props) {
  const { packet, run, reviewing, disabled, stale, busy, edited, questions } = props;
  const hasExtraction = !!run?.extracted_fields?.RFQ;
  const approved = !!run?.clarification.approval && !stale;
  const isAnalyzing = busy === "Analyzing packet";
  return <section className="panel analysis" aria-labelledby="analysis-heading">
    <header className="panel-heading"><div className="heading-pair"><ListChecks/><h2 id="analysis-heading">Analysis &amp; findings</h2></div>
      {run?.analysis.status === "succeeded" && !stale && <span className="counter">{run.findings.length} findings</span>}
    </header>
    {!hasExtraction || !run ? <>
      <div className="analysis-empty">
        <div aria-hidden="true" className={"scan-visual" + (isAnalyzing ? " in-progress" : "")}><div className="scan-corners"><FileSearch strokeWidth={1.35}/></div></div>
        <h3>{isAnalyzing ? "Analyzing source documents" : props.error ? "Analysis unavailable" : "Ready for analysis"}</h3>
        <p>{isAnalyzing ? "Extracting requirements, validating source passages, and drafting clarification questions." : props.error ? "Your packet is available for inspection. Retry analysis when the service is ready." : "Analyze this packet to compare requirements and prepare source-linked questions."}</p>
      </div>
      <div className="workflow-foot"><span>Extraction</span><ChevronRight/><span>Evidence review</span><ChevronRight/><span>Clarification</span></div>
    </> : <>
      <div className="findings-inner">
        {stale && <div className="callout warn" role="status"><TriangleAlert/><div><strong>Previous analysis</strong><p>This version is stale. Analyze again to review the current packet.</p></div></div>}
        <div className="results-heading"><span className="eyelabel">Findings summary</span>{run.provenance.started_at && <time dateTime={run.provenance.started_at} title={run.provenance.started_at}>{new Date(run.provenance.started_at).toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"})}</time>}</div>
        {run.findings.length === 0 && <div className="callout neutral"><ClipboardCheck/><div><strong>{run.analysis.status === "succeeded" ? "No blockers detected" : "Extraction needs review"}</strong><p>Estimator review of all fields and sources is required.</p></div></div>}
        {run.findings.map(f => <FindingCard key={f.finding_id} finding={f} packet={packet} reviewing={reviewing}
          question={questions.find(q => q.finding_id === f.finding_id)} editable={!disabled && !approved && run.allowed_actions.edit_draft} onEdit={props.onEdit}/>)}
        {!reviewing && <button className="btn primary review-btn" onClick={props.onReview} disabled={disabled || !run.allowed_actions.review_evidence}><ScanLine/>Review evidence<ArrowRight/></button>}
        {reviewing && <>
          <FieldReview key={run.run_id} run={run} disabled={disabled} onCorrect={props.onCorrect}/>
          <div className="review-footer" id="clarification-packet" tabIndex={-1}>
            <div className="heading-pair"><ShieldCheck/><h3>Clarification packet</h3></div>
            {approved ? <>
              <strong className="approved"><Check/>Clarification approved</strong><p>{run.quote_readiness === "blocked" ? "Quote blocked. Requirements remain unresolved while awaiting customer clarification." : "Engineering readiness remains subject to estimator review."}</p>
              <div className="button-row"><button className="btn primary" disabled={disabled || !run.allowed_actions.download_export} onClick={props.onDownload}><Download/>Download packet</button>
                <button className="btn plain" onClick={props.onReopen} disabled={disabled || !run.allowed_actions.edit_draft}><PencilLine/>Edit clarification</button></div>
            </> : <>
              <p>By approving, I confirm that I inspected all three sources, checked extraction meaning and completeness, and reviewed the questions. This approves the clarification wording only.</p>
              {edited && <div className="draft-note">Edited draft · Awaiting approval</div>}
              {run.clarification.status === "not_started" && run.allowed_actions.correct_fields && <button className="btn plain" disabled={disabled} onClick={props.onRedraft}><FileSearch/>Retry drafting</button>}
              <button className="btn primary approve-btn" onClick={props.onApprove} disabled={disabled || !run.allowed_actions.approve_clarification || questions.some(q => !q.question.trim())}><Download/>Approve clarification packet</button>
              <span className="action-caption">Downloads the current, source-linked packet.</span>
            </>}
          </div>
        </>}
      </div>
    </>}
    {busy && !isAnalyzing && <div className="inline-progress"><LoaderCircle className="spinner"/>{busy}…</div>}
  </section>;
}

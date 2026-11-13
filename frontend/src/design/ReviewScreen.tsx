// RevisionGate review screen: presentation only.
// Everything shown comes from props. This file never compares values, decides
// readiness, clears a blocker, or calls a service. The container (src/main.tsx)
// owns state and passes callbacks named in handoffs/SHARED_CONTRACT.json.
import { Fragment, useEffect, useId, useLayoutEffect, useRef, useState, type FormEvent, type ReactNode, type RefObject } from "react";
import {
  AlertOctagon, ArrowRight, Check, ChevronDown, CircleDashed, Clock, Download, Eye, FlaskConical, History,
  LoaderCircle, LocateFixed, PencilLine, RotateCcw, ScanLine, TriangleAlert, X,
} from "lucide-react";
import { engineeringSources, fieldNames } from "../types";
import type { Correction, FieldName, Finding, Packet, Question, Run, Source, SourceId, Value } from "../types";
import { lines } from "../labels";
import { copy, fieldLabel, packetLabel, sourceLabel, t } from "./copy";
import { Logo } from "./Logo";
import "./revisiongate.css";

export type ReviewScreenProps = {
  /** Packet selection */
  packets: Packet[];
  packetId: string;
  packetsLoading?: boolean;
  packet?: Packet;
  /** Authoritative run from the backend, or null before the first analysis */
  run: Run | null;
  /** Container state */
  questions: Question[];
  /** Wording kept from a draft that was cleared by a correction. Shown read-only. */
  previousDraft?: Question[];
  reviewing: boolean;
  analyzing: boolean;
  busy: string;
  error: string;
  notice: string;
  stale: boolean;
  edited: boolean;
  canLoadReplacement?: boolean;
  /** Set only when replaying a saved run. Shows the recorded-run label. */
  recordedAt?: string;
  /** Set only by the design gallery. Shows the synthetic-preview label. */
  preview?: boolean;
  /** Shared-contract callbacks */
  onAnalyzePacket: () => void;
  onReviewEvidence: () => void;
  onCorrectField: (correction: Correction) => Promise<boolean> | void;
  onEditDraft: (findingId: string, text: string) => void;
  onApproveClarification: () => void;
  onDownloadExport: () => void;
  /** Container actions that already exist in src/main.tsx */
  onSelectPacket: (packetId: string) => void;
  onReopenDraft?: () => void;
  onRefreshDraft?: () => void;
  onLoadReplacement?: () => void;
  onRetryPackets?: () => void;
};

type Tone = "danger" | "warn" | "review" | "neutral" | "ok";
type Kind = Finding["kind"];
type Note = { findingId: string; kind: Kind; field: FieldName; role: "evidence" | "policy" };
type Span = { start: number; end: number; tone: "conflict" | "attention" | "located" };

const kindTone: Record<Kind, Tone> = { conflict: "danger", missing: "warn", needs_review: "warn" };
const kindIcon = { conflict: AlertOctagon, missing: CircleDashed, needs_review: Eye };
const cx = (...names: (string | false | null | undefined)[]) => names.filter(Boolean).join(" ");
const time = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
const reducedMotion = () => typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

function findingTitle(f: Finding) {
  const template = f.kind === "conflict" ? copy.finding.conflictTitle : f.kind === "missing" ? copy.finding.missingTitle : copy.finding.needsReviewTitle;
  return t(template, { field: fieldLabel[f.field] });
}
function findingExplain(f: Finding) {
  const field = fieldLabel[f.field].toLowerCase();
  if (f.kind === "conflict") return f.field === "revision" ? copy.finding.revisionConflict : f.field === "material" ? copy.finding.materialConflict : t(copy.finding.genericConflict, { field });
  if (f.kind === "missing") return f.field === "finish" ? copy.finding.finishMissing : t(copy.finding.genericMissing, { field });
  return t(copy.finding.needsReviewBody, { field });
}

/** Which findings point at which source line. A lookup, not a rule. */
function collectNotes(run: Run) {
  const notes = new Map<string, Note[]>();
  for (const f of run.findings) {
    const add = (ref: string, role: Note["role"]) => notes.set(ref, [...(notes.get(ref) ?? []), { findingId: f.finding_id, kind: f.kind, field: f.field, role }]);
    f.evidence_refs.forEach(ref => add(ref, "evidence"));
    f.policy_refs.forEach(ref => add(ref, "policy"));
  }
  return notes;
}
function collectSpans(run: Run, source: SourceId) {
  const spans = new Map<string, Span[]>();
  const fields = run.extracted_fields[source];
  if (!fields) return spans;
  for (const field of fieldNames) {
    const related = run.findings.find(f => f.field === field && source in f.values);
    const tone: Span["tone"] = related?.kind === "conflict" ? "conflict" : related?.kind === "needs_review" ? "attention" : "located";
    for (const e of fields[field]?.evidence ?? []) {
      if (e.source_id !== source) continue;
      spans.set(e.line_id, [...(spans.get(e.line_id) ?? []), { start: e.char_start, end: e.char_end, tone }]);
    }
  }
  return spans;
}

/** Offsets are Unicode code points into the line body, end exclusive. */
function Highlighted({ body, spans }: { body: string; spans: Span[] }) {
  const chars = Array.from(body);
  const out: ReactNode[] = [];
  let cursor = 0;
  for (const span of [...spans].sort((a, b) => a.start - b.start)) {
    if (span.end <= cursor || span.start >= chars.length) continue;
    out.push(chars.slice(cursor, span.start).join(""));
    out.push(<mark key={span.start + "-" + span.end} className={"rg-hl rg-hl--" + span.tone}>{chars.slice(Math.max(cursor, span.start), span.end).join("")}</mark>);
    cursor = span.end;
  }
  out.push(chars.slice(cursor).join(""));
  return <>{out}</>;
}

function useNarrow(ref: RefObject<HTMLElement | null>, max = 900) {
  const [narrow, setNarrow] = useState(false);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => setNarrow(entry.contentRect.width < max));
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref, max]);
  return narrow;
}

function Sources({ docs, run, uid, activeRef, lineId, onGoToFinding }: {
  docs: Source[]; run: Run | null; uid: string; activeRef: string; lineId: (ref: string) => string; onGoToFinding: (id: string) => void;
}) {
  const notes = run ? collectNotes(run) : new Map<string, Note[]>();
  return <section className="rg-pane rg-sources" aria-labelledby={uid + "-sources"}>
    <header className="rg-pane-head">
      <h2 id={uid + "-sources"}>{copy.evidence.sourcesHeading}</h2>
      <span className="rg-count">{t(copy.evidence.sourcesCount, { n: docs.length })}</span>
    </header>
    {docs.length === 0 && <p className="rg-empty">{copy.hero.noPacket}</p>}
    {docs.map(doc => {
      const docLines = lines(doc.text);
      const spans = run ? collectSpans(run, doc.source_id) : new Map<string, Span[]>();
      const headId = uid + "-doc-" + doc.source_id;
      return <article className="rg-doc" key={doc.source_id} aria-labelledby={headId}>
        <header className="rg-doc-head">
          <div><span className="rg-eyebrow">{sourceLabel[doc.source_id].type}</span><h3 id={headId}>{sourceLabel[doc.source_id].title}</h3></div>
          <span className="rg-chip rg-mono">{doc.source_id} · {t(copy.evidence.lineCount, { n: docLines.length })}</span>
        </header>
        <ol className="rg-lines">
          {docLines.map(line => {
            const ref = doc.source_id + ":" + line.id;
            const lineNotes = notes.get(ref) ?? [];
            const evidence = lineNotes.filter(n => n.role === "evidence");
            const tone = evidence.some(n => n.kind === "conflict") ? "conflict" : evidence.length ? "attention" : lineNotes.length ? "policy" : "";
            return <li key={line.id} id={lineId(ref)} tabIndex={-1} className={cx("rg-line", tone && "rg-line--" + tone, activeRef === ref && "is-active")}>
              <span className="rg-line-id rg-mono">{line.id}</span>
              <span className="rg-line-body"><Highlighted body={line.body} spans={spans.get(line.id) ?? []} /></span>
              {lineNotes.length > 0 && <span className="rg-line-tags">
                {lineNotes.map(note => {
                  const Icon = note.role === "policy" ? Check : kindIcon[note.kind];
                  const label = t(note.role === "policy" ? copy.evidence.lineTagMissing : note.kind === "conflict" ? copy.evidence.lineTagConflict : copy.evidence.lineTagNeedsReview, { field: fieldLabel[note.field] });
                  const finding = run?.findings.find(f => f.finding_id === note.findingId);
                  return <button type="button" key={note.findingId + note.role} className={cx("rg-linetag", "rg-tone-" + (note.role === "policy" ? "review" : kindTone[note.kind]))}
                    onClick={() => onGoToFinding(note.findingId)} aria-label={t(copy.evidence.goToFinding, { title: finding ? findingTitle(finding) : label })}>
                    {note.role === "policy" ? null : <Icon />}{label}
                  </button>;
                })}
              </span>}
            </li>;
          })}
        </ol>
      </article>;
    })}
  </section>;
}

function Passage({ reference, run, docs, field, policy, onShow }: {
  reference: string; run: Run; docs: Source[]; field: FieldName; policy?: boolean; onShow: (ref: string) => void;
}) {
  const [source, id] = reference.split(":") as [SourceId, string];
  const doc = docs.find(d => d.source_id === source);
  const body = doc ? lines(doc.text).find(l => l.id === id)?.body : undefined;
  const spans = policy ? [] : (collectSpans(run, source).get(id) ?? []).filter(span => (run.extracted_fields[source]?.[field]?.evidence ?? []).some(e => e.line_id === id && e.char_start === span.start));
  const review = run.field_states?.[source]?.[field]?.semantic_review_status;
  const state = policy ? { icon: null, text: copy.evidence.policy, tone: "review" as Tone }
    : body === undefined ? { icon: <Eye />, text: copy.evidence.notLocated, tone: "warn" as Tone }
    : review === "confirmed" ? { icon: <Check />, text: copy.evidence.confirmed, tone: "ok" as Tone }
    : review === "corrected" ? { icon: <PencilLine />, text: copy.evidence.corrected, tone: "review" as Tone }
    : { icon: <LocateFixed />, text: copy.evidence.located, tone: "review" as Tone };
  return <figure className={cx("rg-passage", policy && "rg-passage--policy")}>
    <figcaption>
      <span className="rg-mono">{policy ? sourceLabel.CHECKLIST.short : sourceLabel[source]?.short ?? source} · {id}</span>
      <button type="button" className="rg-link" onClick={() => onShow(reference)}>{copy.actions.showInDocument}</button>
    </figcaption>
    <blockquote>{body === undefined ? "—" : <Highlighted body={body} spans={spans} />}</blockquote>
    <p className={cx("rg-passage-state", "rg-text-" + state.tone)}>{state.icon}{state.text}</p>
  </figure>;
}

function FindingCard({ f, run, docs, question, open, canToggle, editable, domId, onToggle, onEdit, onShow }: {
  f: Finding; run: Run; docs: Source[]; question?: Question; open: boolean; canToggle: boolean; editable: boolean; domId: string;
  onToggle: () => void; onEdit: (id: string, text: string) => void; onShow: (ref: string) => void;
}) {
  const Icon = kindIcon[f.kind];
  const entries = Object.entries(f.values) as [SourceId, Value][];
  const approval = run.clarification.approval;
  const stateText = approval ? (run.clarification.status === "awaiting_customer_response" ? copy.finding.awaitingAnswer : copy.finding.questionApproved)
    : question ? copy.finding.questionDrafted : copy.finding.unresolved;
  const isEdited = !!question && run.questions.find(q => q.finding_id === f.finding_id)?.question !== question.question;
  const qid = domId + "-q";
  return <article className={cx("rg-finding", "rg-finding--" + f.kind)} id={domId} tabIndex={-1} aria-labelledby={domId + "-t"}>
    <header className="rg-finding-head">
      <span className={cx("rg-kind", "rg-tone-" + kindTone[f.kind])}><Icon />{copy.finding[f.kind]}</span>
      <h3 id={domId + "-t"}>{findingTitle(f)}</h3>
      <span className="rg-finding-state">{stateText}</span>
    </header>
    {entries.length > 0 && <div className="rg-versus" role="group" aria-label={findingTitle(f)}>
      {entries.map(([source, value], index) => {
        const ref = f.evidence_refs.find(r => r.startsWith(source + ":"));
        return <Fragment key={source}>
          {index > 0 && f.kind === "conflict" && <span className="rg-versus-op" role="img" aria-label={copy.finding.notEqual}>≠</span>}
          <div className={cx("rg-value", value == null && "rg-value--empty")}>
            <span className="rg-value-src">{sourceLabel[source]?.short ?? source}{ref && <span className="rg-mono"> · {ref.split(":")[1]}</span>}</span>
            <strong className={value == null ? undefined : "rg-mono"}>{value ?? copy.finding.noValue}</strong>
          </div>
        </Fragment>;
      })}
    </div>}
    <p className="rg-finding-note">{findingExplain(f)}</p>
    {canToggle && <button type="button" className="rg-btn rg-btn--quiet rg-btn--sm rg-finding-toggle" aria-expanded={open} aria-controls={domId + "-ev"} onClick={onToggle}>
      {open ? copy.actions.hideEvidence : copy.actions.showEvidence}<ChevronDown className={open ? "rg-flip" : undefined} />
    </button>}
    {open && <div className="rg-evidence" id={domId + "-ev"}>
      <h4 className="rg-eyebrow">{copy.evidence.heading}</h4>
      {f.evidence_refs.length > 0
        ? <div className="rg-passages">{f.evidence_refs.map(ref => <Passage key={ref} reference={ref} run={run} docs={docs} field={f.field} onShow={onShow} />)}</div>
        : <p className="rg-passage-state rg-text-warn"><CircleDashed />{copy.evidence.nothingToCite}</p>}
      {f.policy_refs.length > 0 && <div className="rg-passages rg-passages--policy">{f.policy_refs.map(ref => <Passage key={ref} reference={ref} run={run} docs={docs} field={f.field} policy onShow={onShow} />)}</div>}
      {question && <div className="rg-question">
        <div className="rg-question-head">
          <label htmlFor={qid}>{copy.question.label}</label>
          {isEdited && <span className="rg-chip rg-tone-warn"><PencilLine />{copy.question.edited}</span>}
        </div>
        <textarea id={qid} rows={3} maxLength={1000} value={question.question} readOnly={!editable} aria-describedby={qid + "-h"}
          aria-invalid={!question.question.trim() || undefined} onChange={e => onEdit(f.finding_id, e.target.value)} />
        <p id={qid + "-h"} className="rg-hint">
          {!question.question.trim() ? copy.question.empty : approval ? copy.question.locked : f.kind === "conflict" ? copy.question.hint : copy.question.hintMissing}
        </p>
        <p className="rg-refs"><span>{copy.question.refs}</span> <span className="rg-mono">{[...question.evidence_refs, ...question.policy_refs].join(" · ") || "—"}</span></p>
      </div>}
    </div>}
  </article>;
}

function CorrectionForm({ run, source, field, disabled, onSave, onClose }: {
  run: Run; source: SourceId; field: FieldName; disabled: boolean; onSave: ReviewScreenProps["onCorrectField"]; onClose: () => void;
}) {
  const current = run.extracted_fields[source]?.[field];
  const docLines = lines(run.sources.find(s => s.source_id === source)?.text ?? "");
  const [value, setValue] = useState(String(current?.value ?? ""));
  const [absent, setAbsent] = useState(current?.value == null);
  const [lineId, setLineId] = useState(current?.evidence[0]?.line_id ?? "");
  const id = useId();
  async function save(event: FormEvent) {
    event.preventDefault();
    const line = docLines.find(l => l.id === lineId);
    if (!absent && !line) return;
    // Same payload the logic track's FieldReview sends: the whole chosen line is the evidence.
    const correction: Correction = {
      source_id: source, field, value: absent ? null : field === "quantity" ? Number(value) : value.trim(),
      evidence: !absent && line ? [{ source_id: source, line_id: line.id, char_start: 0, char_end: Array.from(line.body).length, quote: line.body }] : [],
    };
    if ((await onSave(correction)) !== false) onClose();
  }
  return <form className="rg-correction" onSubmit={save} aria-labelledby={id + "t"}>
    <h4 id={id + "t"}>{t(copy.correction.title, { field: fieldLabel[field].toLowerCase(), source: sourceLabel[source].short })}</h4>
    <label className="rg-check"><input type="checkbox" checked={absent} disabled={disabled} onChange={e => setAbsent(e.target.checked)} />{copy.correction.absent}</label>
    {!absent && <div className="rg-correction-fields">
      <label>{copy.correction.valueLabel}
        <input required maxLength={160} type={field === "quantity" ? "number" : "text"} min={field === "quantity" ? 1 : undefined} step={field === "quantity" ? 1 : undefined}
          value={value} disabled={disabled} onChange={e => setValue(e.target.value)} />
      </label>
      <label>{copy.correction.lineLabel}
        <select required value={lineId} disabled={disabled} onChange={e => setLineId(e.target.value)}>
          <option value="">{copy.correction.linePlaceholder}</option>
          {docLines.map(l => <option key={l.id} value={l.id}>{l.id} · {l.body}</option>)}
        </select>
      </label>
    </div>}
    <p className="rg-hint">{copy.correction.consequence}</p>
    <div className="rg-row">
      <button type="submit" className="rg-btn rg-btn--primary rg-btn--sm" disabled={disabled}><Check />{copy.actions.saveCorrection}</button>
      <button type="button" className="rg-btn rg-btn--quiet rg-btn--sm" disabled={disabled} onClick={onClose}><X />{copy.actions.cancel}</button>
    </div>
  </form>;
}

function FieldTable({ run, disabled, defaultOpen, uid, onCorrect }: {
  run: Run; disabled: boolean; defaultOpen: boolean; uid: string; onCorrect: ReviewScreenProps["onCorrectField"];
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [editing, setEditing] = useState<{ source: SourceId; field: FieldName } | null>(null);
  const statusTone = { Supported: "review", Conflict: "danger", Missing: "warn", "Needs review": "warn" } as const;
  const statusText = { Supported: copy.fields.supported, Conflict: copy.fields.conflict, Missing: copy.fields.missing, "Needs review": copy.fields.needs_review } as const;
  const reviewText = { pending: copy.fields.reviewPending, confirmed: copy.fields.reviewConfirmed, corrected: copy.fields.reviewCorrected } as const;
  return <details className="rg-fields" open={open} onToggle={e => setOpen(e.currentTarget.open)}>
    <summary><span>{copy.fields.summary}</span><ChevronDown /></summary>
    <p className="rg-hint">{copy.fields.body}</p>
    <table aria-label={copy.fields.heading}>
      <thead><tr><th scope="col">{copy.fields.columnField}</th>{engineeringSources.map(s => <th scope="col" key={s}>{sourceLabel[s].short}</th>)}</tr></thead>
      <tbody>
        {fieldNames.map(field => <Fragment key={field}>
          <tr>
            <th scope="row">{fieldLabel[field]}</th>
            {engineeringSources.map(source => {
              const entry = run.extracted_fields[source]?.[field];
              const state = run.field_states?.[source]?.[field];
              if (!entry) return <td key={source}>—</td>;
              const StateIcon = state?.status === "Conflict" ? AlertOctagon : state?.status === "Missing" ? CircleDashed : state?.status === "Needs review" ? Eye : state?.semantic_review_status === "confirmed" ? Check : LocateFixed;
              return <td key={source}>
                <div className="rg-cell">
                  <div>
                    <strong className={entry.value == null ? "rg-cell-empty" : "rg-mono"}>{entry.value ?? copy.finding.noValue}</strong>
                    {state && <span className={cx("rg-cell-state", "rg-text-" + statusTone[state.status])}><StateIcon />{statusText[state.status]} · {reviewText[state.semantic_review_status]}</span>}
                  </div>
                  <button type="button" className="rg-iconbtn" disabled={disabled || !run.allowed_actions.correct_fields}
                    aria-label={t(copy.fields.correctAria, { source: sourceLabel[source].short, field: fieldLabel[field].toLowerCase() })}
                    aria-expanded={editing?.source === source && editing.field === field} onClick={() => setEditing({ source, field })}><PencilLine /></button>
                </div>
              </td>;
            })}
          </tr>
          {editing?.field === field && <tr className="rg-fields-edit"><td colSpan={3}>
            <CorrectionForm key={uid + editing.source + field} run={run} source={editing.source} field={field} disabled={disabled} onSave={onCorrect} onClose={() => setEditing(null)} />
          </td></tr>}
        </Fragment>)}
      </tbody>
    </table>
  </details>;
}

export function ReviewScreen(p: ReviewScreenProps) {
  const { run, packet, questions, reviewing, analyzing, busy, error, notice, stale, edited } = p;
  const uid = useId().replace(/[^a-zA-Z0-9]/g, "");
  const rootRef = useRef<HTMLDivElement>(null);
  const statusRef = useRef<HTMLDivElement>(null);
  const findingsRef = useRef<HTMLHeadingElement>(null);
  const narrow = useNarrow(rootRef);
  const [openIds, setOpenIds] = useState<string[]>([]);
  const [activeRef, setActiveRef] = useState("");

  const results = run && run.extracted_fields?.RFQ ? run : null;
  const approval = !stale ? results?.clarification.approval ?? null : null;
  const phase = analyzing ? "analyzing" : results ? "results" : error ? "failed" : "idle";
  const locked = !!busy || stale;
  const docs = results?.sources ?? packet?.sources ?? [];
  const part = results?.extracted_fields.RFQ?.part_id?.value ?? null;
  const allowed = results?.allowed_actions;
  const emptyQuestion = questions.some(q => !q.question.trim());
  const count = (kind: Kind) => results?.findings.filter(f => f.kind === kind).length ?? 0;
  const draftMissing = !!results && !approval && !stale && results.findings.length > 0 && questions.length === 0;

  const readinessKey = stale ? "out_of_date" : analyzing ? "analyzing" : !results ? "not_analyzed" : results.quote_readiness;
  const readinessTone: Tone = readinessKey === "blocked" ? "danger" : readinessKey === "needs_review" || readinessKey === "out_of_date" ? "warn"
    : readinessKey === "no_detected_blockers_pending_human_review" ? "review" : "neutral";
  const ReadinessIcon = readinessKey === "blocked" ? AlertOctagon : readinessTone === "warn" || readinessTone === "review" ? Eye : analyzing ? LoaderCircle : CircleDashed;

  // Move focus to what changed, only after a change the user caused.
  const previous = useRef({ phase, reviewing, approved: !!approval });
  useEffect(() => {
    const before = previous.current;
    previous.current = { phase, reviewing, approved: !!approval };
    if ((before.phase !== phase && (phase === "results" || phase === "failed")) || (!before.approved && approval)) statusRef.current?.focus();
    else if (!before.reviewing && reviewing) findingsRef.current?.focus();
  }, [phase, reviewing, approval]);

  const lineId = (ref: string) => uid + "-line-" + ref.replace(":", "-");
  const findingId = (id: string) => uid + "-finding-" + id;
  const reveal = (el: HTMLElement | null) => { el?.scrollIntoView({ block: "center", behavior: reducedMotion() ? "auto" : "smooth" }); el?.focus({ preventScroll: true }); };
  const showLine = (ref: string) => { setActiveRef(ref); reveal(document.getElementById(lineId(ref))); };
  const showFinding = (id: string) => reveal(document.getElementById(findingId(id)));

  const step = !results ? 1 : approval ? 3 : reviewing ? 3 : 2;
  const summary = !results ? null
    : results.quote_readiness === "blocked" ? { tone: "danger" as Tone, icon: <AlertOctagon />, title: copy.summary.blockedTitle, body: copy.summary.blockedBody }
    : results.quote_readiness === "needs_review" ? { tone: "warn" as Tone, icon: <Eye />, title: copy.summary.needsReviewTitle, body: copy.summary.needsReviewBody }
    : { tone: "review" as Tone, icon: <Eye />, title: copy.summary.clearTitle, body: copy.summary.clearBody };
  const counts = [
    count("conflict") && t(count("conflict") === 1 ? copy.summary.conflicts : copy.summary.conflictsPlural, { n: count("conflict") }),
    count("missing") && t(count("missing") === 1 ? copy.summary.missing : copy.summary.missingPlural, { n: count("missing") }),
    count("needs_review") && t(copy.summary.needsReview, { n: count("needs_review") }),
  ].filter(Boolean).join(" · ");
  const provider = results?.provenance.provider ?? "";
  const recordedLabel = /ibm/i.test(provider) ? copy.provenance.recordedIbm : copy.provenance.recordedOther;
  const approveBlockedReason = !allowed ? "" : stale ? copy.draft.blockedByStale : count("needs_review") ? copy.draft.blockedByNeedsReview
    : emptyQuestion ? copy.question.empty : !allowed.approve_clarification ? copy.draft.blockedGeneric : "";

  const sources = <Sources key="sources" docs={docs} run={stale ? null : results} uid={uid} activeRef={activeRef} lineId={lineId} onGoToFinding={showFinding} />;

  const review = <section key="review" className="rg-pane rg-review" id={uid + "-review"} aria-labelledby={uid + "-review-h"}>
    <h2 className="rg-sr" id={uid + "-review-h"}>{copy.finding.paneLabel}</h2>

    {stale && <div className="rg-panel rg-panel--warn" role="alert">
      <TriangleAlert />
      <div>
        <h3>{copy.draft.stale}</h3>
        {error && <p className="rg-panel-lead">{error}</p>}
        <p>{p.canLoadReplacement ? copy.draft.staleBody : copy.draft.staleNoReplacement}</p>
        {p.canLoadReplacement && p.onLoadReplacement && <button type="button" className="rg-btn rg-btn--plain rg-btn--sm" onClick={p.onLoadReplacement}><RotateCcw />{copy.actions.loadCurrent}</button>}
      </div>
    </div>}

    <div className={cx("rg-status", stale && "is-stale")} ref={statusRef} tabIndex={-1}>
      {phase === "idle" && <div className="rg-hero">
        <p className="rg-eyebrow">{copy.product.descriptor}</p>
        <h3 className="rg-hero-title">{copy.hero.heading}</h3>
        <p>{packet ? copy.hero.body : p.packetsLoading ? copy.topbar.packetsLoading : copy.hero.noPacket}</p>
        <ol className="rg-steps" aria-label={copy.hero.stepsLabel}>
          <li><strong>{copy.actions.analyze}</strong><span>{copy.hero.step1}</span></li>
          <li><strong>{copy.actions.review}</strong><span>{copy.hero.step2}</span></li>
          <li><strong>{copy.actions.approve}</strong><span>{copy.hero.step3}</span></li>
        </ol>
      </div>}

      {phase === "analyzing" && <div className="rg-progress" aria-busy="true">
        <h3><LoaderCircle className="rg-spin" />{copy.loading.heading}</h3>
        <p>{copy.loading.body}</p>
        <p className="rg-eyebrow">{copy.loading.listLabel}</p>
        <ol className="rg-progress-list">
          {[copy.loading.step1, copy.loading.step2, copy.loading.step3, copy.loading.step4, copy.loading.step5].map(text => <li key={text}>{text}</li>)}
        </ol>
      </div>}

      {phase === "failed" && <div className="rg-panel rg-panel--error" role="alert">
        <TriangleAlert />
        <div>
          <h3>{packet ? copy.error.analysisTitle : copy.error.packetsTitle}</h3>
          <p className="rg-panel-lead">{error}</p>
          <p>{packet ? copy.error.analysisBody + " " + copy.error.retryHint : copy.hero.noPacketsBody}</p>
          {!packet && p.onRetryPackets && <button type="button" className="rg-btn rg-btn--plain rg-btn--sm" onClick={p.onRetryPackets}><RotateCcw />{copy.actions.retryPackets}</button>}
          {packet && <details className="rg-manual"><summary>{copy.error.manualTitle}</summary><p>{copy.error.manualBody}</p></details>}
        </div>
      </div>}

      {phase === "results" && approval && results && <div className="rg-panel rg-panel--ok">
        <Check />
        <div>
          <h3>{results.findings.length ? copy.approval.title : copy.approval.titleNoBlockers}</h3>
          <p>{t(copy.approval.detail, { time: time(approval.approved_at), version: results.versions.draft_version })} {results.quote_readiness === "blocked" ? copy.approval.blockedBody : copy.approval.clearBody}</p>
          {results.clarification.status === "awaiting_customer_response" && <p className="rg-await"><Clock /><span><strong>{copy.approval.awaiting}</strong> {copy.approval.awaitingBody}</span></p>}
        </div>
      </div>}

      {phase === "results" && summary && <div className={cx("rg-panel", "rg-panel--" + summary.tone)}>
        {summary.icon}
        <div>
          <h3>{summary.title}</h3>
          <p>{summary.body}</p>
          {(counts || results?.provenance.started_at) && <p className="rg-panel-meta">
            {counts && <strong>{counts}</strong>}
            {results?.provenance.started_at && <time dateTime={results.provenance.started_at}>{t(copy.summary.analyzedAt, { time: time(results.provenance.started_at) })}</time>}
          </p>}
        </div>
      </div>}
    </div>

    {!stale && error && phase === "results" && <div className="rg-panel rg-panel--error" role="alert">
      <TriangleAlert /><div><h3>{copy.error.requestTitle}</h3><p className="rg-panel-lead">{error}</p><p>{copy.error.requestBody}</p></div>
    </div>}
    {draftMissing && <div className="rg-panel rg-panel--warn">
      <TriangleAlert />
      <div>
        <h3>{copy.draft.draftMissing}</h3><p>{copy.draft.draftMissingBody}</p>
        {p.onRefreshDraft && <button type="button" className="rg-btn rg-btn--plain rg-btn--sm" disabled={locked || !allowed?.correct_fields} onClick={p.onRefreshDraft}><RotateCcw />{copy.actions.refreshDraft}</button>}
      </div>
    </div>}
    {notice && !error && <p className="rg-notice"><Check />{notice}</p>}

    {phase === "results" && results && <>
      <h3 className="rg-section-title" ref={findingsRef} tabIndex={-1}>
        {copy.finding.listLabel} <span className="rg-count">{results.findings.length}</span>
      </h3>
      {results.findings.length === 0 && <p className="rg-empty">{copy.question.none}</p>}
      <div className={cx("rg-findings", stale && "is-stale")}>
        {results.findings.map(f => <FindingCard key={f.finding_id} f={f} run={results} docs={docs} domId={findingId(f.finding_id)}
          question={questions.find(q => q.finding_id === f.finding_id)} open={reviewing || openIds.includes(f.finding_id)} canToggle={!reviewing}
          editable={!locked && !approval && !!allowed?.edit_draft} onEdit={p.onEditDraft} onShow={showLine}
          onToggle={() => setOpenIds(ids => ids.includes(f.finding_id) ? ids.filter(id => id !== f.finding_id) : [...ids, f.finding_id])} />)}
      </div>
      {reviewing && <FieldTable key={results.run_id} run={results} disabled={locked} defaultOpen={results.findings.length === 0} uid={uid} onCorrect={p.onCorrectField} />}
    </>}

    {p.previousDraft && p.previousDraft.length > 0 && <details className="rg-provenance rg-previous">
      <summary>{copy.draft.previousHeading}<ChevronDown /></summary>
      {p.previousDraft.map(q => <p key={q.finding_id}>{q.question}</p>)}
    </details>}

    <footer className="rg-actionbar">
      <div className="rg-actionbar-text">
        <p className="rg-stepper">
          <span className="rg-eyebrow">{approval ? copy.steps.complete : t(copy.steps.counter, { n: step })}</span>
          <span className="rg-stepdots" aria-hidden="true">{[1, 2, 3].map(n => <i key={n} className={cx(n < step || approval ? "is-done" : n === step ? "is-current" : "")} />)}</span>
        </p>
        {results && reviewing && !approval && <>
          <p>{results.findings.length ? copy.draft.attestation : copy.draft.attestationNoQuestions}</p>
          {edited && <p className="rg-text-warn rg-strong"><PencilLine />{copy.draft.edited}</p>}
          {approveBlockedReason && <p className="rg-text-warn rg-strong" id={uid + "-why"}><TriangleAlert />{approveBlockedReason}</p>}
        </>}
        {busy && !analyzing && <p className="rg-busy"><LoaderCircle className="rg-spin" />{t(copy.loading.working, { label: busy })}</p>}
      </div>
      <div className="rg-actionbar-buttons">
        {results && !approval && <button type="button" className="rg-btn rg-btn--quiet" disabled={!!busy || !packet} onClick={p.onAnalyzePacket}><RotateCcw />{copy.actions.reanalyze}</button>}
        {!results && <button type="button" key="analyze" className="rg-btn rg-btn--primary" disabled={!!busy || !packet} onClick={p.onAnalyzePacket}>
          {analyzing ? <LoaderCircle className="rg-spin" /> : <ScanLine />}{analyzing ? copy.actions.analyzing : phase === "failed" ? copy.actions.retry : copy.actions.analyze}{!analyzing && <ArrowRight />}
        </button>}
        {results && !reviewing && <button type="button" key="review" className="rg-btn rg-btn--primary" disabled={locked || !allowed?.review_evidence} onClick={p.onReviewEvidence}>
          <Eye />{copy.actions.review}<ArrowRight />
        </button>}
        {results && reviewing && !approval && <span className="rg-actionbar-primary">
          <button type="button" key="approve" className="rg-btn rg-btn--primary" disabled={locked || !allowed?.approve_clarification || emptyQuestion}
            aria-describedby={approveBlockedReason ? uid + "-why" : undefined} onClick={p.onApproveClarification}><Download />{copy.actions.approve}</button>
          <small>{copy.draft.approveCaption}</small>
        </span>}
        {results && approval && <>
          {p.onReopenDraft && <button type="button" className="rg-btn rg-btn--quiet" disabled={locked || !allowed?.edit_draft} onClick={p.onReopenDraft}><PencilLine />{copy.actions.reopen}</button>}
          <button type="button" key="download" className="rg-btn rg-btn--primary" disabled={locked || !allowed?.download_export} onClick={p.onDownloadExport}><Download />{copy.actions.download}</button>
        </>}
      </div>
    </footer>

    {results && <details className="rg-provenance">
      <summary>{copy.provenance.heading}<span className="rg-chip">{p.preview ? copy.provenance.preview : p.recordedAt ? recordedLabel : copy.provenance.live}</span><ChevronDown /></summary>
      <dl>
        <dt>{copy.provenance.mode}</dt><dd>{p.preview ? copy.provenance.previewBody : p.recordedAt ? t(copy.provenance.recordedBody, { time: new Date(p.recordedAt).toLocaleString() }) : copy.provenance.live}</dd>
        <dt>{copy.provenance.provider}</dt><dd>{provider || "—"}</dd>
        <dt>{copy.provenance.model}</dt><dd className="rg-mono">{results.provenance.model_id || "—"}</dd>
        <dt>{copy.provenance.started}</dt><dd>{results.provenance.started_at ? new Date(results.provenance.started_at).toLocaleString() : "—"}</dd>
        <dt>{copy.provenance.run}</dt><dd className="rg-mono">{results.run_id}</dd>
        <dt>{copy.provenance.versions}</dt><dd>{t(copy.provenance.versionsValue, { run: results.versions.run_version, draft: results.versions.draft_version })}</dd>
        <dt>{copy.provenance.rules}</dt><dd className="rg-mono">{results.versions.rule_version}</dd>
        <dt>{copy.provenance.hash}</dt><dd className="rg-mono">{results.versions.source_hash.slice(0, 16)}</dd>
      </dl>
      <p className="rg-hint">{copy.provenance.storage}</p>
    </details>}
  </section>;

  return <div className="rg" ref={rootRef}>
    <div className={cx("rg-screen", narrow && "is-narrow")}>
      <a className="rg-skip" href={"#" + uid + "-review"}>{copy.topbar.skip}</a>
      <header className="rg-topbar">
        <h1 className="rg-brand"><Logo tone="reversed" /><span className="rg-sr">: {copy.topbar.pageTitle}</span></h1>
        <div className="rg-packet">
          <label htmlFor={uid + "-packet"}>{copy.topbar.packetLabel}</label>
          <span className="rg-select">
            <select id={uid + "-packet"} value={p.packetId} disabled={!!busy || !p.packets.length} onChange={e => p.onSelectPacket(e.target.value)}>
              {!p.packets.length && <option value="">{p.packetsLoading ? copy.topbar.packetsLoading : copy.topbar.packetsUnavailable}</option>}
              {p.packets.map(option => <option key={option.packet_id} value={option.packet_id}>{packetLabel[option.packet_id] ?? option.packet_id}</option>)}
            </select>
            <ChevronDown />
          </span>
        </div>
        <span className="rg-synthetic" title={copy.topbar.syntheticHint}><FlaskConical />{copy.topbar.synthetic}</span>
        <div className="rg-part">
          <span className="rg-eyebrow">{copy.topbar.partLabel}</span>
          <span className="rg-mono">{part ?? "—"}{part == null && <span className="rg-sr">{copy.topbar.partUnknown}</span>}</span>
        </div>
        <div className="rg-readiness">
          <span className="rg-eyebrow">{copy.topbar.readinessLabel}</span>
          <strong className={cx("rg-pill", "rg-tone-" + readinessTone)}><ReadinessIcon className={analyzing ? "rg-spin" : undefined} />{copy.readiness[readinessKey]}</strong>
        </div>
      </header>

      {(p.recordedAt || p.preview) && <p className={cx("rg-banner", p.recordedAt ? "rg-banner--recorded" : "rg-banner--preview")}>
        {p.recordedAt ? <History /> : <FlaskConical />}
        <strong>{p.recordedAt ? recordedLabel : copy.provenance.preview}</strong>
        <span>{p.recordedAt ? t(copy.provenance.recordedBody, { time: new Date(p.recordedAt).toLocaleString() }) : copy.provenance.previewBody}</span>
      </p>}

      <div className="rg-sr" role="status" aria-live="polite">
        {analyzing ? copy.loading.announce : busy ? t(copy.loading.working, { label: busy }) : notice || (phase === "results" && summary ? summary.title + " " + counts : "")}
      </div>

      <main className="rg-main">{narrow ? [review, sources] : [sources, review]}</main>
    </div>
  </div>;
}

import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { AlertCircle, ArrowRight, Box, CheckCircle2, ChevronDown, Circle, FlaskConical, FolderClosed, LoaderCircle, LockKeyhole, RotateCcw, ScanLine, ShieldAlert } from "lucide-react";
import { api, ApiError } from "./api";
import { Analysis } from "./Analysis";
import { Documents } from "./Documents";
import { packets } from "./labels";
import { ReviewScreen } from "./design";
import type { Correction, Packet, Question, Run } from "./types";

import "./styles.css";

function Header() {
  return <header className="app-header"><div className="header-inner">
    <div className="brand"><img src="/mark.svg" width="34" height="34" alt=""/><span>Revision<span className="brand-light">Gate</span></span></div>
    <span className="workspace-name">Estimator workspace</span>
    <span className="synthetic-tag"><FlaskConical/>Synthetic demo</span>
  </div></header>;
}

function App() {
  const [available, setAvailable] = useState<Packet[]>([]);
  const [packetId, setPacketId] = useState("");
  const [loadingPackets, setLoadingPackets] = useState(true);
  const [attempt, retryFixtures] = useState(0);
  const [run, setRun] = useState<Run | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [stale, setStale] = useState(false);
  const [replacement, setReplacement] = useState<Run | null>(null);
  const [reviewing, setReviewing] = useState(false);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [busy, setBusy] = useState("");
  const [previousDraft, setPreviousDraft] = useState<Question[]>([]);
  const operating = useRef(false);
  const reviewIntro = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let active = true;
    setLoadingPackets(true); setError("");
    api.fixtures().then(list => {
      if (active) { setAvailable(list); setPacketId(list[0]?.packet_id ?? ""); }
    }).catch(e => { if (active) setError(e.message); }).finally(() => { if (active) setLoadingPackets(false); });
    return () => { active = false; };
  }, [attempt]);

  const packet = available.find(p => p.packet_id === packetId);
  const edited = questions.some(q => run?.questions.find(original => original.finding_id === q.finding_id)?.question !== q.question);
  function load(result: Run, showReview: boolean) {
    setRun(result); setQuestions(result.questions); setReviewing(showReview);
    setStale(false); setReplacement(null); setPreviousDraft([]);
  }
  function select(id: string) {
    setPacketId(id); setRun(null); setReviewing(false); setQuestions([]); setReplacement(null);
    setNotice(""); setError(""); setStale(false); setPreviousDraft([]);
  }
  function handleError(e: unknown, operation: string) {
    setError(e instanceof Error ? e.message : "The request failed. Retry the operation.");
    if (e instanceof ApiError && e.status === 409) {
      setStale(true); setReplacement(e.currentRun ?? null); return;
    }
    if (operation === "analyze" && run) {
      setStale(true);
      if (e instanceof ApiError && e.currentRun?.extracted_fields?.RFQ) setReplacement(e.currentRun);
    } else if (e instanceof ApiError && e.currentRun) {
      load(e.currentRun, operation === "correct");
      if (operation === "correct" && questions.length && e.currentRun.analysis.status === "failed") setPreviousDraft(questions);
    } else if (e instanceof ApiError && e.status === 0 && ["correct", "approve", "reopen"].includes(operation)) {
      setStale(true);
    }
  }
  async function perform(label: string, operation: string, action: () => Promise<void>) {
    if (operating.current) return false;
    operating.current = true;
    setBusy(label); setError(""); setNotice("");
    try {
      await action();
      return true;
    } catch (e) {
      handleError(e, operation);
      return false;
    } finally { operating.current = false; setBusy(""); }
  }
  function analyze() {
    if (!packet) return;
    void perform("Analyzing packet", "analyze", async () => {
      load(await api.analyze(packet), false);
      setNotice("Analysis complete. Open Review evidence to inspect all findings.");
    });
  }
  function openReview() {
    setReviewing(true); setNotice("");
    requestAnimationFrame(() => reviewIntro.current?.focus());
  }
  function correct(correction?: Correction) {
    if (!run) return Promise.resolve(false);
    return perform(correction ? "Saving correction and regenerating draft" : "Regenerating draft", "correct", async () => {
      load(await api.correct(run, correction ? [correction] : []), true);
      setNotice("A new draft is ready. Review the current questions and sources before approval.");
    });
  }
  function reopen() {
    if (!run) return;
    void perform("Opening draft for editing", "reopen", async () => {
      load(await api.reopen(run), true);
      setNotice("The previous approval has been invalidated. Review and approve the edited draft to download it.");
    });
  }
  function approve() {
    if (!run || !reviewing) return;
    void perform("Approving clarification", "approve", async () => {
      const approved = await api.approve(run, questions);
      load(approved, true);
      // Keep approval visible even if the independent download request fails.
      setBusy("Downloading approved packet");
      try {
        await api.download(approved); setNotice("Clarification approved. Packet download started.");
      } catch(e) { handleError(e, "download"); }
    });
  }
  function download() {
    if (run) void perform("Downloading approved packet", "download", async () => {
      await api.download(run); setNotice("Packet download started.");
    });
  }
  const disabled = !!busy || stale;
  const part = run?.extracted_fields?.RFQ?.part_id?.value;
  const readiness = stale ? "Needs review" : !run || run.analysis.status === "running" ? "Not assessed" : run.quote_readiness === "blocked" ? "Blocked" : "Needs review";
  const ReadinessIcon = readiness === "Blocked" ? LockKeyhole : readiness === "Not assessed" ? Circle : ShieldAlert;
  // Presentation lives in src/design. This container still owns all state and API calls.
  return <ReviewScreen
    packets={available} packetId={packetId} packetsLoading={loadingPackets} packet={packet} run={run}
    questions={questions} previousDraft={previousDraft} reviewing={reviewing} analyzing={busy === "Analyzing packet"} busy={busy}
    error={error} notice={notice} stale={stale} edited={edited} canLoadReplacement={!!replacement}
    onSelectPacket={select} onAnalyzePacket={analyze} onReviewEvidence={openReview} onCorrectField={correct}
    onEditDraft={(id, text) => setQuestions(qs => qs.map(q => q.finding_id === id ? {...q, question: text} : q))}
    onApproveClarification={approve} onDownloadExport={download} onReopenDraft={reopen} onRefreshDraft={() => void correct()}
    onLoadReplacement={() => { if (replacement) { load(replacement, false); setError(""); setNotice("Current extraction loaded. Review its evidence before continuing."); } }}
    onRetryPackets={() => retryFixtures(n => n + 1)}/>;
}

createRoot(document.getElementById("root")!).render(<App/>);

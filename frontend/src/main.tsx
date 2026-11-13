import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { api, ApiError } from "./api";
import { ReviewScreen } from "./design";
import { readReviewSession, saveReviewSession, type SavedReview } from "./reviewSession";
import type { Correction, Packet, Question, Run } from "./types";
import "./styles.css";

function snapshot(packetId: string, run: Run | null, reviewing: boolean, questions: Question[]): SavedReview {
  const edits: Record<string, string> = {};
  if (run && !run.clarification.approval) {
    for (const question of questions) {
      const original = run.questions.find(q => q.finding_id === question.finding_id);
      if (original && question.question !== original.question) edits[question.finding_id] = question.question;
    }
  }
  return {
    packetId, reviewing, edits, resume: !!run,
    runId: run?.run_id ?? null,
    runVersion: run?.versions.run_version ?? null,
    draftVersion: run?.versions.draft_version ?? null,
  };
}

function sameVersion(saved: SavedReview, run: Run | null) {
  return run != null && saved.packetId === run.packet.packet_id && saved.runId === run.run_id
    && saved.runVersion === run.versions.run_version && saved.draftVersion === run.versions.draft_version;
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
  const [previousDraft, setPreviousDraft] = useState<string[]>([]);
  const operating = useRef(false);

  function load(result: Run, showReview: boolean, wording = result.questions) {
    saveReviewSession(snapshot(result.packet.packet_id, result, showReview, wording));
    setPacketId(result.packet.packet_id); setRun(result); setQuestions(wording); setReviewing(showReview);
    setStale(false); setReplacement(null); setPreviousDraft([]);
  }

  useEffect(() => {
    let active = true;
    async function restore() {
      setLoadingPackets(true); setError(""); setBusy("Restoring review");
      try {
        const list = await api.fixtures();
        if (!active) return;
        const saved = readReviewSession();
        const selected = list.find(p => p.packet_id === saved?.packetId) ?? list[0];
        if (saved?.resume && selected?.packet_id === saved.packetId) {
          let current = await api.currentRun();
          // A reload can race the original analysis request reaching the backend.
          // Read status without resubmitting a model request or an approval.
          for (let poll = 0; active && poll < 60; poll++) {
            const waitForStart = saved.pending === "analyze" && (!current || current.run_id === saved.runId);
            const waitForChange = sameVersion(saved, current) && (saved.pending === "correct" ||
              (saved.pending === "reopen" && !!current?.clarification.approval) ||
              (saved.pending === "approve" && !current?.clarification.approval));
            const running = current?.analysis.status === "running";
            if (!running && !(poll < 2 && (waitForStart || waitForChange))) break;
            setBusy(running ? "Waiting for the current analysis" : "Restoring review");
            await new Promise(resolve => window.setTimeout(resolve, 1000));
            if (!active) return;
            current = await api.currentRun();
          }
          if (!active) return;
          if (current?.analysis.status === "running") throw new Error("The current analysis is still running. Retry to check its progress.");
          if (current && current.packet.packet_id === saved.packetId) {
            // Only wording comes from tab storage. References, approval, and
            // everything that permits an action come from the latest server run.
            const useEdits = sameVersion(saved, current) && current.allowed_actions.edit_draft && !current.clarification.approval;
            const wording = useEdits ? current.questions.map(q => ({
              ...q, question: saved.edits[q.finding_id] ?? q.question,
            })) : current.questions;
            load(current, !!current.clarification.approval || (saved.reviewing && saved.runId === current.run_id), wording);
            if (current.analysis.status === "failed") {
              setError("The last request failed. Inspect the source documents and retry.");
            } else {
              setNotice("Review restored.");
            }
          } else {
            setPreviousDraft(Object.values(saved.edits));
            setNotice(current ? "The selected packet has no current review. Analyze it to begin." :
              "The server review is no longer available. Analyze the selected packet to start a new review.");
          }
        }
        if (active) { setAvailable(list); setPacketId(selected?.packet_id ?? ""); }
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : "The review could not be restored. Retry to reconnect.");
      } finally {
        if (active) { setLoadingPackets(false); setBusy(""); }
      }
    }
    void restore();
    return () => { active = false; };
  }, [attempt]);

  const packet = available.find(p => p.packet_id === packetId);
  const edited = questions.some(q => run?.questions.find(original => original.finding_id === q.finding_id)?.question !== q.question);

  function select(id: string) {
    saveReviewSession(snapshot(id, null, false, []));
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
      if (operation === "correct" && questions.length && e.currentRun.analysis.status === "failed") setPreviousDraft(questions.map(q => q.question));
    } else if (e instanceof ApiError && e.status === 0 && ["correct", "approve", "reopen"].includes(operation)) {
      setStale(true);
    }
  }

  async function perform(label: string, operation: "analyze" | "correct" | "approve" | "reopen" | "download", action: () => Promise<void>) {
    if (operating.current) return false;
    operating.current = true;
    if (operation !== "download") {
      saveReviewSession({ ...snapshot(packetId, run, reviewing, questions), resume: true, pending: operation });
    }
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
    saveReviewSession(snapshot(packetId, run, true, questions));
    setReviewing(true); setNotice("");
  }
  function editQuestion(id: string, text: string) {
    if (!run?.allowed_actions.edit_draft || run.clarification.approval) return;
    const next = questions.map(q => q.finding_id === id ? { ...q, question: text } : q);
    // Persist during the input event, including an intentionally cleared field.
    saveReviewSession(snapshot(packetId, run, reviewing, next));
    setQuestions(next);
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

  return <ReviewScreen
    packets={available} packetId={packetId} packetsLoading={loadingPackets} packet={packet} run={run}
    questions={questions} previousDraft={previousDraft} reviewing={reviewing} analyzing={busy === "Analyzing packet"} busy={busy}
    error={error} notice={notice} stale={stale} edited={edited} canLoadReplacement={!!replacement}
    onSelectPacket={select} onAnalyzePacket={analyze} onReviewEvidence={openReview} onCorrectField={correct}
    onEditDraft={editQuestion}
    onApproveClarification={approve} onDownloadExport={download} onReopenDraft={reopen} onRefreshDraft={() => void correct()}
    onLoadReplacement={() => { if (replacement) { load(replacement, false); setError(""); setNotice("Current extraction loaded. Review its evidence before continuing."); } }}
    onRetryPackets={() => retryFixtures(n => n + 1)}/>;
}

createRoot(document.getElementById("root")!).render(<App/>);

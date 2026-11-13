// Design state gallery. Development preview only: scripted synthetic states,
// no backend, no model call. Open /gallery.html on the Vite dev server.
import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { ReviewScreen } from "../ReviewScreen";
import { Logo, Mark } from "../Logo";
import type { Question } from "../../types";
import { packets, states } from "./states";
import "./gallery.css";

const widths = { full: "100%", laptop: "1180px", mobile: "390px" } as const;
type Width = keyof typeof widths;

function read() {
  const [id, width] = window.location.hash.slice(1).split("/");
  return { id: states.some(s => s.id === id) ? id : states[0].id, width: (width in widths ? width : "full") as Width };
}

function Gallery() {
  const [{ id, width }, setView] = useState(read);
  const state = states.find(s => s.id === id)!;
  const [questions, setQuestions] = useState<Question[]>(state.props.questions);
  const [log, setLog] = useState<string[]>([]);
  useEffect(() => { const sync = () => setView(read()); window.addEventListener("hashchange", sync); return () => window.removeEventListener("hashchange", sync); }, []);
  useEffect(() => { setQuestions(state.props.questions); setLog([]); }, [state]);
  const go = (next: Partial<{ id: string; width: Width }>) => { window.location.hash = (next.id ?? id) + "/" + (next.width ?? width); };
  const call = (name: string, detail = "") => setLog(entries => [name + (detail ? "(" + detail + ")" : "()"), ...entries].slice(0, 6));

  return <div className="gal">
    <aside className="gal-side">
      <div className="gal-brand"><Logo /><span>State gallery</span></div>
      <p className="gal-warning"><strong>Synthetic preview.</strong> Scripted design states. No backend and no model call. Not evidence of a working integration.</p>
      <nav aria-label="States">
        <ol>{states.map((s, index) => <li key={s.id}>
          <button type="button" aria-current={s.id === id ? "true" : undefined} onClick={() => go({ id: s.id })}><span>{String(index + 1).padStart(2, "0")}</span>{s.title}</button>
        </li>)}</ol>
      </nav>
      <div className="gal-marks" aria-label="Logo marks">
        <span><Mark size={40} /></span><span className="gal-dark"><Mark size={40} tone="reversed" /></span><span><Mark size={16} /></span>
      </div>
    </aside>
    <div className="gal-stage">
      <header className="gal-head">
        <div><h1>{state.title}</h1><p>{state.check}</p></div>
        <div className="gal-widths" role="group" aria-label="Preview width">
          {(Object.keys(widths) as Width[]).map(w => <button type="button" key={w} aria-pressed={w === width} onClick={() => go({ width: w })}>{w}</button>)}
        </div>
      </header>
      <div className="gal-frame" style={{ width: widths[width] }}>
        <ReviewScreen key={state.id} {...state.props} packets={packets} questions={questions}
          onSelectPacket={packetId => call("onSelectPacket", packetId)}
          onAnalyzePacket={() => call("onAnalyzePacket")}
          onReviewEvidence={() => call("onReviewEvidence")}
          onCorrectField={correction => { call("onCorrectField", JSON.stringify({ source_id: correction.source_id, field: correction.field, value: correction.value })); return Promise.resolve(false); }}
          onEditDraft={(findingId, text) => { setQuestions(qs => qs.map(q => q.finding_id === findingId ? { ...q, question: text } : q)); call("onEditDraft", findingId); }}
          onApproveClarification={() => call("onApproveClarification")}
          onDownloadExport={() => call("onDownloadExport")}
          onReopenDraft={() => call("onReopenDraft")}
          onRefreshDraft={() => call("onRefreshDraft")}
          onLoadReplacement={() => call("onLoadReplacement")}
          onRetryPackets={() => call("onRetryPackets")} />
      </div>
      <p className="gal-log" aria-live="polite"><strong>Callbacks fired:</strong> {log.length ? log.join("  ·  ") : "none yet. Nothing here changes state; the container owns that."}</p>
    </div>
  </div>;
}

createRoot(document.getElementById("root")!).render(<Gallery />);

import { useState, type FormEvent } from "react";
import { Check, ChevronDown, PencilLine, X } from "lucide-react";
import { engineeringSources, fieldNames, type Correction, type FieldName, type Run, type SourceId } from "./types";
import { fields, lines, sources } from "./labels";

function stateClass(status: string | undefined) {
  return status === "Conflict" ? "conflict" : status === "Supported" ? "supported" : "attention";
}

type Editing = { source: SourceId; field: FieldName };
export function FieldReview({ run, disabled, onCorrect }: {
  run: Run; disabled: boolean; onCorrect: (correction: Correction) => Promise<boolean>;
}) {
  const [editing, setEditing] = useState<Editing | null>(null);
  const [value, setValue] = useState("");
  const [absent, setAbsent] = useState(false);
  const [lineId, setLineId] = useState("");
  function edit(source: SourceId, field: FieldName) {
    const current = run.extracted_fields[source]?.[field];
    setEditing({ source, field }); setValue(String(current?.value ?? "")); setAbsent(current?.value == null);
    setLineId(current?.evidence[0]?.line_id ?? "");
  }
  async function save(event: FormEvent) {
    event.preventDefault();
    if (!editing) return;
    const source = run.sources.find(s => s.source_id === editing.source)!;
    const line = lines(source.text).find(l => l.id === lineId);
    if (!absent && !line) return;
    const correction = {
      source_id: editing.source, field: editing.field,
      value: absent ? null : editing.field === "quantity" ? Number(value) : value.trim(),
      evidence: !absent && line ? [{ source_id: editing.source, line_id: line.id, char_start: 0,
        char_end: Array.from(line.body).length, quote: line.body }] : [],
    };
    if (await onCorrect(correction)) setEditing(null);
  }
  return <details className="field-review" open={true}>
    <summary><span>Inspect or correct extracted fields</span><ChevronDown/></summary>
    <p>Check each value against the complete source. Correct an extraction error here. Saving regenerates the draft and invalidates its approval.</p>
    {engineeringSources.map(source => <div className="field-group" key={source}>
      <h4>{sources[source].title}</h4>
      {fieldNames.map(field => {
        const entry = run.extracted_fields[source]?.[field];
        const state = run.field_states?.[source]?.[field];
        if (!entry) return null;
        return <div className="field-row" key={field}>
          <span>{fields[field]}</span><div><strong>{entry.value ?? "No value extracted"}</strong>
            {state && <small className={stateClass(state.status)}>{state.status} · {state.semantic_review_status === "pending" ? "Review pending" : state.semantic_review_status}</small>}
          </div>
          <button type="button" className="icon-button" disabled={disabled || !run.allowed_actions.correct_fields} aria-label={"Correct " + sources[source].short + " " + fields[field]} onClick={() => edit(source, field)}><PencilLine/></button>
          {editing?.source === source && editing.field === field && <form className="correction-form" onSubmit={save}>
            <h4>Correct {fields[field].toLowerCase()} in {sources[source].short}</h4>
            <label className="check"><input type="checkbox" checked={absent} onChange={e => setAbsent(e.target.checked)} disabled={disabled}/>I inspected this source and found no explicit value.</label>
            {!absent && <>
              <label>Explicit source value<input required maxLength={160} type={field === "quantity" ? "number" : "text"} min={field === "quantity" ? 1 : undefined} step={field === "quantity" ? 1 : undefined} value={value} onChange={e => setValue(e.target.value)} disabled={disabled}/></label>
              <label>Supporting source line<select required value={lineId} onChange={e => setLineId(e.target.value)} disabled={disabled}>
                <option value="">Select a line</option>
                {lines(run.sources.find(doc => doc.source_id === source)!.text).map(l => <option key={l.id} value={l.id}>{l.id} · {l.body}</option>)}
              </select></label>
            </>}
            <div className="button-row"><button className="btn primary small" type="submit" disabled={disabled}><Check/>Save correction</button>
              <button className="btn quiet small" type="button" disabled={disabled} onClick={() => setEditing(null)}><X/>Cancel</button></div>
          </form>}
        </div>;
      })}
    </div>)}
  </details>;
}

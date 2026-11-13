import { useState } from "react";
import { BookOpen, FileCheck2, FileStack, FileText, Layers2 } from "lucide-react";
import type { Evidence, Run, Source, SourceId } from "./types";
import { lines, sources } from "./labels";

const sourceIcons = { RFQ: FileText, DRAWING: Layers2, CHECKLIST: FileCheck2 };

function Highlight({ body, evidence }: { body: string; evidence: Evidence[] }) {
  const characters = Array.from(body);
  const spans = [...evidence].sort((a,b) => a.char_start - b.char_start);
  let cursor = 0;
  const segments = [];
  for (const span of spans) {
    if (span.char_end <= cursor) continue;
    segments.push(characters.slice(cursor, span.char_start).join(""));
    segments.push(<mark key={span.char_start + "-" + span.char_end}>{characters.slice(Math.max(cursor, span.char_start), span.char_end).join("")}</mark>);
    cursor = span.char_end;
  }
  segments.push(characters.slice(cursor).join(""));
  return <>{segments}</>;
}

export function Documents({ docs, run, reviewed }: { docs: Source[]; run: Run | null; reviewed: boolean }) {
  const [selected, select] = useState<SourceId>("RFQ");
  const visible = reviewed ? docs : docs.filter(doc => doc.source_id === selected);
  const references = new Set(run?.findings.flatMap(f => [...f.evidence_refs, ...f.policy_refs]));
  return <section className="panel documents" aria-labelledby="source-heading">
    <header className="panel-heading"><div className="heading-pair"><FileStack/><h2 id="source-heading">Source documents</h2></div><span className="counter">{docs.length} files</span></header>
    <div className="source-switcher" aria-label="Source documents">
      {docs.map(doc => {
        const Icon = sourceIcons[doc.source_id];
        return reviewed ? <a key={doc.source_id} href={"#document-" + doc.source_id}><Icon/>{sources[doc.source_id].short}</a>
          : <button type="button" key={doc.source_id} aria-pressed={selected === doc.source_id} onClick={() => select(doc.source_id)}><Icon/>{sources[doc.source_id].short}</button>;
      })}
    </div>
    {visible.map(doc => {
      const textLines = lines(doc.text);
      const fieldValues = run?.extracted_fields?.[doc.source_id];
      const evidence = fieldValues ? Object.values(fieldValues).flatMap(field => field.evidence) : [];
      return <article key={doc.source_id} className="document-sheet" id={"document-" + doc.source_id} tabIndex={-1}>
        <div className="sheet-heading"><div><div className="eyelabel">{sources[doc.source_id].type}</div><h3>{sources[doc.source_id].title}</h3></div><span className="file-type">TXT</span></div>
        <div className="source-lines" aria-label={sources[doc.source_id].title + " lines"}>
          {textLines.map(line => {
            const ref = doc.source_id + ":" + line.id;
            return <div id={doc.source_id + "-" + line.id} tabIndex={-1} key={line.id} className={"source-line" + (references.has(ref) ? " cited" : "")}><span className="line-id">{line.id}</span><span className="line-body"><Highlight body={line.body} evidence={evidence.filter(span => span.line_id === line.id)}/></span></div>;
          })}
        </div>
        <div className="sheet-foot"><BookOpen/>{textLines.length} source lines<span className="file-name">{doc.source_id}</span></div>
      </article>;
    })}
  </section>;
}

export function Passage({ reference, docs }: { reference: string; docs: Source[] }) {
  const [source, id] = reference.split(":");
  const doc = docs.find(d => d.source_id === source);
  const body = doc && lines(doc.text).find(l => l.id === id)?.body;
  return <blockquote className={"passage" + (source === "CHECKLIST" ? " policy" : "")}><a href={"#" + source + "-" + id}>{source === "CHECKLIST" ? "Policy" : source} · {id}</a><p>{body}</p></blockquote>;
}

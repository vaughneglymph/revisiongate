import type { FieldName, SourceId } from "./types";
export const fields: Record<FieldName, string> = {
  part_id: "Part ID", quantity: "Quantity", revision: "Revision", material: "Material", finish: "Finish",
};
export const packets: Record<string, string> = {
  "01_conflicted": "01 · Conflicted packet", "02_material_changed": "02 · Material changed",
  "03_complete": "03 · Complete packet", "04_injection": "04 · Embedded instruction",
};
export const sources: Record<SourceId, { short: string; title: string; type: string }> = {
  RFQ: { short: "RFQ", title: "Request for quotation", type: "Customer request" },
  DRAWING: { short: "Drawing", title: "Drawing notes", type: "Engineering document" },
  CHECKLIST: { short: "Checklist", title: "Shop intake checklist", type: "Review policy" },
};
export function lines(text: string) {
  return text.split("\n").map(line => {
    const delimiter = line.indexOf(" | ");
    return { id: line.slice(0, delimiter), body: line.slice(delimiter + 3) };
  });
}

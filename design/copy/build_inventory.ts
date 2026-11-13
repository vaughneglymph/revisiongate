// Regenerate COPY_INVENTORY.md from the strings the app actually ships.
// Run from the repo root: bun design/copy/build_inventory.ts
import { copy, fieldLabel, packetLabel, sourceLabel } from "../../frontend/src/design/copy";
import { writeFileSync } from "node:fs";
const titles: Record<string, string> = {
  product: "Product", topbar: "Top bar (TopBar)", readiness: "Quote readiness label (persistent)", hero: "Idle state (hero)",
  actions: "Action labels", steps: "Step indicator (ActionBar)", loading: "Analyzing state", summary: "Result summary panel",
  finding: "Findings (FindingCard)", evidence: "Evidence and source lines (Passage, Sources)", question: "Clarification questions",
  fields: "Extracted requirements (FieldTable)", correction: "Manual correction (CorrectionForm)", draft: "Draft, stale draft, approval guard",
  approval: "Approval, awaiting response, export", error: "Errors, timeout, retry, manual review", provenance: "Run details and recorded-run label",
  captions: "Six demo-video captions",
};
let out = "# RevisionGate copy inventory\n\nGenerated from `frontend/src/design/copy.ts`. Do not edit by hand: change the string in `copy.ts`, then run `bun design/copy/build_inventory.ts`.\n\nKeys are `copy.<component>.<string>`. `{placeholders}` are filled at render time from run data.\n";
for (const [group, strings] of Object.entries(copy)) {
  out += `\n## ${titles[group] ?? group}\n\n| Key | Copy |\n|---|---|\n`;
  for (const [key, value] of Object.entries(strings)) out += `| \`${group}.${key}\` | ${String(value).replace(/\|/g, "\\|")} |\n`;
}
out += "\n## Labels\n\n| Key | Copy |\n|---|---|\n";
for (const [k, v] of Object.entries(fieldLabel)) out += `| \`fieldLabel.${k}\` | ${v} |\n`;
for (const [k, v] of Object.entries(sourceLabel)) out += `| \`sourceLabel.${k}\` | ${v.short} · ${v.title} · ${v.type} |\n`;
for (const [k, v] of Object.entries(packetLabel)) out += `| \`packetLabel.${k}\` | ${v} |\n`;
writeFileSync(new URL("./COPY_INVENTORY.md", import.meta.url), out);
console.log("wrote COPY_INVENTORY.md", out.split("\n").length, "lines");

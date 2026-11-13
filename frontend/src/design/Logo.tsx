// RevisionGate logo: compact RG monogram on a rounded tile.
// R takes the neutral color and G the teal, the same split as the wordmark
// (Revision + Gate). No check mark, seal, or shield: the mark does not suggest
// certification or approval.
// Letter outlines come from design/brand/build_logos.py (the editable master).
import { logoPaths } from "./logoPaths";

type Tone = "color" | "reversed" | "mono";

const tones = {
  color: { tile: "#132238", r: "#FFFFFF", g: "#4FD1C5", word: "#132238", accent: "#007F7A" },
  reversed: { tile: "#FFFFFF", r: "#132238", g: "#007F7A", word: "#FFFFFF", accent: "#4FD1C5" },
  mono: { tile: "currentColor", r: "", g: "", word: "currentColor", accent: "currentColor" },
} as const;

export function Mark({ size = 28, tone = "color", title }: { size?: number; tone?: Tone; title?: string }) {
  const c = tones[tone];
  return (
    <svg className="rg-mark" viewBox="0 0 48 48" width={size} height={size} style={{ width: size, height: size }}
      role={title ? "img" : undefined} aria-label={title} aria-hidden={title ? undefined : true} focusable="false">
      {tone === "mono"
        ? <path fill="currentColor" fillRule="evenodd" d={logoPaths.tile + logoPaths.r + logoPaths.g} />
        : <><path fill={c.tile} d={logoPaths.tile} /><path fill={c.r} d={logoPaths.r} /><path fill={c.g} d={logoPaths.g} /></>}
    </svg>
  );
}

export function Logo({ tone = "color", size = 28 }: { tone?: Tone; size?: number }) {
  const c = tones[tone];
  return (
    <span className="rg-logo" style={{ color: c.word }}>
      <Mark size={size} tone={tone} />
      <span className="rg-logo-word">
        Revision<span style={{ color: c.accent }}>Gate</span>
      </span>
    </span>
  );
}

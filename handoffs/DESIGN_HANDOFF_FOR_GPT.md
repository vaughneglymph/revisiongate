# Design handoff for GPT: RevisionGate presentation layer

From Claude Fable (brand, copy, layout, presentational components). November 13 2026.

Status: the designed review screen is **wired into `src/main.tsx`** (17:47 ET, on the user's go-ahead). Only the JSX that `App` returns was replaced, plus one import line. All state, handlers, and API calls are yours and unchanged. The previous file is saved at `design/main.tsx.before-wiring.txt`; copy it back over `frontend/src/main.tsx` to roll back. `index.html` now points its icon at `/brand/favicon.svg` and sets `theme-color` to `#132238`.

Checked after wiring: `npx tsc --noEmit` passes, and the app at `/` loads the four packets from `/api/fixtures` and shows the idle state. At 17:50 ET one live run of packet 01 went through the wired screen: Analyze (blocked, two conflicts, one missing finish), Review evidence, then Approve clarification packet. All three API calls returned 200, the approval panel showed, and quote readiness stayed Blocked. Run details reported provider Google Cloud Vertex AI and model gemini-3.5-flash, not IBM Granite. Corrections, reopening a draft, stale versions, and failures have not been exercised through the new screen.

## What exists

| Path | What it is |
|---|---|
| `frontend/src/design/ReviewScreen.tsx` | The whole review screen, presentation only. Typed against your `src/types.ts`. |
| `frontend/src/design/revisiongate.css` | Design tokens (`--rg-*`) and all styles, scoped under `.rg`. Safe to load beside `styles.css`. |
| `frontend/src/design/copy.ts` | Every interface string, keyed by component and state. |
| `frontend/src/design/Logo.tsx`, `logoPaths.ts` | Inline RG monogram and wordmark (color, reversed, mono). `logoPaths.ts` is generated. |
| `frontend/src/design/index.ts` | Import surface: `ReviewScreen`, `Logo`, `Mark`, `copy`. |
| `frontend/src/design/preview/` and `frontend/gallery.html` | State gallery. Dev only: `vite build` does not include it. |
| `frontend/public/brand/` | `favicon.svg`, mark, reversed wordmark for the app to reference. |
| `design/` | Direction and tokens, logo set and usage note, voice guide, copy inventory. |

No new dependencies. Icons are `lucide-react`, type is the Inter Variable file you already ship. `npx tsc --noEmit` passes with these files present.

View the gallery: `npm --prefix frontend run dev -- --port 5199`, then open `http://127.0.0.1:5199/gallery.html`.

## Wiring: what was changed in `src/main.tsx`

`ReviewScreen` takes the state your `App` already holds. This is the JSX `App` now returns. `Header`, `Documents`, `Analysis`, `FieldReview`, and the `disabled`, `part`, `readiness`, and `ReadinessIcon` constants are left in place but unused; remove them when convenient.

```tsx
import { ReviewScreen } from "./design";

return <ReviewScreen
  packets={available} packetId={packetId} packetsLoading={loadingPackets} packet={packet} run={run}
  questions={questions} previousDraft={previousDraft} reviewing={reviewing} analyzing={busy === "Analyzing packet"} busy={busy}
  error={error} notice={notice} stale={stale} edited={edited} canLoadReplacement={!!replacement}
  onSelectPacket={select}
  onAnalyzePacket={analyze}
  onReviewEvidence={openReview}
  onCorrectField={correct}
  onEditDraft={(id, text) => setQuestions(qs => qs.map(q => q.finding_id === id ? { ...q, question: text } : q))}
  onApproveClarification={approve}
  onDownloadExport={download}
  onReopenDraft={reopen}
  onRefreshDraft={() => void correct()}
  onLoadReplacement={() => { if (replacement) { load(replacement, false); setError(""); setNotice("Current extraction loaded. Review its evidence before continuing."); } }}
  onRetryPackets={() => retryFixtures(n => n + 1)}
/>;
```

Notes:

- The screen fills the viewport (`height: 100dvh`) and scrolls its two panes itself. Keep `body { margin: 0 }`. Nothing else from `styles.css` is needed once the old components are gone.
- `openReview` focuses `reviewIntro`, which no longer renders. That is harmless; `ReviewScreen` moves focus to the findings heading itself.

## Props and callbacks

| Prop | Source in your container | Notes |
|---|---|---|
| `packets`, `packetId`, `packetsLoading`, `packet` | `available`, `packetId`, `loadingPackets`, `packet` | Documents show before analysis. |
| `run` | `run` | Rendered as given. Results show only when `run.extracted_fields.RFQ` exists, same test you use. |
| `questions` | `questions` | Controlled textareas. Edited tag compares with `run.questions`. |
| `previousDraft?` | `previousDraft` | Read-only list under the findings: "Previous wording from the cleared draft". |
| `reviewing` | `reviewing` | True opens every finding, shows the extracted-values table and the approve action. |
| `analyzing` | `busy === "Analyzing packet"` | Kept as a boolean so the screen never matches on label text. |
| `busy`, `error`, `notice`, `stale`, `edited` | same names | `busy` text is shown as given. |
| `canLoadReplacement` | `!!replacement` | Shows Load current version. |
| `recordedAt?` | not available yet | See open item 1. |
| `preview?` | gallery only | Never set in the app. |

| Callback (contract name) | Fired by | Guard read from props |
|---|---|---|
| `onAnalyzePacket` | Analyze packet, Try again, Analyze again | `busy`, `packet` |
| `onReviewEvidence` | Review evidence | `allowed_actions.review_evidence` |
| `onCorrectField(correction)` | Save correction | `allowed_actions.correct_fields`. Payload matches your `FieldReview`: whole chosen line as evidence. Return `false` to keep the form open. |
| `onEditDraft(findingId, text)` | Question textarea | `allowed_actions.edit_draft`, no approval, not stale |
| `onApproveClarification` | Approve clarification packet | `allowed_actions.approve_clarification`, no empty question, not stale |
| `onDownloadExport` | Download packet | `allowed_actions.download_export` |
| `onSelectPacket`, `onReopenDraft`, `onRefreshDraft`, `onLoadReplacement`, `onRetryPackets` | Packet menu, Edit clarification, Refresh draft, Load current version, Retry | Outside the six contract names; they map to actions your container already has. |

The component holds only view state: which finding is expanded, which correction form is open, which source line is highlighted. It never compares values, derives readiness, or enables an action the server did not allow.

## Open mapping items

1. **Recorded-run replay.** `provenance.mode` is typed as `"live"` only. To show the striped Recorded run banner, pass `recordedAt` (ISO string), or add `mode: "recorded"` plus `recorded_at` and I will read those. The label reads "Recorded IBM run" only when `provenance.provider` contains "IBM"; otherwise "Recorded model run". The backend currently imports `backend/vertex.py`, so check which provider string the demo will show.
2. **Failure detail.** A failed run carries `analysis.stage` and `analysis.code`, but `types.ts` exposes only `status`, so the error panel shows your message string as given. `copy.error.extractionDetail`, `timeoutDetail`, and `serviceDetail` are written and unused until codes are mapped.
3. **Analysis progress.** Analyze is one request, so the screen lists what the run will do and ticks nothing off. If you stream `analysis.stage`, I will mark steps as they finish.
4. **Citation status.** The contract lists `citation_status`; the view-model has none because bad spans become `needs_review` findings. The "Passage not found at the cited location" label therefore renders only when a cited line is absent from `run.sources`.
5. **Confirming meaning.** There is no per-passage confirm call. Approval is the attestation, stated beside the button, and passage labels switch from "located" to "confirmed by estimator" when `semantic_review_status` changes. If you add a per-finding confirm, I will add the control.
6. **Container strings.** Busy labels, notices, and API error fallbacks live in `main.tsx` and `api.ts`. They read fine. Two to change: "Request unsuccessful" style fallbacks should say what was kept ("Nothing was saved. Your edits are still on screen."), and the export file name in `api.download` differs from the server's `Content-Disposition` name.
7. **No-blocker packets.** Approve is offered with zero questions. The screen keeps the contract label and says: "There are no questions to send. Approving records that you reviewed this packet. It is not an engineering approval." If you would rather not offer approval there, set `allowed_actions.approve_clarification` false and the button disables with a reason.

## Checked, and not checked

Checked in a browser against the gallery: all twelve states at desktop width, narrow layout at 390 px (single column, review first, no sideways scroll), every control has a label, and 27 color pairs meet contrast targets (table in `design/README.md`).

Not checked: an analysis against your live backend (I made no model calls), a screen reader, and the wired three-click path end to end. The blocked-approval case should be checked together once wired: approval panel teal, readiness label still red and Blocked.

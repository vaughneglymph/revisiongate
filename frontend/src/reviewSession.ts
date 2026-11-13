export type SavedReview = {
  packetId: string;
  reviewing: boolean;
  runId: string | null;
  runVersion: number | null;
  draftVersion: number | null;
  edits: Record<string, string>;
  resume: boolean;
  pending?: "analyze" | "correct" | "approve" | "reopen";
};

const identityKey = "revisiongate.workspace.v1";
const reviewKey = "revisiongate.review.v1";
const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;

function openWorkspace(): string {
  const fresh = crypto.randomUUID();
  try {
    const navigation = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
    // New and duplicated tabs can start with a copy of the opener's sessionStorage.
    // Only a reload is entitled to reclaim that saved workspace and its drafts.
    if (navigation?.type === "reload") {
      const previous = sessionStorage.getItem(identityKey);
      if (previous && uuid.test(previous)) return previous;
    }
    sessionStorage.removeItem(reviewKey);
    sessionStorage.setItem(identityKey, fresh);
  } catch {
    // A browser with storage disabled can still run its own in-memory review.
  }
  return fresh;
}

export const workspaceId = openWorkspace();

function isVersion(value: unknown): boolean {
  return value === null || (typeof value === "number" && Number.isSafeInteger(value) && value >= 0);
}

export function readReviewSession(): SavedReview | null {
  try {
    const raw = sessionStorage.getItem(reviewKey);
    if (!raw) return null;
    const record = JSON.parse(raw);
    if (record?.workspace !== workspaceId) return null;
    const value = record.review;
    if (!value || typeof value.packetId !== "string" || typeof value.reviewing !== "boolean"
        || typeof value.resume !== "boolean" || !(value.runId === null || typeof value.runId === "string")
        || !isVersion(value.runVersion) || !isVersion(value.draftVersion)
        || !value.edits || typeof value.edits !== "object" || Array.isArray(value.edits)
        || !Object.values(value.edits).every(text => typeof text === "string")
        || (value.pending !== undefined && !["analyze", "correct", "approve", "reopen"].includes(value.pending))) {
      return null;
    }
    return value;
  } catch {
    return null;
  }
}

export function saveReviewSession(review: SavedReview): void {
  try {
    sessionStorage.setItem(reviewKey, JSON.stringify({ workspace: workspaceId, review }));
  } catch {
    // Storage may be disabled or full; the active review remains available in React.
  }
}

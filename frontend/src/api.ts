import type { Correction, Packet, Question, Run } from "./types";
import { sourceIds } from "./types";

// Keep the workspace with this page's review. Duplicating a tab also starts a fresh review.
const workspaceId = crypto.randomUUID();

export class ApiError extends Error {
  constructor(message: string, public status: number, public currentRun?: Run) { super(message); }
}

async function request(path: string, method = "GET", body?: unknown): Promise<Response> {
  let response: Response;
  try {
    const headers = new Headers({ "X-RevisionGate-Workspace": workspaceId });
    if (body !== undefined) headers.set("Content-Type", "application/json");
    response = await fetch(path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    throw new ApiError("The server could not be reached. Check the connection and retry.", 0);
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const detail = error.detail;
    throw new ApiError(
      typeof detail?.message === "string" ? detail.message : "The server could not complete this request. Retry or reload the current review.",
      response.status, detail?.current_run,
    );
  }
  return response;
}

function versions(run: Run) {
  return { expected_run_version: run.versions.run_version, expected_draft_version: run.versions.draft_version };
}
function runPath(run: Run, action: string) { return "/api/runs/" + encodeURIComponent(run.run_id) + "/" + action; }

export const api = {
  async fixtures(): Promise<Packet[]> { return (await (await request("/api/fixtures")).json()).packets; },
  async analyze(packet: Packet): Promise<Run> { return (await request("/api/analyze", "POST", packet)).json(); },
  async correct(run: Run, corrections: Correction[]): Promise<Run> {
    return (await request(runPath(run, "fields"), "PATCH", { ...versions(run), corrections })).json();
  },
  async reopen(run: Run): Promise<Run> {
    return (await request(runPath(run, "reopen"), "POST", versions(run))).json();
  },
  async approve(run: Run, questions: Question[]): Promise<Run> {
    return (await request(runPath(run, "approve-clarification"), "POST", {
      ...versions(run), questions, reviewed_finding_ids: run.findings.map(f => f.finding_id),
      reviewed_sources: [...sourceIds], confirmed_meaning_and_completeness: true,
    })).json();
  },
  async download(run: Run) {
    const response = await request(runPath(run, "export"));
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = run.packet.packet_id + "-clarification.json";
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  },
};

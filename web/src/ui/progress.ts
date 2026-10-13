import type { Job } from "../data/contract";

/** Zero-based visual steps. Unknown/closed requests never imply a successful pickup. */
export function statusStep(state: string): number | null {
  switch (state) {
    case "received": return 0;
    case "reviewed": case "waiting": return 1;
    case "taken": case "window": case "held":
    case "already_left": case "not_found": case "needs_more_help": return 2;
    case "on_the_way": case "on_scene": return 3;
    case "done": return 4;
    default: return null;
  }
}

export function jobStep(job: Pick<Job, "state" | "window">): number {
  switch (job.state) {
    case "closed": return 4;
    case "on_scene": return 3;
    case "on_the_way": return 2;
    case "held": return 0; // The withdrawn estimate is not a current time setting.
    case "taken": return job.window ? 1 : 0;
  }
}

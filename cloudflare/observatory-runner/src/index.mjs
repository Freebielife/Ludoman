import { projects } from "./projects.mjs";

const GITHUB_API = "https://api.github.com";
const GITHUB_API_VERSION = "2026-03-10";
const TICK_MINUTES = 10;

export function validateProject(project) {
  if (!project || typeof project !== "object") throw new Error("Invalid project configuration");
  for (const field of ["id", "owner", "repo", "workflow", "ref"]) {
    if (typeof project[field] !== "string" || !/^[A-Za-z0-9._-]+$/.test(project[field])) {
      throw new Error("Invalid " + field + " in project configuration");
    }
  }
  if (typeof project.enabled !== "boolean") throw new Error("Project enabled flag must be boolean");
  const { everyMinutes, phaseMinutes } = project;
  if (!Number.isInteger(everyMinutes) || everyMinutes < TICK_MINUTES ||
      everyMinutes > 1440 || 1440 % everyMinutes !== 0 ||
      everyMinutes % TICK_MINUTES !== 0) {
    throw new Error("Invalid everyMinutes for " + project.id);
  }
  if (!Number.isInteger(phaseMinutes) || phaseMinutes < 0 ||
      phaseMinutes >= everyMinutes || phaseMinutes % TICK_MINUTES !== 0) {
    throw new Error("Invalid phaseMinutes for " + project.id);
  }
}

export function selectDueProjects(scheduledTime, registry = projects) {
  const at = new Date(scheduledTime);
  if (!Number.isFinite(at.getTime())) throw new Error("Invalid scheduled time");
  // Slots repeat every UTC day; everyMinutes must divide 1440.
  const minuteOfDay = at.getUTCHours() * 60 + at.getUTCMinutes();
  for (const project of registry) validateProject(project);
  const ids = registry.map(p => p.id);
  if (new Set(ids).size !== ids.length) throw new Error("Duplicate project ID");
  return registry.filter(p => p.enabled && minuteOfDay % p.everyMinutes === p.phaseMinutes);
}

export async function dispatchDue({ scheduledTime, token, registry = projects, fetcher = fetch }) {
  const due = selectDueProjects(scheduledTime, registry);
  if (!due.length) return [];
  if (typeof token !== "string" || !token.trim()) {
    throw new Error("GITHUB_ACTIONS_TOKEN secret is missing");
  }

  // Failures for one repository do not prevent other repositories dispatching.
  const outcomes = await Promise.allSettled(due.map(async project => {
    const endpoint = GITHUB_API + "/repos/" +
      encodeURIComponent(project.owner) + "/" +
      encodeURIComponent(project.repo) + "/actions/workflows/" +
      encodeURIComponent(project.workflow) + "/dispatches";
    const response = await fetcher(endpoint, {
      method: "POST",
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: "Bearer " + token,
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ ref: project.ref })
    });
    if (!response.ok) {
      throw new Error(project.id + ": GitHub dispatch HTTP " + response.status);
    }
    return project.id;
  }));

  const failures = outcomes.flatMap((r, i) =>
    r.status === "rejected"
      ? [due[i].id + ": " + (r.reason instanceof Error ? r.reason.message : "dispatch failed")]
      : []);
  if (failures.length) {
    // Never log request headers, GitHub tokens or response bodies.
    throw new Error("Some observatories could not start: " + failures.join("; "));
  }
  return outcomes.map(r => r.value);
}

export default {
  // No public HTTP trigger. Only the authenticated Cloudflare cron scheduler
  // invokes scheduled(); this prevents strangers from starting Actions jobs.
  fetch() {
    return new Response("Not found", { status: 404 });
  },
  async scheduled(event, env) {
    const dispatched = await dispatchDue({
      scheduledTime: event.scheduledTime,
      token: env.GITHUB_ACTIONS_TOKEN
    });
    console.log(dispatched.length
      ? "Observatory dispatch accepted: " + dispatched.join(", ")
      : "No observatories due in this slot");
  }
};

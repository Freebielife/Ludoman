import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import worker, { dispatchDue, selectDueProjects, validateProject } from "../src/index.mjs";
import { projects } from "../src/projects.mjs";

const monday = "2026-11-16T12:00:00.000Z";
const setup = (overrides = {}) => ({
  id: "new-token", owner: "Freebielife", repo: "NewToken", workflow: "update.yml",
  ref: "main", everyMinutes: 30, phaseMinutes: 10, enabled: true, ...overrides
});

test("Ludoman fires at :00 and :30 UTC, with future projects offset", () => {
  const registry = [projects[0], setup()];
  assert.deepEqual(selectDueProjects(monday, registry).map(p => p.id), ["ludoman"]);
  assert.deepEqual(selectDueProjects("2026-11-16T12:10:00Z", registry).map(p => p.id), ["new-token"]);
  assert.deepEqual(selectDueProjects("2026-11-16T12:20:00Z", registry), []);
  assert.deepEqual(selectDueProjects("2026-11-16T12:30:00Z", registry).map(p => p.id), ["ludoman"]);
  assert.deepEqual(selectDueProjects("2026-11-16T12:40:00Z", registry).map(p => p.id), ["new-token"]);
});

test("disabled project cannot be dispatched", () => {
  const disabled = setup({ enabled: false, phaseMinutes: 0 });
  assert.deepEqual(selectDueProjects(monday, [disabled]), []);
});

test("future projects can request slower 60- or 120-minute cadence", () => {
  const registry = [setup({ everyMinutes: 60, phaseMinutes: 0 }),
    setup({ id: "new-token-2", everyMinutes: 120, phaseMinutes: 30 })];
  assert.equal(selectDueProjects(monday, registry).length, 1);
  assert.equal(selectDueProjects("2026-11-16T12:30:00Z", registry).length, 1);
  assert.equal(selectDueProjects("2026-11-16T13:30:00Z", registry).length, 0);
});

test("validates project configuration and uniqueness", () => {
  assert.doesNotThrow(() => validateProject(projects[0]));
  assert.throws(() => validateProject(setup({ everyMinutes: 17 })), /everyMinutes/);
  assert.throws(() => validateProject(setup({ phaseMinutes: 7 })), /phaseMinutes/);
  assert.throws(() => validateProject(setup({ owner: "../unsafe" })), /owner/);
  assert.throws(() => selectDueProjects(monday, [setup(), setup()]), /Duplicate/);
});

test("GitHub workflow_dispatch uses fine-grained token securely", async () => {
  const calls = [];
  const sent = await dispatchDue({
    scheduledTime: monday, token: "test-secret", registry: [projects[0]],
    fetcher: async (url, init) => {
      calls.push({ url, init });
      return { ok: true, status: 204 };
    }
  });
  assert.deepEqual(sent, ["ludoman"]);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url,
    "https://api.github.com/repos/Freebielife/Ludoman/actions/workflows/update.yml/dispatches");
  assert.equal(calls[0].init.method, "POST");
  assert.equal(calls[0].init.headers.Authorization, "Bearer test-secret");
  assert.deepEqual(JSON.parse(calls[0].init.body), { ref: "main" });
});

test("no token means no API request, unless no projects are due", async () => {
  const spy = async () => { throw new Error("Should not dispatch"); };
  await assert.rejects(() => dispatchDue({
    scheduledTime: monday, token: "", fetcher: spy
  }), /GITHUB_ACTIONS_TOKEN/);
  assert.deepEqual(await dispatchDue({
    scheduledTime: "2026-11-16T12:10:00Z", token: "", fetcher: spy
  }), []);
});

test("failed repository dispatch does not block other configured projects", async () => {
  const registry = [projects[0], setup({ phaseMinutes: 0 })];
  const requests = [];
  await assert.rejects(() => dispatchDue({
    scheduledTime: monday, token: "test-secret", registry,
    fetcher: async url => {
      requests.push(url);
      return { ok: !url.includes("/NewToken/"), status: url.includes("/NewToken/") ? 403 : 204 };
    }
  }), /new-token.*403/);
  assert.equal(requests.length, 2);
});

test("incoming HTTP requests cannot manually trigger jobs", async () => {
  const result = await worker.fetch(new Request("https://worker.example/"), {});
  assert.equal(result.status, 404);
});

test("cloudflare scheduled handler dispatches configured repos", async () => {
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push([url, options]);
    return { ok: true, status: 204 };
  };
  try {
    await worker.scheduled({ scheduledTime: Date.parse(monday) }, { GITHUB_ACTIONS_TOKEN: "test-secret" });
    assert.equal(calls.length, 1);
  } finally {
    globalThis.fetch = original;
  }
});

test("wrangler cron matches the ten-minute dispatcher slot", () => {
  const json = JSON.parse(readFileSync(new URL("../wrangler.jsonc", import.meta.url), "utf8"));
  assert.equal(json.name, "freebie-observatory-runner");
  assert.equal(json.main, "src/index.mjs");
  assert.deepEqual(json.triggers.crons, ["*/10 * * * *"]);
  assert.equal(JSON.stringify(json).includes("GITHUB_ACTIONS_TOKEN"), false);
});

test("403 distinguishes insufficient token permissions without leaking response details", async () => {
  const response = new Response(JSON.stringify({
    message: "Resource not accessible by personal access token",
    secret: "not-to-be-logged"
  }), { status: 403, headers: {
    "content-type": "application/json",
    "x-accepted-github-permissions": "actions=write",
    "x-ratelimit-remaining": "4900"
  } });
  await assert.rejects(
    () => dispatchDue({ scheduledTime: monday, token: "test-secret",
      fetcher: async () => response }),
    error => {
      assert.match(error.message, /reason=token-repository-permissions/);
      assert.match(error.message, /required_permissions=actions=write/);
      assert.match(error.message, /rate_remaining=4900/);
      assert.doesNotMatch(error.message, /test-secret|not-to-be-logged/);
      return true;
    }
  );
});

test("403 rate limit is classified separately from permissions", async () => {
  await assert.rejects(
    () => dispatchDue({ scheduledTime: monday, token: "test-secret",
      fetcher: async () => new Response(JSON.stringify({
        message: "API rate limit exceeded for this user."
      }), { status: 403, headers: { "x-ratelimit-remaining": "0" } }) }),
    /reason=rate-limit.*rate_remaining=0/
  );
});

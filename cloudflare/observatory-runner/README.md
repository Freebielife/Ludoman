# Shared TON Observatory Runner (Cloudflare Worker)

This is a **single, shared scheduler** for Ludoman and future TON observatories. The source currently lives in Ludoman's repository, but the running Worker is independent of any token. It does not serve TON Sites, fetch blockchain data, modify tokens, or handle Telegram messages. Each project continues to collect/build its own on-chain snapshot in its GitHub repository.

**Status (20 Nov 2026):** The GitHub Actions history for Ludoman includes regular successful `workflow_dispatch` launches at **12:00, 12:30 UTC** and earlier, consistent with the configured external 30-minute runner. This is evidence that GitHub accepts remote dispatches, but Cloudflare's live deployment, secrets and logs must still be checked in its dashboard; these cannot be authenticated by repository contents alone. The legacy GitHub cron was removed from Ludoman `update.yml`.

**TAC onboarding:** A second registry record for `Freebielife/Freebielife-TAC-Observatory` is now present with `workflow:"refresh.yml"`, `everyMinutes:30`, and `phaseMinutes:10` (planned runs at :10 / :40 UTC). It is deliberately **disabled** until the existing Cloudflare Worker secret `GITHUB_ACTIONS_TOKEN` is authorized to dispatch the new repository. Without that permission enabling TAC would produce GitHub 403 responses and failed Worker runs. To activate safely: (1) in GitHub fine-grained token settings add that exact repository with **Actions: Read and write**, (2) confirm the Worker secret still uses that token (replace its encrypted value if it was regenerated), (3) set TAC's `enabled:true` here and deploy the connected Worker, (4) observe successful TAC `workflow_dispatch` runs at two consecutive :10 / :40 UTC slots. **Never paste a PAT into chat, GitHub code or screenshots.** Until these steps are complete TAC retains its own native GitHub `*/10` cron as a fallback, though scheduled starts may be delayed or skipped by GitHub.

## Architecture

```text
Cloudflare Cron (*/10, UTC)
  -> freebie-observatory-runner
  -> select enabled projects due in their 10-minute slots
  -> GitHub API: workflow_dispatch
  -> each project's GitHub Actions update.yml
  -> snapshot.json + standalone index.html
  -> existing published TON Site reads refreshed GitHub data
```

A project configured for `everyMinutes: 30` runs on the chosen phase every half hour. The 10-minute global Worker tick lets different projects start at staggered times. For example Ludoman at `:00`/`:30`, a second project at `:10`/`:40`, a third at `:20`/`:50` (all UTC). A future project may use 10, 30, 60, 120, or any multiple of 10 that divides 1440.

## One-time setup (user account access required)

1. In GitHub, create a **fine-grained personal access token** for the owner `Freebielife`. Repository access: **Only selected repositories**, initially `Ludoman`. Repository permissions: **Actions — Read and write**. Use a sensible expiration and store the token securely. New repositories added later must also be granted access. Never commit or send this value in chat.
2. In **Cloudflare Dashboard → Workers & Pages**, create a new Worker connected to the GitHub repository `Freebielife/Ludoman`. Use its **main** branch and **Root directory: `cloudflare/observatory-runner`**. Worker name must equal `freebie-observatory-runner` from `wrangler.jsonc`. Deploy command: `npx wrangler deploy`. This is a *new Worker*, not the existing Telegram bot Worker.
3. In the new Worker's **Settings → Variables and Secrets**, create an **encrypted Secret**, name `GITHUB_ACTIONS_TOKEN`, value = your private GitHub token. Do not set it as a plaintext variable. Save/deploy the secret.
4. Verify Cloudflare logs show `Observatory dispatch accepted: ludoman` at :00 or :30 UTC and that `Freebielife/Ludoman → Actions → Refresh LUDOMAN data` has a new `workflow_dispatch` run which successfully updates the snapshot.
5. **Only after repeated confirmed successes**, remove the old `schedule:` block from Ludoman `.github/workflows/update.yml`, preserving `workflow_dispatch` and `push` triggers, then verify another Cloudflare-triggered run. Until step 5, duplicate runs are possible because the old GitHub 10-minute cron remains in place.
6. Keep the original KITO updater and the separate Telegram Worker unchanged.

Cloudflare Git integration deploys code changes from `main`. If your dashboard already has a Worker with this exact name, choose a different **new** name and update `wrangler.jsonc` before connecting; do not overwrite another Worker.

## New project onboarding

- Add one record to `src/projects.mjs` with ID, owner, repo, workflow name, default-branch ref, `everyMinutes`, `phaseMinutes`, and `enabled:true`.
- Configure that repository's workflow to accept `workflow_dispatch` and to build/publish its own site data.
- Add that repository to the same fine-grained token's selected repositories or use an appropriately scoped GitHub App token.
- Run `node --test cloudflare/observatory-runner/tests/*.test.mjs` in the repository root. Push to the connected production branch, confirm Cloudflare auto-deploys, and inspect two scheduled runs before depending on it.
- Use a new phase (for a 30-minute cadence: 0, 10, or 20) to avoid synchronized builds. If more than three projects share 30-minute cadence, distribute projects evenly among the phases.
- Future Telegram notifications are intentionally **not** included until this scheduler has been tested with Ludoman and a second project.

## Security and troubleshooting

- Public HTTP requests to this Worker return HTTP 404. A secret token cannot be supplied via its URL; only Cloudflare's built-in cron invokes the scheduling handler.
- The GitHub token is required only when a project is due. A missing token or a rejected GitHub API request causes a failed run instead of false success.
- Cloudflare logs show project IDs and GitHub status codes, never the token, request headers, or response body.
- A GitHub 401/403 means token or repository permissions; 404 commonly means repo/workflow inaccessible to the token or a wrong name; GitHub 200/204 indicates accepted dispatch, **not that the collector succeeded**. Confirm the actual Actions job.
- Cloudflare Cron runs in UTC; dashboard changes can take a few minutes to propagate. User's local time is not used to determine slots.
- This scheduler does not auto-publish changes to a TON Storage bag. Existing TON Sites read the GitHub snapshot as before.

## Local testing

```bash
node --test cloudflare/observatory-runner/tests/*.test.mjs
```

Manual deployment (requires local Cloudflare login) from this directory: `npx wrangler deploy`. Do not store `.dev.vars` or tokens in Git.

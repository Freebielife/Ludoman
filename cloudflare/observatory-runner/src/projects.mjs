// Central registry for all future TON observatories.
// Each enabled project runs once per everyMinutes, at its phaseMinutes UTC offset.
// Both values must be multiples of 10. Stagger future projects across phases.
export const projects = Object.freeze([
  Object.freeze({
    id: "ludoman",
    owner: "Freebielife",
    repo: "Ludoman",
    workflow: "update.yml",
    ref: "main",
    everyMinutes: 30,
    phaseMinutes: 0,
    enabled: true
  }),
  // TAC has been authorized by the owner in the existing Cloudflare token's
  // selected repositories (2026-11-20). Actual dispatch must be confirmed in
  // Cloudflare logs and GitHub Actions after deployment of this revision.
  Object.freeze({
    id: "tac",
    owner: "Freebielife",
    repo: "Freebielife-TAC-Observatory",
    workflow: "refresh.yml",
    ref: "main",
    everyMinutes: 30,
    phaseMinutes: 10,
    enabled: true
  }),
  // ARBUZ uses the third slot; GitHub token access must include this repository.
  Object.freeze({
    id: "arbuz",
    owner: "Freebielife",
    repo: "ARBUZ",
    workflow: "update.yml",
    ref: "main",
    everyMinutes: 30,
    phaseMinutes: 20,
    enabled: true
  }),
  // Notcoin public repo authorized by the owner (2026-11-22).
  // Cloudflare deployment and successful dispatch require live verification.
  Object.freeze({
    id: "notcoin",
    owner: "Freebielife",
    repo: "Notcoin",
    workflow: "update.yml",
    ref: "main",
    everyMinutes: 30,
    phaseMinutes: 20,
    enabled: true
  }),
  Object.freeze({
    id: "mem",
    owner: "Freebielife",
    repo: "NOT-MEME",
    workflow: "update.yml",
    ref: "main",
    everyMinutes: 30,
    phaseMinutes: 0,
    enabled: true
  })
,
  // MAJOR: flag 003; production dispatch and token access require verification.
  Object.freeze({
    id: "major", owner: "Freebielife", repo: "Major",
    workflow: "update.yml", ref: "main",
    everyMinutes: 30, phaseMinutes: 10, enabled: true
  })
,
  // LAMBO: token access and live Cloudflare dispatch require verification.
  Object.freeze({
    id: "lambo", owner: "Freebielife", repo: "Lambo",
    workflow: "update.yml", ref: "main",
    everyMinutes: 30, phaseMinutes: 10, enabled: true
  })
]);

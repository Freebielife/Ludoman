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
  })
]);

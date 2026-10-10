/*
  Saved game state (progress, circuit settings, Dark Port seed) in localStorage.

  Qollab allows one IonQ job per Run, so players press Stop and Run between IonQ
  confirmations; saving here keeps their progress and circuit across Runs.
  Storage can be unavailable (private mode, sandboxed frames): every access is
  wrapped and the game works without it.
*/

const KEY = "phase-shift:v1";

function emptyState() {
  return { progress: { stars: {}, ionq: [] }, attempts: {}, current: null };
}

export function loadState() {
  try {
    const raw = globalThis.localStorage?.getItem(KEY);
    if (!raw) return emptyState();
    const data = JSON.parse(raw);
    return {
      progress: data.progress ?? { stars: {}, ionq: [] },
      attempts: data.attempts && typeof data.attempts === "object" ? data.attempts : {},
      current: typeof data.current === "string" ? data.current : null,
    };
  } catch (_err) {
    return emptyState();
  }
}

export function saveState(state) {
  try {
    globalThis.localStorage?.setItem(KEY, JSON.stringify(state));
  } catch (_err) {
    /* storage unavailable: progress lasts for this page only */
  }
}

export function newSeed() {
  try {
    const a = new Uint32Array(1);
    globalThis.crypto.getRandomValues(a);
    return a[0] % 1000000000;
  } catch (_err) {
    return Math.floor(Math.random() * 1000000000);
  }
}

/*
  Bridge between the page and the Python module `phaseshift.api`.

  - On Qollab, `api` is the namespace from the STATIC import in main.js
    (`import * as api from "phaseshift.api"`), served by Pyodide. Locally,
    dev/index.html maps the same name to dev/py-shim.js, which forwards calls to
    dev/server.py (real CPython + Qiskit). Nothing here knows which one it is.
  - `backend` is the global Qollab creates from "Select QPU". We never create it.
  - Calls are positional: fn.callPromising(backend, ...args). Results are
    converted with toJs({dict_converter: Object.fromEntries}) and the proxy is
    destroyed right after.
  - One call at a time (busy flag), with a timeout so the UI never stays "running".
*/

export const TIMEOUT_MS = 180000;

function plain(proxy) {
  try {
    return proxy && typeof proxy.toJs === "function"
      ? proxy.toJs({ dict_converter: Object.fromEntries })
      : proxy;
  } finally {
    proxy?.destroy?.();
  }
}

/** Qollab's injected backend, or undefined when none was selected / running locally. */
export function qollabBackend() {
  try {
    // eslint-disable-next-line no-undef
    if (typeof backend !== "undefined" && backend !== null) return backend;
  } catch (_err) {
    /* not defined */
  }
  return globalThis.backend ?? undefined;
}

/** Let the browser paint (e.g. "Running…") before Python blocks the main thread. */
export function nextPaint() {
  return new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve, 0)));
}

export function createBridge(api) {
  let busy = false;

  async function raw(name, args) {
    const fn = api[name];
    if (!fn || typeof fn.callPromising !== "function") {
      return { ok: false, code: "missing", error: `Python function ${name} is unavailable` };
    }
    let timer;
    const call = fn.callPromising(...args);
    const timeout = new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error("timeout")), TIMEOUT_MS);
    });
    try {
      return plain(await Promise.race([call, timeout]));
    } catch (err) {
      if (String(err?.message) === "timeout") {
        call.then((p) => p?.destroy?.(), () => {});
        return { ok: false, code: "timeout", error: `No answer after ${TIMEOUT_MS / 1000} s. Try again, or use the in-browser simulator.` };
      }
      return { ok: false, code: "js_error", error: String(err?.message ?? err) };
    } finally {
      clearTimeout(timer);
    }
  }

  return {
    get busy() {
      return busy;
    },
    info: () => raw("info", []),
    backendInfo: () => raw("backend_info", [qollabBackend()]),
    progressStatus: (progress) => raw("progress_status", [progress]),
    preview: (levelId, config, seed) => raw("preview", [levelId, config, seed]),
    defaultConfig: (levelId) => raw("default_config", [levelId]),
    sweep: (levelId, config, seed, reveal) => raw("sweep", [levelId, config, seed, reveal]),

    /** Run a level. Returns null if another run is in progress. */
    async runLevel(levelId, config, options, { onTick } = {}) {
      if (busy) return null;
      busy = true;
      const t0 = performance.now();
      const tick = setInterval(() => onTick?.(Math.round((performance.now() - t0) / 1000)), 1000);
      try {
        await nextPaint();
        return await raw("run_level", [qollabBackend(), levelId, config, options]);
      } finally {
        clearInterval(tick);
        busy = false;
      }
    },
  };
}

/*
  Local stand-in for Qollab's Pyodide module proxy of `phaseshift.api`.
  Each export has callPromising(...args) and resolves to an object with
  toJs() and destroy(), like a Pyodide PyProxy. Calls go to dev/server.py.
*/

const TOKEN = "__qollab_backend__";
const isBackend = (a) => a !== undefined && a !== null && a === globalThis.backend;

async function call(name, args) {
  const res = await fetch(`/api/${name}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ args: args.map((a) => (isBackend(a) ? TOKEN : a ?? null)) }),
  });
  const data = await res.json();
  return { toJs: () => data, destroy: () => {} };
}

const fn = (name) => ({ callPromising: (...args) => call(name, args) });

// Each page load is a new "Qollab Run": fresh backend object on the server.
await fetch("/api/_new_run", { method: "POST" });

export const info = fn("info");
export const backend_info = fn("backend_info");
export const default_config = fn("default_config");
export const progress_status = fn("progress_status");
export const preview = fn("preview");
export const run_level = fn("run_level");
export const sweep = fn("sweep");

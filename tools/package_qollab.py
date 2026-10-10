"""Build the Qollab upload zip from an explicit allowlist and check Qollab's limits.

    python tools/package_qollab.py        # writes dist/phase-shift-qollab.zip

Qollab "JS + Qiskit" project layout (all paths relative to the project root):
    index.html  main.js  main.css         page (body-only HTML), logic, styles
    web/*.js                              UI modules imported by main.js
    phaseshift/*.py                       Python package; main.js imports phaseshift.api
    requirements.txt  README.md  LICENSE

Checks (limits other teams found on the platform): at most 100 files, each under
2 MB, README under 65,000 characters, no caches/secrets/dev files.
Development-only files (dev/, tests/, tools/, notebooks/, docs/, assets/) stay out.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
ZIP = DIST / "phase-shift-qollab.zip"

MAX_FILES = 100
MAX_BYTES = 2 * 1024 * 1024
MAX_README = 65_000
SECRET = re.compile(
    r"(api[_-]?key|secret|token|passw(or)?d)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"
    r"|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36,}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----",
    re.IGNORECASE,
)


def allowlist() -> list[Path]:
    files = [ROOT / n for n in ("index.html", "main.js", "main.css", "requirements.txt", "README.md", "LICENSE")]
    files += sorted((ROOT / "web").glob("*.js"))
    files += sorted((ROOT / "phaseshift").glob("*.py"))
    return files


def fail(msg: str) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


def main() -> int:
    files = allowlist()
    for f in files:
        if not f.is_file():
            return fail(f"missing {f.relative_to(ROOT)}")
        size = f.stat().st_size
        if size >= MAX_BYTES:
            return fail(f"{f.relative_to(ROOT)} is {size} bytes (limit {MAX_BYTES})")
        text = f.read_text(encoding="utf-8")
        if SECRET.search(text):
            return fail(f"possible secret in {f.relative_to(ROOT)}")
    if len(files) > MAX_FILES:
        return fail(f"{len(files)} files (limit {MAX_FILES})")
    readme_chars = len((ROOT / "README.md").read_text(encoding="utf-8"))
    if readme_chars >= MAX_README:
        return fail(f"README.md has {readme_chars} characters (limit {MAX_README})")
    main_js = (ROOT / "main.js").read_text(encoding="utf-8").rstrip().splitlines()
    if main_js[-1].strip() != "await new Promise(() => {});":
        return fail("main.js must end with `await new Promise(() => {});` (keeps IonQ reachable)")
    if 'import * as api from "phaseshift.api";' not in "\n".join(main_js):
        return fail("main.js must statically import phaseshift.api")

    DIST.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.relative_to(ROOT).as_posix())
    total = sum(f.stat().st_size for f in files)
    print(f"wrote {ZIP.relative_to(ROOT)}: {len(files)} files, {total / 1024:.0f} KiB, README {readme_chars} chars")
    for f in files:
        print(f"  {f.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

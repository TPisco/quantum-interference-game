"""Tidy TTS voiceover files: trim the ends and shorten over-long pauses.

    python3 vo_clean.py in_dir out_dir

TTS engines sometimes leave multi-second gaps inside a sentence. Any internal
silence longer than MAX_PAUSE is cut down to KEEP_PAUSE; leading and trailing
silence is trimmed to a few frames. Normal pauses (commas, full stops) stay.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

THRESH = "-40dB"
MAX_PAUSE, KEEP_PAUSE = 0.7, 0.45
LEAD, TAIL = 0.06, 0.15


def silences(path: Path) -> tuple[list[tuple[float, float]], float]:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af",
                          f"silencedetect=n={THRESH}:d=0.3", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", str(path)], text=True))
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    if len(ends) < len(starts):
        ends.append(dur)
    return [(max(0.0, a), b) for a, b in zip(starts, ends)], dur


def keep_ranges(sil: list[tuple[float, float]], dur: float) -> list[tuple[float, float]]:
    cuts = []
    for a, b in sil:
        if a <= 0.01:
            cuts.append((0.0, max(0.0, b - LEAD)))
        elif b >= dur - 0.01:
            cuts.append((min(dur, a + TAIL), dur))
        elif b - a > MAX_PAUSE:
            cuts.append((a + KEEP_PAUSE / 2, b - KEEP_PAUSE / 2))
    keep, t = [], 0.0
    for a, b in sorted(cuts):
        if a > t:
            keep.append((t, a))
        t = max(t, b)
    if t < dur:
        keep.append((t, dur))
    return [(a, b) for a, b in keep if b - a > 0.01]


def clean(src: Path, dst: Path) -> str:
    sil, dur = silences(src)
    keep = keep_ranges(sil, dur)
    parts = [f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[p{i}]" for i, (a, b) in enumerate(keep)]
    chain = ";".join(parts) + ";" + "".join(f"[p{i}]" for i in range(len(keep))) + \
        f"concat=n={len(keep)}:v=0:a=1[a]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-filter_complex", chain,
                    "-map", "[a]", "-ar", "48000", str(dst)], check=True)
    new = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", str(dst)], text=True))
    return f"{src.name}: {dur:.2f}s -> {new:.2f}s"


if __name__ == "__main__":
    src_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted(src_dir.glob("*.wav")):
        print(clean(f, out_dir / f.name))

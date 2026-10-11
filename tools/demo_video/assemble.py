"""Join cleaned voiceover segments into one track and print a timing sheet.

    python3 assemble.py script_v2.json clean_dir out.wav [gap_s] [lead_s] [tail_s]

Segments follow the order in the script, separated by a fixed gap, after a
short lead-in and before a tail for the end card. The mix is normalised to
-16 LUFS (true peak -1.5 dB). The sheet gives each segment's start and end in
the full track, which is what the screen recordings are cut to.
"""

from __future__ import annotations

import json
import subprocess
import sys


def duration(path: str) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path], text=True))


def mmss(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:05.2f}"


def main() -> None:
    script, clean, out = sys.argv[1], sys.argv[2], sys.argv[3]
    gap = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
    lead = float(sys.argv[5]) if len(sys.argv) > 5 else 1.5
    tail = float(sys.argv[6]) if len(sys.argv) > 6 else 3.0
    segs = json.load(open(script))["segments"]
    inputs, filters, rows, t = [], [], [], lead
    for i, seg in enumerate(segs):
        path = f"{clean}/{seg['id']}.wav"
        d = duration(path)
        rows.append((seg["id"], t, t + d, d, seg.get("title", "")))
        inputs += ["-i", path]
        ms = int(t * 1000)
        filters.append(f"[{i}:a]adelay={ms}|{ms},apad[a{i}]")
        t += d + gap
    total = t - gap + tail
    mix = "".join(f"[a{i}]" for i in range(len(segs)))
    filters.append(f"{mix}amix=inputs={len(segs)}:normalize=0,atrim=0:{total:.3f},"
                   "loudnorm=I=-16:TP=-1.5:LRA=11[out]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "[out]", "-ar", "48000", out], check=True)
    print(f"{'seg':4} {'start':>8} {'end':>8} {'len':>6}  title")
    for sid, a, b, d, title in rows:
        print(f"{sid:4} {mmss(a):>8} {mmss(b):>8} {d:6.2f}  {title}")
    print(f"TOTAL {mmss(total)}  (lead {lead}s, gaps {gap}s, tail {tail}s)")


if __name__ == "__main__":
    main()

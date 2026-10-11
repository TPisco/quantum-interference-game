"""Write burned-in captions (.srt) for the assembled voiceover.

    python3 make_captions.py script_v2.json clean_dir out.srt [gap_s] [lead_s]

Use the same gap and lead as assemble.py so caption times match the full track.
Each segment's caption text (digits) and spoken text (words) are split at the
same sentence marks. faster-whisper word timestamps, matched to the spoken
text, bracket each mark; the cue changes at the voice's pause inside that
bracket (the last pause before the next chunk's first word). Needs ffmpeg and
faster-whisper, both preinstalled in the Higgsfield sandbox.
"""

from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys

MAX_CHARS, MIN_CHARS = 84, 22
SPLIT = re.compile(r"(?<=[.?:;])\s+")


def duration(path: str) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path], text=True))


def pauses(path: str) -> list[tuple[float, float]]:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=n=-35dB:d=0.12",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    if len(ends) < len(starts):
        ends.append(duration(path))
    return [(max(0.0, a), b) for a, b in zip(starts, ends)]


def chunks(text: str, spoken: str) -> list[tuple[str, str]]:
    a, b = SPLIT.split(text.strip()), SPLIT.split(spoken.strip())
    if len(a) != len(b):
        return [(text, spoken)]
    # A short chunk that ends in ':' or '?' leads into the next one ("Why? Follow the
    # arrows."); any other short chunk finishes the previous one ("... again: still 50/50.").
    pairs: list[tuple[str, str]] = []
    carry: tuple[str, str] | None = None
    for ca, cb in zip(a, b):
        if carry:
            ca, cb, carry = carry[0] + " " + ca, carry[1] + " " + cb, None
        if len(ca) < MIN_CHARS and ca[-1] in ":?":
            carry = (ca, cb)
        elif len(ca) < MIN_CHARS and pairs and len(pairs[-1][0]) + len(ca) < MAX_CHARS:
            pairs[-1] = (pairs[-1][0] + " " + ca, pairs[-1][1] + " " + cb)
        else:
            pairs.append((ca, cb))
    if carry:
        pairs.append(carry)
    out: list[tuple[str, str]] = []
    for ca, cb in pairs:
        sa, sb = ca.split(", "), cb.split(", ")
        if len(ca) > MAX_CHARS and len(sa) == len(sb) > 1:
            k = min(range(1, len(sa)), key=lambda i: abs(len(", ".join(sa[:i])) - len(ca) / 2))
            out += [(", ".join(sa[:k]) + ",", ", ".join(sb[:k]) + ","), (", ".join(sa[k:]), ", ".join(sb[k:]))]
        else:
            out.append((ca, cb))
    return out


def norm(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "", word.lower())


def timed(path: str, parts: list[tuple[str, str]], model) -> list[tuple[float, float, str]]:
    """(start, end, caption) inside one file, cut at the pauses between parts."""
    dur, sil = duration(path), pauses(path)
    s0 = next((b for a, b in sil if a <= 0.01), 0.0)
    s1 = next((a for a, b in sil if b >= dur - 0.01), dur)
    inner = [(a, b) for a, b in sil if a > 0.01 and b < dur - 0.01]
    heard = [w for s in model.transcribe(path, word_timestamps=True, beam_size=5)[0] for w in s.words]
    said = [norm(w) for _, sp in parts for w in sp.split()]
    match = {}  # index in the spoken text -> index in what whisper heard
    blocks = difflib.SequenceMatcher(None, said, [norm(w.word) for w in heard], autojunk=False)
    for blk in blocks.get_matching_blocks():
        match.update({blk.a + k: blk.b + k for k in range(blk.size)})
    cuts, n = [], 0
    for _, sp in parts[:-1]:
        n += len(sp.split())
        prev = max((i for i in match if i < n), default=None)
        nxt = min((i for i in match if i >= n), default=None)
        lo = heard[match[prev]].end if prev is not None else s0
        hi = heard[match[nxt]].start if nxt is not None else s1
        inside = [(a, b) for a, b in inner if lo - 0.15 <= a <= hi + 0.05]  # whisper's word edges run early
        if inside:
            # The pause right before the next chunk's first word, when whisper heard
            # that word; otherwise the longest pause (full stops pause longest).
            cuts.append(inside[-1] if nxt == n else max(inside, key=lambda p: p[1] - p[0]))
        else:
            x = hi if nxt == n else (lo + hi) / 2
            cuts.append((x, x))
    starts = [s0] + [b for _, b in cuts]
    ends = [a for a, _ in cuts] + [s1]
    return [(st - 0.05, en + 0.2, cap) for (cap, _), st, en in zip(parts, starts, ends)]


def wrap(line: str) -> str:
    if len(line) <= 42:
        return line
    cut = min((i for i, ch in enumerate(line) if ch == " "), key=lambda i: abs(i - len(line) / 2))
    return line[:cut] + "\n" + line[cut + 1:]


def stamp(t: float) -> str:
    ms = int(round(max(0.0, t) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main() -> None:
    from faster_whisper import WhisperModel

    script, clean, out = sys.argv[1], sys.argv[2], sys.argv[3]
    gap = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
    lead = float(sys.argv[5]) if len(sys.argv) > 5 else 1.5
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    cues, t = [], lead
    for seg in json.load(open(script))["segments"]:
        path = f"{clean}/{seg['id']}.wav"
        parts = chunks(seg["text"], seg.get("tts", seg["text"]))
        cues += [[t + a, t + b, cap] for a, b, cap in timed(path, parts, model)]
        t += duration(path) + gap
    for k in range(len(cues) - 1):
        cues[k][1] = min(cues[k][1], cues[k + 1][0] - 0.04)
    with open(out, "w") as f:
        for n, (a, b, cap) in enumerate(cues, 1):
            f.write(f"{n}\n{stamp(a)} --> {stamp(b)}\n{wrap(cap)}\n\n")
    print(f"{len(cues)} captions -> {out}")


if __name__ == "__main__":
    main()

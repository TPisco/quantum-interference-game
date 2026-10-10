"""Render the Phase Shift demo video from an edit decision list (EDL).

    python3 render.py edl.json --work out/ [--only seg03] [--preview]

The EDL (see edl.json) lists segments in order. Each segment is either

* a "card": a full-frame background (video or image) with title text, or
* a "clip": one or more ranges of a screen recording, placed in a framed
  "screen" over a dark background, with eased zooms, labels and callouts.

Every segment may carry a voiceover file ("vo"). The segment is timed to its
voiceover: clip ranges are sped up or slowed down together (within limits) so the
picture lasts as long as the narration plus a small lead and tail. Zooms and labels
are written in SOURCE time (timestamps of the recording), so they stay on the
right moment whatever speed the fit chooses.

After the segments, the script concatenates them, lays the voiceover clips on one
track, normalises loudness to -16 LUFS, writes captions (ASS) from the authored VO
text, timed with Whisper word timestamps when available, and burns them in.

Runs the same locally and in Higgsfield's sandbox (ffmpeg + Pillow; faster-whisper
optional). Fonts are picked from the first existing path in FONT_CANDIDATES.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
# The screen recording sits in a frame, leaving a band at the bottom for captions.
SCREEN_W, SCREEN_H = 1664, 936
SCREEN_X, SCREEN_Y = (W - SCREEN_W) // 2, 26
NAVY = (11, 16, 32)
PANEL = (20, 27, 52)
LINE = (52, 64, 107)
CYAN = (92, 225, 230)
AMBER = (255, 176, 0)
TEXT = (232, 236, 248)
MUTED = (180, 190, 219)

FONT_CANDIDATES = {
    "title": ["/usr/share/fonts/truetype/higgsfield/Montserrat-ExtraBold.ttf",
              "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
              "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "bold": ["/usr/share/fonts/opentype/inter/Inter-Bold.otf",
             "/usr/share/fonts/truetype/higgsfield/Metropolis-ExtraBold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "regular": ["/usr/share/fonts/opentype/inter/Inter-Regular.otf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}
CAPTION_FONT = "DejaVu Sans"  # present in both environments; libass finds it via fontconfig

MIN_SPEED, MAX_SPEED = 0.6, 3.0
VO_LEAD, VO_TAIL = 0.35, 0.45


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES[kind]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def run(cmd: list[str], quiet: bool = True) -> None:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.stderr.write(res.stderr[-4000:])
        raise SystemExit(f"command failed: {' '.join(cmd[:6])} ...")
    if not quiet:
        print(res.stderr[-2000:])


def probe_duration(path: str) -> float:
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", path], text=True)
    return float(out.strip())


def probe_size(path: str) -> tuple[int, int]:
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height", "-of", "csv=p=0", path], text=True)
    w, h = out.strip().split(",")[:2]
    return int(w), int(h)


# --------------------------------------------------------------------------- graphics

def make_background(path: Path, art: str | None) -> None:
    """Dark backdrop: blurred, darkened Higgsfield art if available, else a gradient."""
    if art and os.path.exists(art):
        img = Image.open(art).convert("RGB")
        ratio = max(W / img.width, H / img.height)
        img = img.resize((math.ceil(img.width * ratio), math.ceil(img.height * ratio)), Image.LANCZOS)
        left, top = (img.width - W) // 2, (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(28))
        img = Image.blend(img, Image.new("RGB", (W, H), NAVY), 0.72)
    else:
        img = Image.new("RGB", (W, H), NAVY)
        d = ImageDraw.Draw(img)
        for y in range(H):
            k = y / H
            d.line([(0, y), (W, y)], fill=tuple(int(NAVY[i] * (1 - k) + PANEL[i] * k) for i in range(3)))
    # Soft shadow under the screen frame.
    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle(
        [SCREEN_X - 6, SCREEN_Y + 10, SCREEN_X + SCREEN_W + 6, SCREEN_Y + SCREEN_H + 22], 22, fill=170)
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, shadow)
    img.save(path)


def make_frame_overlay(path: Path) -> None:
    """Rounded corners + thin border drawn on top of the screen recording."""
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mask = Image.new("L", (W, H), 255)
    ImageDraw.Draw(mask).rounded_rectangle(
        [SCREEN_X, SCREEN_Y, SCREEN_X + SCREEN_W - 1, SCREEN_Y + SCREEN_H - 1], 18, fill=0)
    # Outside the rounded rect (only the corners matter) is filled from the background later,
    # so here we only draw the border; corner masking is done with the alpha "cornermask".
    d = ImageDraw.Draw(over)
    d.rounded_rectangle([SCREEN_X, SCREEN_Y, SCREEN_X + SCREEN_W - 1, SCREEN_Y + SCREEN_H - 1], 18,
                        outline=LINE + (255,), width=3)
    over.save(path)
    mask.save(path.with_name("cornermask.png"))


def text_box(lines: list[tuple[str, str, int, tuple]], pad=(30, 22), bar=True, radius=16,
             bg=PANEL + (236,), line_gap=8) -> Image.Image:
    """lines: (text, font_kind, size, color). Returns an RGBA panel image."""
    fonts = [font(k, s) for _, k, s, _ in lines]
    sizes = [f.getbbox(t) for (t, *_), f in zip(lines, fonts)]
    width = max(b[2] - b[0] for b in sizes) + pad[0] * 2 + (10 if bar else 0)
    heights = [f.getbbox("Ag")[3] - f.getbbox("Ag")[1] for f in fonts]
    height = sum(heights) + line_gap * (len(lines) - 1) + pad[1] * 2
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, width - 1, height - 1], radius, fill=bg, outline=LINE + (255,), width=2)
    if bar:
        d.rounded_rectangle([0, 0, 9, height - 1], 4, fill=CYAN + (255,))
    y = pad[1]
    x = pad[0] + (10 if bar else 0)
    for (t, _, _, color), f, h in zip(lines, fonts, heights):
        d.text((x, y - f.getbbox("Ag")[1]), t, font=f, fill=color + (255,) if len(color) == 3 else color)
        y += h + line_gap
    return img


def card_text(spec: dict) -> Image.Image:
    """Full-frame transparent layer with centred title text for title/outro cards."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = spec.get("y", 560)
    for item in spec["lines"]:
        f = font(item.get("font", "regular"), item["size"])
        color = tuple(item.get("color", TEXT))
        bbox = d.textbbox((0, 0), item["text"], font=f)
        x = (W - (bbox[2] - bbox[0])) // 2 - bbox[0]
        # Soft shadow for legibility on top of video.
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x + 3, y + 4 - bbox[1]), item["text"], font=f, fill=(0, 0, 0, 200))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(img)
        d.text((x, y - bbox[1]), item["text"], font=f, fill=color + (255,))
        y += (bbox[3] - bbox[1]) + item.get("gap", 24)
    return img


# --------------------------------------------------------------------------- timing

def rlen(r: dict) -> float:
    """Output length of a range (freeze ranges hold one frame for r['dur'] seconds)."""
    return r["dur"] if "freeze" in r else (r["out"] - r["in"]) / r["speed"]


def fit_ranges(ranges: list[dict], target: float) -> tuple[list[dict], float]:
    """Fit the picture to `target` seconds.

    Moving ranges share one speed factor (clamped to MIN_SPEED..MAX_SPEED). Freeze
    ranges keep their duration, but absorb any remaining shortfall or excess first
    (proportionally), so stills grow before anything gets slow-motion.
    Returns (ranges, hold) where hold is leftover time added as a frozen last frame.
    """
    moving = [r for r in ranges if "freeze" not in r]
    frozen = sum(r["dur"] for r in ranges if "freeze" in r)
    natural = sum((r["out"] - r["in"]) / r.get("speed", 1.0) for r in moving)
    avail = max(0.5, target - frozen)
    k = natural / avail if moving else 1.0
    out = []
    for r in ranges:
        if "freeze" in r:
            out.append(dict(r))
        else:
            s = min(MAX_SPEED, max(MIN_SPEED, r.get("speed", 1.0) * k))
            out.append({**r, "speed": s})
    length = sum(rlen(r) for r in out)
    gap = target - length
    if frozen > 0 and abs(gap) > 0.01:
        f = max(0.2, (frozen + gap) / frozen)
        for r in out:
            if "freeze" in r:
                r["dur"] = r["dur"] * f
        gap = target - sum(rlen(r) for r in out)
    return out, max(0.0, gap)


def src_to_out(ranges: list[dict], t: float) -> float | None:
    """Map a source timestamp to segment output time (None if cut away)."""
    acc = 0.0
    for r in ranges:
        if "freeze" in r:
            if abs(t - r["freeze"]) < 1e-6:
                return acc
        elif r["in"] <= t <= r["out"]:
            return acc + (t - r["in"]) / r["speed"]
        acc += rlen(r)
    return None


def window_out(ranges, a: float, b: float) -> tuple[float, float] | None:
    """Output-time window covering source window [a, b]; a freeze range whose frame
    lies in [a, b] contributes its whole held duration."""
    acc, lo, hi = 0.0, None, None
    for r in ranges:
        d = rlen(r)
        if "freeze" in r:
            if a <= r["freeze"] <= b:
                lo = acc if lo is None else lo
                hi = acc + d
        else:
            s0, s1 = max(a, r["in"]), min(b, r["out"])
            if s0 < s1:
                o0 = acc + (s0 - r["in"]) / r["speed"]
                o1 = acc + (s1 - r["in"]) / r["speed"]
                lo = o0 if lo is None else min(lo, o0)
                hi = o1 if hi is None else max(hi, o1)
        acc += d
    if lo is None or hi is None or hi - lo < 0.05:
        return None
    return lo, hi


# --------------------------------------------------------------------------- segments

def _view(x, y, w, h, scale, ox, oy, cw, ch, zmax):
    """Zoom and centre offset (relative to canvas centre) that frame a source rect."""
    X, Y, Wd, Hd = ox + x * scale, oy + y * scale, w * scale, h * scale
    z = max(1.0, min(cw / (Wd * 1.06), ch / (Hd * 1.06), zmax))
    return z, X + Wd / 2 - cw / 2, Y + Hd / 2 - ch / 2


def _smooth(u: str) -> str:
    return f"(({u})*({u})*(3-2*({u})))"


def zoom_exprs(zooms: list[dict], scale: float, ox: float, oy: float, cw: int, ch: int,
               path: list[dict] | None = None) -> tuple[str, str, str]:
    """zoompan z/x/y expressions.

    zooms: windows that ease in from the full view to a rect and back out.
    path:  keyframes [{t, x, y, w, h}] in output time: the camera glides from one
           rect to the next (smoothstep) and holds before the first/after the last.
    Rects are in source pixels; scale/ox/oy map them onto the zoompan canvas.
    """
    t = "(on/30)"
    if path:
        views = [_view(k["x"], k["y"], k["w"], k["h"], scale, ox, oy, cw, ch, k.get("max", 3.0)) for k in path]
        z0, cx0, cy0 = views[0]
        zs, cxs, cys = [f"{z0:.4f}"], [f"{cx0:.2f}"], [f"{cy0:.2f}"]
        for i in range(len(path) - 1):
            a, b = path[i]["t"], path[i + 1]["t"]
            e = _smooth(f"clip(({t}-{a:.3f})/{max(0.05, b - a):.3f},0,1)")
            (za, xa, ya), (zb, xb, yb) = views[i], views[i + 1]
            zs.append(f"{zb - za:.4f}*{e}")
            cxs.append(f"{xb - xa:.2f}*{e}")
            cys.append(f"{yb - ya:.2f}*{e}")
        zexpr = "max(1," + "+".join(zs) + ")"
        cx = f"({cw / 2:.2f}+" + "+".join(cxs) + ")"
        cy = f"({ch / 2:.2f}+" + "+".join(cys) + ")"
    else:
        zs, cxs, cys = [], [], []
        for zw in zooms:
            a, b, r = zw["t0"], zw["t1"], zw.get("ramp", 0.6)
            r = min(r, max(0.1, (b - a) / 2))
            e = _smooth(f"min(clip(({t}-{a:.3f})/{r:.3f},0,1),clip(({b:.3f}-{t})/{r:.3f},0,1))")
            z, dx, dy = _view(zw["x"], zw["y"], zw["w"], zw["h"], scale, ox, oy, cw, ch, zw.get("max", 2.6))
            zs.append(f"{z - 1:.4f}*{e}")
            cxs.append(f"{dx:.2f}*{e}")
            cys.append(f"{dy:.2f}*{e}")
        zexpr = "1+" + "+".join(zs) if zs else "1"
        cx = f"({cw / 2:.2f}+" + "+".join(cxs) + ")" if cxs else f"{cw / 2:.2f}"
        cy = f"({ch / 2:.2f}+" + "+".join(cys) + ")" if cys else f"{ch / 2:.2f}"
    xexpr = f"clip({cx}-iw/zoom/2,0,iw-iw/zoom)"
    yexpr = f"clip({cy}-ih/zoom/2,0,ih-ih/zoom)"
    return zexpr, xexpr, yexpr


def render_clip(seg: dict, cfg: dict, work: Path, target: float, out: Path) -> dict:
    src = cfg["sources"][seg["source"]]
    still = src.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    sw, sh = (Image.open(src).size if still else probe_size(src))
    crop = cfg.get("crops", {}).get(seg["source"])  # [x, y, w, h] trims pillarbox bars
    cx0, cy0 = (crop[0], crop[1]) if crop else (0, 0)
    if crop:
        sw, sh = crop[2], crop[3]
    if still:
        ranges, hold = [{"freeze": 0.0, "dur": target}], 0.0
    else:
        ranges, hold = fit_ranges(seg["ranges"], target)
    # Canvas for zoompan: 2x the screen size for smoother sub-pixel motion.
    cw, ch = SCREEN_W * 2, SCREEN_H * 2
    scale = min(cw / sw, ch / sh)
    ox, oy = (cw - sw * scale) / 2, (ch - sh * scale) / 2
    zooms = []
    for z in seg.get("zooms", []):
        win = window_out(ranges, z["src0"], z["src1"])
        if win:
            zooms.append({**z, "x": z["x"] - cx0, "y": z["y"] - cy0, "t0": win[0], "t1": win[1]})
    path = None
    if seg.get("path"):
        path = []
        for k in seg["path"]:
            if "frac" in k:
                tt = k["frac"] * target
            elif "at" in k:
                tt = k["at"]
            else:
                tt = src_to_out(ranges, k["src"]) or 0.0
            path.append({**k, "t": tt, "x": k["x"] - cx0, "y": k["y"] - cy0})
    zexpr, xexpr, yexpr = zoom_exprs(zooms, scale, ox, oy, cw, ch, path)

    src_in = ["-loop", "1", "-i", src] if still else ["-i", src]
    inputs = [*src_in, "-loop", "1", "-i", str(work / "bg.png"),
              "-loop", "1", "-i", str(work / "frame.png"), "-loop", "1", "-i", str(work / "cornermask.png")]
    pre = "[0:v]"
    if crop:
        pre += f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]},"
    pre += "setpts=PTS-STARTPTS"
    blurs = seg.get("blur", [])
    chain = f"{pre}[src0]"
    for i, b in enumerate(blurs):
        bx, by = int(b["x"] - cx0), int(b["y"] - cy0)
        chain += (f";[src{i}]split=2[bs{i}][bc{i}];[bc{i}]crop={int(b['w'])}:{int(b['h'])}:{bx}:{by},"
                  f"gblur=sigma=16:steps=3[bb{i}];[bs{i}][bb{i}]overlay={bx}:{by}:"
                  f"enable='between(t,{b['src0']:.3f},{b['src1']:.3f})'[src{i + 1}]")
    srcl = f"src{len(blurs)}"
    chain += f";[{srcl}]split={len(ranges)}" + "".join(f"[in{i}]" for i in range(len(ranges)))
    for i, r in enumerate(ranges):
        if "freeze" in r:
            n = max(1, int(round(r["dur"] * FPS)))
            if still:
                chain += f";[in{i}]fps={FPS},trim=end_frame=1,loop=loop={n - 1}:size=1:start=0,setpts=N/{FPS}/TB[r{i}]"
            else:
                chain += (f";[in{i}]trim=start={r['freeze']:.3f}:duration=0.2,setpts=PTS-STARTPTS,fps={FPS},"
                          f"trim=end_frame=1,loop=loop={n - 1}:size=1:start=0,setpts=N/{FPS}/TB[r{i}]")
        else:
            chain += (f";[in{i}]trim={r['in']:.3f}:{r['out']:.3f},setpts=(PTS-STARTPTS)/{r['speed']:.5f},"
                      f"fps={FPS}[r{i}]")
    joined = "".join(f"[r{i}]" for i in range(len(ranges)))
    chain += f";{joined}concat=n={len(ranges)}:v=1:a=0[cat]"
    pad_hold = f",tpad=stop_mode=clone:stop_duration={hold:.3f}" if hold > 0.01 else ""
    bgc = "0x%02x%02x%02x" % NAVY
    if seg.get("scroll"):
        # Tall screenshot: scale to a reading width, centre it, and glide vertically.
        iw = int(seg.get("width", 1100)) // 2 * 2
        k = iw / sw
        ih = int(round(sh * k / 2)) * 2  # even sizes for yuv420p
        keys = [{**k, "at": k["frac"] * target if "frac" in k else k["at"]} for k in seg["scroll"]]
        y0 = keys[0]["y"] * k
        terms = [f"{y0:.1f}"]
        for i in range(len(keys) - 1):
            a, b = keys[i]["at"], keys[i + 1]["at"]
            e = _smooth(f"clip((t-{a:.3f})/{max(0.05, b - a):.3f},0,1)")
            terms.append(f"{(keys[i + 1]['y'] - keys[i]['y']) * k:.1f}*{e}")
        yexp = f"clip({'+'.join(terms)},0,{max(0, ih - SCREEN_H)})"
        chain += (f";[cat]scale={iw}:{ih}:flags=lanczos,pad={SCREEN_W}:{max(ih, SCREEN_H)}:"
                  f"{(SCREEN_W - iw) // 2}:0:color={bgc},setsar=1,"
                  f"crop={SCREEN_W}:{SCREEN_H}:0:'{yexp}',fps={FPS}[scr]")
    elif not zooms and not path:
        k = min(SCREEN_W / sw, SCREEN_H / sh)
        chain += (f";[cat]scale={int(sw * k)}:{int(sh * k)}:flags=lanczos,"
                  f"pad={SCREEN_W}:{SCREEN_H}:(ow-iw)/2:(oh-ih)/2:color={bgc}{pad_hold},setsar=1[scr]")
    else:
        canvas = (f"scale={int(sw * scale)}:{int(sh * scale)}:flags=lanczos,"
                  f"pad={cw}:{ch}:{int(ox)}:{int(oy)}:color={bgc}")
        chain += (f";[cat]{canvas}{pad_hold},setsar=1,"
                  f"zoompan=z='{zexpr}':x='{xexpr}':y='{yexpr}':d=1:s={SCREEN_W}x{SCREEN_H}:fps={FPS}[scr]")
    # Screen over background, then mask the corners with background pixels, then border.
    chain += (f";[1:v]trim=duration={target:.3f},setpts=PTS-STARTPTS,fps={FPS}[bg]"
              f";[bg][scr]overlay={SCREEN_X}:{SCREEN_Y}:shortest=1[v0]"
              f";[1:v]trim=duration={target:.3f},setpts=PTS-STARTPTS,fps={FPS},format=rgba[bg2]"
              f";[3:v]trim=duration={target:.3f},setpts=PTS-STARTPTS,fps={FPS},format=gray[m]"
              f";[bg2][m]alphamerge[corners];[v0][corners]overlay=0:0[v1]"
              f";[2:v]trim=duration={target:.3f},setpts=PTS-STARTPTS,fps={FPS},format=rgba[fr];[v1][fr]overlay=0:0[v2]")
    last = "v2"
    n_in = 4
    for k, lab in enumerate(seg.get("labels", [])):
        img = text_box([(t, kind, size, tuple(col)) for t, kind, size, col in lab["lines"]])
        p = work / f"{seg['id']}_label{k}.png"
        img.save(p)
        if "src" in lab:
            t0 = src_to_out(ranges, lab["src"]) or 0.0
        else:
            t0 = lab.get("at", 0.0)
        t1 = min(target, t0 + lab.get("dur", 3.5))
        x = lab.get("x", SCREEN_X + 28)
        y = lab.get("y", SCREEN_Y + 24)
        if x == "right":
            x = SCREEN_X + SCREEN_W - img.width - 28
        inputs += ["-loop", "1", "-i", str(p)]
        chain += (f";[{n_in}:v]trim=duration={target:.3f},setpts=PTS-STARTPTS,fps={FPS},format=rgba,"
                  f"fade=t=in:st={t0:.3f}:d=0.35:alpha=1,fade=t=out:st={max(t0, t1 - 0.35):.3f}:d=0.35:alpha=1[l{k}]"
                  f";[{last}][l{k}]overlay={x}:{y}:enable='between(t,{t0:.3f},{t1:.3f})'[o{k}]")
        last = f"o{k}"
        n_in += 1
    chain += f";[{last}]trim=duration={target:.3f},format=yuv420p[out]"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", chain, "-map", "[out]",
         "-r", str(FPS), "-c:v", "libx264", "-preset", cfg.get("preset", "medium"), "-crf", "18",
         "-an", str(out)])
    return {"ranges": ranges, "hold": hold, "zooms": [(round(z["t0"], 2), round(z["t1"], 2)) for z in zooms]}


def render_card(seg: dict, cfg: dict, work: Path, target: float, out: Path) -> dict:
    bg = cfg["assets"].get(seg.get("background", ""), "")
    layer = card_text(seg["text"])
    lp = work / f"{seg['id']}_text.png"
    layer.save(lp)
    fade_in = seg.get("text_in", 0.8)
    inputs = []
    if bg.endswith((".mp4", ".mov", ".webm")) and os.path.exists(bg):
        bd = probe_duration(bg)
        slow = max(1.0, target / bd)
        inputs += ["-i", bg]
        base = (f"[0:v]setpts={slow:.4f}*PTS,fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},trim=duration={target:.3f},setpts=PTS-STARTPTS")
    elif bg and os.path.exists(bg):
        inputs += ["-loop", "1", "-i", bg]
        frames = int(target * FPS)
        base = (f"[0:v]scale=3840:-2,crop=3840:2160,zoompan=z='1+0.06*on/{frames}':x='iw/2-iw/zoom/2':"
                f"y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps={FPS},trim=duration={target:.3f}")
    else:
        inputs += ["-f", "lavfi", "-i", f"color=c=0x0b1020:s={W}x{H}:r={FPS}:d={target:.3f}"]
        base = "[0:v]null"
    dim = seg.get("dim", 0.35)
    chain = (f"{base},eq=brightness=-{dim * 0.25:.3f}:saturation=1.05[b];"
             f"[1:v]trim=duration={target:.3f},setpts=PTS-STARTPTS,fps={FPS},format=rgba,"
             f"fade=t=in:st={seg.get('text_at', 0.6):.2f}:d={fade_in:.2f}:alpha=1[t];"
             f"[b][t]overlay=0:0,fade=t=in:st=0:d={seg.get('fade_in', 0.6)},"
             f"fade=t=out:st={max(0, target - seg.get('fade_out', 0.6)):.3f}:d={seg.get('fade_out', 0.6)},"
             f"format=yuv420p[out]")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-loop", "1", "-i", str(lp), "-filter_complex", chain,
         "-map", "[out]", "-t", f"{target:.3f}", "-r", str(FPS), "-c:v", "libx264",
         "-preset", cfg.get("preset", "medium"), "-crf", "18", "-an", str(out)])
    return {}


# --------------------------------------------------------------------------- captions

def speech_bounds(path: str) -> tuple[float, float]:
    """Start/end of speech in a VO file (silencedetect, -40 dB)."""
    res = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=n=-40dB:d=0.15",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    dur = probe_duration(path)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", res)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", res)]
    s0 = ends[0] if starts and starts[0] < 0.05 and ends else 0.0
    s1 = starts[-1] if starts and (not ends or starts[-1] > ends[-1]) else dur
    return s0, s1


def whisper_words(path: str) -> list[tuple[str, float, float]] | None:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    global _WHISPER
    if "_WHISPER" not in globals():
        _WHISPER = WhisperModel(os.environ.get("WHISPER_MODEL", "small.en"), device="cpu", compute_type="int8")
    segs, _ = _WHISPER.transcribe(path, word_timestamps=True, beam_size=5)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def chunk_text(text: str, max_chars: int = 84) -> list[list[str]]:
    """Split authored text into caption chunks (<= 2 lines), breaking at punctuation."""
    words = text.split()
    chunks, cur = [], []
    for w in words:
        if cur and len(" ".join(cur + [w])) > max_chars:
            chunks.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[.!?]$", w) and len(" ".join(cur)) > 25:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def caption_events(text: str, vo_path: str, offset: float) -> list[tuple[float, float, str]]:
    chunks = chunk_text(text)
    words = [w for c in chunks for w in c]
    timed = whisper_words(vo_path)
    times: list[tuple[float, float]] = []
    if timed:
        # Sequentially align authored words to recognised words (fuzzy, by normalised prefix).
        j = 0
        for w in words:
            nw = norm(w)
            hit = None
            for k in range(j, min(j + 6, len(timed))):
                tw = norm(timed[k][0])
                if tw and nw and (tw == nw or tw.startswith(nw[:4]) or nw.startswith(tw[:4])):
                    hit = k
                    break
            if hit is not None:
                times.append((timed[hit][1], timed[hit][2]))
                j = hit + 1
            else:
                times.append((None, None))
        # Fill gaps by interpolation.
        known = [i for i, t in enumerate(times) if t[0] is not None]
        if not known:
            timed = None
        else:
            for i, t in enumerate(times):
                if t[0] is None:
                    prev = max([k for k in known if k < i], default=None)
                    nxt = min([k for k in known if k > i], default=None)
                    a = times[prev][1] if prev is not None else times[nxt][0]
                    b = times[nxt][0] if nxt is not None else times[prev][1]
                    times[i] = (a, b)
    if not timed:
        s0, s1 = speech_bounds(vo_path)
        total = sum(len(w) + 1 for w in words)
        acc = 0
        times = []
        for w in words:
            a = s0 + (s1 - s0) * acc / total
            acc += len(w) + 1
            times.append((a, s0 + (s1 - s0) * acc / total))
    events, i = [], 0
    for c in chunks:
        a = times[i][0]
        b = times[i + len(c) - 1][1]
        i += len(c)
        events.append((offset + a, offset + b + 0.15, " ".join(c)))
    # No overlaps; minimum 0.9 s on screen.
    for k in range(len(events) - 1):
        a, b, t = events[k]
        events[k] = (a, min(max(b, a + 0.9), events[k + 1][0] - 0.02), t)
    return events


def ass_time(t: float) -> str:
    t = max(0.0, t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap2(text: str, width: int = 46) -> str:
    if len(text) <= width:
        return text
    words, best = text.split(), None
    for k in range(1, len(text.split())):
        a, b = " ".join(words[:k]), " ".join(words[k:])
        score = max(len(a), len(b))
        if best is None or score < best[0]:
            best = (score, a, b)
    return best[1] + "\\N" + best[2]


def write_ass(events: list[tuple[float, float, str]], path: Path) -> None:
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{CAPTION_FONT},40,&H00F8ECE8,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2.2,0,2,140,140,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [head]
    for a, b, t in events:
        lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{wrap2(t)}\n")
    path.write_text("".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("--work", default="work")
    ap.add_argument("--only", default=None, help="render only this segment id (for checks)")
    ap.add_argument("--preset", default=None)
    ap.add_argument("--no-captions", action="store_true")
    ap.add_argument("--reuse", action="store_true",
                    help="keep segments already rendered with the same spec and duration")
    ap.add_argument("--segments-only", action="store_true", help="render segments, skip the final mix")
    args = ap.parse_args()

    cfg = json.loads(os.path.expandvars(Path(args.edl).read_text(encoding="utf-8")))
    if args.preset:
        cfg["preset"] = args.preset
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    make_background(work / "bg.png", cfg["assets"].get("backdrop"))
    make_frame_overlay(work / "frame.png")

    timeline, t = [], 0.0
    report = []
    for seg in cfg["segments"]:
        vo = cfg.get("vo", {}).get(seg["id"])
        vo_path = vo["file"] if vo and os.path.exists(vo["file"]) else None
        vo_dur = probe_duration(vo_path) if vo_path else 0.0
        target = max(seg.get("min", 2.0), vo_dur + VO_LEAD + VO_TAIL if vo_path else seg.get("dur", 4.0))
        target = round(target * FPS) / FPS
        out = work / f"{seg['id']}.mp4"
        sig = json.dumps({"seg": seg, "target": target, "src": cfg["sources"].get(seg.get("source", ""), ""),
                          "v": 2}, sort_keys=True)
        sigf = work / f"{seg['id']}.sig"
        fresh = out.exists() and sigf.exists() and sigf.read_text() == sig
        wanted = [x for x in (args.only or "").split(",") if x]
        if (wanted and seg["id"] not in wanted) or (args.reuse and fresh):
            timeline.append((seg, t, target, vo_path, vo))
            t += target
            continue
        print(f"[{seg['id']}] {seg['type']} {target:.2f}s (vo {vo_dur:.2f}s)", flush=True)
        info = (render_clip if seg["type"] == "clip" else render_card)(seg, cfg, work, target, out)
        sigf.write_text(sig)
        real = probe_duration(str(out))
        report.append({"id": seg["id"], "start": round(t, 2), "target": target, "real": round(real, 3),
                       "vo": round(vo_dur, 2), **{k: v for k, v in info.items() if k != "ranges"},
                       "speeds": [round(r["speed"], 2) if "speed" in r else f"freeze {r['dur']:.1f}s"
                                  for r in info.get("ranges", [])]})
        timeline.append((seg, t, target, vo_path, vo))
        t += target
    if args.only or args.segments_only:
        print(json.dumps(report, indent=1))
        return

    # Concatenate picture.
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{(work / (s['id'] + '.mp4')).resolve()}'\n" for s, *_ in timeline))
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
         str(work / "picture.mp4")])
    total = probe_duration(str(work / "picture.mp4"))

    # Voiceover track.
    inputs, mixes, k = [], [], 0
    for seg, start, target, vo_path, vo in timeline:
        if not vo_path:
            continue
        delay = int((start + VO_LEAD + vo.get("shift", 0.0)) * 1000)
        inputs += ["-i", vo_path]
        mixes.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={delay}|{delay}[a{k}]")
        k += 1
    chain = ";".join(mixes) + ";" + "".join(f"[a{i}]" for i in range(k)) + \
        f"amix=inputs={k}:normalize=0,apad,atrim=0:{total:.3f},loudnorm=I=-16:TP=-1.5:LRA=11[a]"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", chain, "-map", "[a]", "-ar", "48000",
         str(work / "voice.wav")])

    # Captions.
    events = []
    if not args.no_captions:
        for seg, start, target, vo_path, vo in timeline:
            if vo_path and vo.get("text"):
                events += caption_events(vo["text"], vo_path, start + VO_LEAD + vo.get("shift", 0.0))
    ass = work / "captions.ass"
    write_ass(events, ass)
    (work / "captions.srt").write_text("".join(
        f"{i + 1}\n{ass_time(a).replace('.', ',')}0 --> {ass_time(b).replace('.', ',')}0\n{t}\n\n"
        for i, (a, b, t) in enumerate(events)), encoding="utf-8")

    vf = f"subtitles={ass.resolve()}" if events else "null"
    final = Path(cfg.get("output", work / "final.mp4"))
    run(["ffmpeg", "-y", "-v", "error", "-i", str(work / "picture.mp4"), "-i", str(work / "voice.wav"),
         "-vf", vf, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", cfg.get("preset", "medium"),
         "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         "-shortest", str(final)])
    (work / "report.json").write_text(json.dumps({"total": total, "segments": report,
                                                  "captions": len(events)}, indent=1))
    print(json.dumps({"final": str(final), "duration": probe_duration(str(final)), "captions": len(events)}))


if __name__ == "__main__":
    main()

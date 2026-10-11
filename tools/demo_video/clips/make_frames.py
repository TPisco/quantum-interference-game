"""Keyframes (1920x1080 SVG) for the Higgsfield clips, drawn in the game's own style.

    python3 make_frames.py out_dir

Writes <name>_start.svg and <name>_end.svg for hook, arrows, kick and amp. Render
them to PNG with render_svg.mjs, upload them to Higgsfield, and pass them to
Kling 3.0 as start_image and end_image (prompts in docs/VIDEO_SCRIPT.md).
arrows_anim.py imports HEAD and dial() from here to draw the exact arrows clip.
"""

import math
import sys
from pathlib import Path

NAVY, BLUE, AMBER, CYAN, WHITE, LINE = "#0B1020", "#4EA8FF", "#FFB000", "#5CE1E6", "#E8ECF8", "#34406B"
HEAD = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
<defs>
<radialGradient id="bg" cx="50%" cy="38%" r="75%"><stop offset="0" stop-color="#141C3A"/><stop offset="1" stop-color="{NAVY}"/></radialGradient>
<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="halo" filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feGaussianBlur stdDeviation="22"/></filter>
</defs>
<rect width="1920" height="1080" fill="url(#bg)"/>
'''


def arrow(x1, y1, x2, y2, color, w=10, head=30, dash=None, opacity=1):
    L = math.hypot(x2 - x1, y2 - y1)
    if L < 1:
        return ""
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    bx, by = x2 - ux * head, y2 - uy * head
    px, py = -uy * head * 0.55, ux * head * 0.55
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<g filter="url(#glow)" opacity="{opacity}"><line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"{d}/>'
            f'<polygon points="{x2:.1f},{y2:.1f} {bx+px:.1f},{by+py:.1f} {bx-px:.1f},{by-py:.1f}" fill="{color}"/></g>')


# 1. Hook: the interferometer from the start page.
def hook(needle_deg, up, down):
    """up/down: brightness 0..1 of the upper (|0>) and lower (|1>) detectors."""
    s1, apex, low, s2 = (560, 330), (960, 150), (960, 510), (1360, 330)
    du, dd = (1650, 205), (1650, 455)
    dial = (760, 420)
    nx = dial[0] + 24 * math.cos(math.radians(needle_deg))
    ny = dial[1] - 24 * math.sin(math.radians(needle_deg))

    def det(c, b):
        core = WHITE if b > 0.75 else CYAN
        out = ""
        if b > 0.05:
            out += f'<circle cx="{c[0]}" cy="{c[1]}" r="{60 + 70*b:.0f}" fill="{CYAN}" opacity="{0.45*b:.2f}" filter="url(#halo)"/>'
        out += f'<circle cx="{c[0]}" cy="{c[1]}" r="40" fill="{core if b > 0.05 else NAVY}" fill-opacity="{max(b,0.0):.2f}" stroke="{CYAN if b > 0.05 else LINE}" stroke-width="5" filter="url(#glow)"/>'
        return out

    def exitline(c, b):
        col = CYAN if b > 0.05 else LINE
        return f'<line x1="{s2[0]}" y1="{s2[1]}" x2="{c[0]}" y2="{c[1]}" stroke="{col}" stroke-width="5" opacity="{0.35 + 0.65*b:.2f}" filter="url(#glow)"/>'

    return (f'<line x1="150" y1="330" x2="{s1[0]}" y2="{s1[1]}" stroke="{WHITE}" stroke-width="6" filter="url(#glow)"/>'
            f'<polyline points="{s1[0]},{s1[1]} {apex[0]},{apex[1]} {s2[0]},{s2[1]}" fill="none" stroke="{BLUE}" stroke-width="8" stroke-linejoin="round" filter="url(#glow)"/>'
            f'<polyline points="{s1[0]},{s1[1]} {low[0]},{low[1]} {s2[0]},{s2[1]}" fill="none" stroke="{AMBER}" stroke-width="8" stroke-dasharray="26 16" stroke-linejoin="round" filter="url(#glow)"/>'
            + exitline(du, up) + exitline(dd, down) +
            f'<circle cx="{dial[0]}" cy="{dial[1]}" r="36" fill="{NAVY}" stroke="{AMBER}" stroke-width="6" filter="url(#glow)"/>'
            f'<line x1="{dial[0]}" y1="{dial[1]}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{WHITE}" stroke-width="6" stroke-linecap="round"/>'
            f'<circle cx="{dial[0]}" cy="{dial[1]}" r="5" fill="{WHITE}"/>'
            f'<circle cx="{s1[0]}" cy="{s1[1]}" r="17" fill="{WHITE}" filter="url(#glow)"/>'
            f'<circle cx="{s2[0]}" cy="{s2[1]}" r="17" fill="{WHITE}" filter="url(#glow)"/>'
            + det(du, up) + det(dd, down))


# 2. Arrows: blue + orange added head to tail; the white sum is exact.
def dial(cx, cy, theta, kind):
    R, L = 250, 165
    body = (f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{LINE}" stroke-width="3" stroke-dasharray="6 10"/>'
            f'<line x1="{cx-R-15}" y1="{cy}" x2="{cx+R+15}" y2="{cy}" stroke="#1F2847" stroke-width="2"/>'
            f'<line x1="{cx}" y1="{cy-R-15}" x2="{cx}" y2="{cy+R+15}" stroke="#1F2847" stroke-width="2"/>')
    bx, by = cx + L, cy
    ox, oy = bx + L * math.cos(math.radians(theta)), by - L * math.sin(math.radians(theta))
    slen = math.hypot(ox - cx, oy - cy)
    if slen > 20:
        body += (f'<line x1="{cx}" y1="{cy}" x2="{ox:.1f}" y2="{oy:.1f}" stroke="{WHITE}" stroke-width="26" stroke-linecap="round" opacity="0.18"/>'
                 + arrow(cx, cy, ox, oy, WHITE, w=7, head=34))
    else:
        body += f'<circle cx="{cx}" cy="{cy}" r="16" fill="none" stroke="{WHITE}" stroke-width="6" filter="url(#glow)"/>'
    body += arrow(cx, cy, bx, by, BLUE, w=12, head=36)
    body += arrow(bx, by - 0, ox, oy, AMBER, w=12, head=36, dash="22 12")
    return body


# 3. Kickback emblem (the level's icon, enlarged).
def kick(lit):
    k, ox, oy = 6, 600, 60
    P = lambda x, y: (ox + k * x, oy + k * y)
    n1, n2, ap, lo = P(20, 46), P(100, 46), P(60, 18), P(60, 74)
    t1, t2, tl = P(14, 100), P(106, 100), P(60, 100)
    a = 0.25 + 0.75 * lit
    body = (f'<polyline points="{n1[0]},{n1[1]} {ap[0]},{ap[1]} {n2[0]},{n2[1]}" fill="none" stroke="{BLUE}" stroke-width="12" stroke-linejoin="round" filter="url(#glow)"/>'
            f'<polyline points="{n1[0]},{n1[1]} {lo[0]},{lo[1]} {n2[0]},{n2[1]}" fill="none" stroke="{AMBER}" stroke-width="{12 + 4*lit:.0f}" stroke-dasharray="34 20" stroke-linejoin="round" filter="url(#glow)"/>'
            f'<line x1="{t1[0]}" y1="{t1[1]}" x2="{t2[0]}" y2="{t2[1]}" stroke="{WHITE}" stroke-width="12" stroke-linecap="round" filter="url(#glow)"/>'
            f'<line x1="{lo[0]}" y1="{lo[1]}" x2="{tl[0]}" y2="{tl[1]}" stroke="{CYAN}" stroke-width="12" filter="url(#glow)"/>'
            f'<circle cx="{lo[0]}" cy="{lo[1]}" r="18" fill="{CYAN}" filter="url(#glow)"/>'
            f'<circle cx="{tl[0]}" cy="{tl[1]}" r="18" fill="{CYAN}" filter="url(#glow)"/>')
    c0, c1, c2, c3 = P(78, 98), P(92, 92), P(92, 78), P(80, 70)
    body += (f'<g opacity="{a:.2f}" filter="url(#glow)"><path d="M{c0[0]} {c0[1]} C {c1[0]} {c1[1]}, {c2[0]} {c2[1]}, {c3[0]} {c3[1]}" fill="none" stroke="{CYAN}" stroke-width="{9 + 5*lit:.0f}" stroke-linecap="round"/>'
             f'<polygon points="{c3[0]},{c3[1]} {c3[0]+54},{c3[1]+6} {c3[0]+18},{c3[1]+42}" fill="{CYAN}"/></g>')
    if lit:
        body += f'<circle cx="{n2[0]}" cy="{n2[1]}" r="110" fill="{CYAN}" opacity="0.55" filter="url(#halo)"/>'
    body += (f'<circle cx="{n1[0]}" cy="{n1[1]}" r="28" fill="{WHITE}" filter="url(#glow)"/>'
             f'<circle cx="{n2[0]}" cy="{n2[1]}" r="{28 + 10*lit:.0f}" fill="{WHITE}" filter="url(#glow)"/>')
    return body


# 4. Amplifier emblem: four bars at 25%, then the |11> bar alone.
def amp(end):
    base, w = 640, 110
    centers = [690, 870, 1050, 1230]
    hs = [12, 12, 12, 520] if end else [160, 160, 160, 160]
    body = f'<line x1="560" y1="{base}" x2="1360" y2="{base}" stroke="{WHITE}" stroke-opacity="0.55" stroke-width="5"/>'
    for i, (c, h) in enumerate(zip(centers, hs)):
        col = CYAN if (end and i == 3) else BLUE
        if end and i == 3:
            body += f'<rect x="{c-w/2-30}" y="{base-h-30}" width="{w+60}" height="{h+30}" rx="30" fill="{CYAN}" opacity="0.35" filter="url(#halo)"/>'
        body += f'<rect x="{c-w/2}" y="{base-h}" width="{w}" height="{h}" rx="16" fill="{col}" filter="url(#glow)"/>'
    body += f'<line x1="560" y1="470" x2="1360" y2="470" stroke="{AMBER}" stroke-width="8" stroke-dasharray="40 26" filter="url(#glow)"/>'
    my = 70 if end else 410
    body += f'<polygon points="1230,{my-26} 1256,{my} 1230,{my+26} 1204,{my}" fill="{AMBER}" filter="url(#glow)"/>'
    return body


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    frames = {
        "hook_start": hook(90, 0.5, 0.5), "hook_end": hook(180, 0.0, 1.0),
        "arrows_start": dial(620, 470, 90, "add") + dial(1300, 470, 90, "cancel"),
        "arrows_end": dial(620, 470, 0, "add") + dial(1300, 470, 180, "cancel"),
        "kick_start": kick(0), "kick_end": kick(1),
        "amp_start": amp(False), "amp_end": amp(True),
    }
    for name, body in frames.items():
        (out / f"{name}.svg").write_text(HEAD + body + "</svg>\n")
    print("ok", sorted(frames))

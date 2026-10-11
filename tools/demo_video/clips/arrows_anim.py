"""Frames for the exact "arrows add or cancel" clip (6 s, 30 fps).

    python3 arrows_anim.py out_dir

Same drawing as the arrows keyframes, but the white sum is always exactly blue +
orange added head to tail (Kling drew it wrong). Render with render_svg.mjs, then
    ffmpeg -framerate 30 -i png/f%04d.png -c:v libx264 -crf 16 -pix_fmt yuv420p arrows_exact_1080.mp4
"""

import sys
from pathlib import Path

from make_frames import HEAD, dial

FPS, DUR, A, B = 30, 6.0, 0.6, 4.4  # the arrows swing between A and B seconds


def ease(x):
    return 4 * x**3 if x < .5 else 1 - (-2 * x + 2)**3 / 2


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    n = int(FPS * DUR)
    for i in range(n):
        t = i / FPS
        k = 0 if t <= A else 1 if t >= B else ease((t - A) / (B - A))
        body = dial(620, 470, 90 - 90 * k, "add") + dial(1300, 470, 90 + 90 * k, "cancel")
        (out / f"f{i:04d}.svg").write_text(HEAD + body + "</svg>\n")
    print("frames", n)

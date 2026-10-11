"""Paint an exact phase needle over the Kling hook clip, then upscale it to 1080p.

    python3 fix_hook.py hook.mp4 hook_fixed_1080.mp4

Kling animates the detectors well but its needle wanders. This covers the dial's
face with a clean needle that eases from 90 to 180 degrees between 5.0 and 7.4 s,
when the detectors swap, and scales 1280x720 to 1920x1080 (lanczos + light sharpen).
Needs ffmpeg, numpy and Pillow.
"""

import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

W, H, FPS = 1280, 720, 24
CX, CY, R_IN = 506.8, 279.6, 21.6  # dial centre and inner radius in the Kling frame
S, P = 8, 56  # supersampling factor, patch size


def ease(x):
    return 4 * x**3 if x < .5 else 1 - (-2 * x + 2)**3 / 2


def angle(t, a=5.0, b=7.4):
    if t <= a:
        return 90.0
    if t >= b:
        return 180.0
    return 90 + 90 * ease((t - a) / (b - a))


def main():
    src, dst = sys.argv[1], sys.argv[2]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    n = len(raw) // (W * H * 3)
    frames = np.frombuffer(raw, np.uint8).reshape(n, H, W, 3)
    face = frames[0, int(CY) - 3:int(CY) + 4, int(CX) + 12:int(CX) + 17].reshape(-1, 3)
    fill = tuple(int(v) for v in np.median(face, axis=0))
    mask_big = Image.new("L", (P * S, P * S), 0)
    ImageDraw.Draw(mask_big).ellipse([(P / 2 - R_IN) * S, (P / 2 - R_IN) * S,
                                      (P / 2 + R_IN) * S, (P / 2 + R_IN) * S], fill=255)
    mask = mask_big.resize((P, P), Image.LANCZOS)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-vf", "scale=1920:1080:flags=lanczos,unsharp=5:5:0.4",
                            "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", dst],
                           stdin=subprocess.PIPE)
    ink = (232, 236, 248)
    for i in range(n):
        img = Image.fromarray(frames[i].copy())
        big = Image.new("RGB", (P * S, P * S), fill)
        d = ImageDraw.Draw(big)
        c, L, th = P * S / 2, 16 * S, math.radians(angle(i / FPS))
        x2, y2 = c + L * math.cos(th), c - L * math.sin(th)
        d.line([c, c, x2, y2], fill=ink, width=4 * S)
        d.ellipse([x2 - 2 * S, y2 - 2 * S, x2 + 2 * S, y2 + 2 * S], fill=ink)
        d.ellipse([c - 3.3 * S, c - 3.3 * S, c + 3.3 * S, c + 3.3 * S], fill=ink)
        img.paste(big.resize((P, P), Image.LANCZOS), (round(CX - P / 2), round(CY - P / 2)), mask)
        enc.stdin.write(img.tobytes())
    enc.stdin.close()
    enc.wait()
    print("frames", n, "dial fill", fill)


if __name__ == "__main__":
    main()

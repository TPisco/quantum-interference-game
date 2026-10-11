"""Cut the second-cut screen recordings to the finished voice track (run in the Higgsfield sandbox).

    python3 edit_v2.py [x264 preset] [only,these,ids]

Expects, under ROOT: rec/u*.mp4 (the recordings), clips/*_1080.mp4 (the four
Higgsfield clips), outro_bg_1080.png, clean_v3/sNN.wav (cleaned voice lines) and
script_sb3.json (line order). Writes one MP4 per line to edit/seg/ and edit/list.txt.
Then:
    ffmpeg -f concat -safe 0 -i list.txt -c copy video.mp4
    ffmpeg -i video.mp4 -i phase_shift_vo_v3.wav -vf "subtitles=captions_v3.srt:force_style='..."
           -c:v libx264 -crf 20 -c:a aac -b:a 192k -shortest phase_shift_demo.mp4

Each line's picture runs from 0.2 s before its voice starts to 0.2 s before the next
line. A piece maps voice time to recording time through anchor pairs
[seconds into the line, seconds into the recording] ("S" and "E" are the picture's
start and end), so each stretch between anchors is sped up or slowed down to land
its click on the right word. Recordings sit in a framed 1600x900 screen with a
section label below; the Higgsfield clips play full frame.
"""
import json, subprocess, sys, os
ROOT = os.path.expanduser("~/ps/v2"); REC = f"{ROOT}/rec"; CL = f"{ROOT}/clips"; OUT = f"{ROOT}/edit/seg"
os.makedirs(OUT, exist_ok=True)
PRESET = sys.argv[1] if len(sys.argv) > 1 else "veryfast"
ONLY = sys.argv[2].split(",") if len(sys.argv) > 2 else None
GAP, LEAD, TAIL = 0.4, 0.8, 2.0
FB = "/usr/share/fonts/truetype/higgsfield/Metropolis-ExtraBold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
NAVY = "0x0B1020"
dur = lambda f: float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f], text=True))
ids = [s["id"] for s in json.load(open(f"{ROOT}/script_sb3.json"))["segments"]]
start, t = {}, LEAD
for i in ids:
    start[i] = t; t += dur(f"{ROOT}/clean_v3/{i}.wav") + GAP
TOTAL = t - GAP + TAIL
V = {i: (0.0 if k == 0 else start[i] - 0.2) for k, i in enumerate(ids)}
VEND = {i: (V[ids[k+1]] if k + 1 < len(ids) else TOTAL) for k, i in enumerate(ids)}
# u01 start, u15 level 1, u08 levels 2-3, u09 kickback, u10 amplifier, u03 Run on QPU + tail,
# u12 phone, u13 keyboard, u14 code
SRC = {"u01": f"{REC}/u01.mp4", "u03": f"{REC}/u03.mp4", "u08": f"{REC}/u08.mp4", "u09": f"{REC}/u09.mp4",
       "u10": f"{REC}/u10.mp4", "u12": f"{REC}/u12.mp4", "u13": f"{REC}/u13.mp4", "u14": f"{REC}/u14.mp4",
       "u15": f"{REC}/u15.mp4", "hook": f"{CL}/hook_fixed_1080.mp4", "arrows": f"{CL}/arrows_exact_1080.mp4",
       "kick": f"{CL}/kick_1080.mp4", "amp": f"{CL}/amp_1080.mp4"}
BLUR = {"u01": [(1700, 0, 220, 70), (10, 60, 170, 80)]}  # Qollab account name and avatar
DEMO = (830, 140, 860, 484)      # start-page demo card (zoom)
DIALOG = (450, 300, 1020, 574)   # Select QPU dialog, IonQ simulators in view (zoom)
KEYS = (60, 420, 1000, 562)      # left column controls, focus ring (zoom)
CODE = (40, 30, 1280, 720)       # editor (zoom)
L = lambda k, t: (k, t)
PLAN = {
 "s01": {"full": True, "title": ("Phase Shift", "A quantum interference puzzle  ·  Qollab × IonQ"), "pieces": [{"src": "hook", "anchors": [["S", 1.0]], "speed": 1.0}]},
 "s02": {"label": L("RUNS ON QOLLAB", "Qiskit in your browser"), "pieces": [{"src": "u01", "anchors": [["S", 0.0], [1.6, 0.9], [3.4, 2.7], ["E", 8.0]]}]},
 "s03a": {"label": L("RUNS ON QOLLAB", "Qiskit in your browser"), "pieces": [{"src": "u01", "anchors": [["S", 8.0], ["E", 9.6]]}]},
 "s03b": {"full": True, "pieces": [{"src": "arrows", "anchors": [["S", 0.0]], "speed": 1.0}]},
 "s03c": {"label": L("THE ONE RULE", "Arrows add or cancel"), "pieces": [{"src": "u01", "anchors": [["S", 11.0], ["E", 13.4]], "crop": DEMO}]},
 "s04": {"label": L("LEVEL 1", "Invisible Ink"), "pieces": [{"src": "u15", "anchors": [["S", 0.0], [1.2, 5.6], [8.8, 9.8], [9.6, 10.8], [11.0, 11.6], [12.6, 13.4], [14.6, 16.4], [15.4, 17.2], ["E", 18.0]]}]},
 "s05": {"label": L("LEVEL 1", "Invisible Ink"), "pieces": [{"src": "u15", "anchors": [["S", 21.0], [2.0, 22.3], [4.6, 24.6], [5.6, 25.3], [7.3, 26.0], [9.0, 28.0], ["E", 29.9]]}]},
 "s06": {"label": L("LEVELS 2 AND 3", "Dark Port, Which-Path Eraser"), "pieces": [{"src": "u08", "anchors": [["S", 0.8], [0.2, 1.4], [5.0, 7.9], ["E", 20.4]]}]},
 "s07a": {"full": True, "title": ("New: Level 4", "Kickback"), "pieces": [{"src": "kick", "anchors": [["S", 0.0]], "speed": 1.6}]},
 "s07b": {"label": L("NEW · LEVEL 4", "Kickback"), "pieces": [{"src": "u09", "anchors": [["S", 1.4], [0.5, 5.5], [3.7, 9.8], [4.6, 10.6], [5.6, 11.4], [7.0, 13.6], [8.4, 14.6], [9.6, 15.6], [11.0, 17.0], ["E", 24.5]]}]},
 "s08a": {"full": True, "title": ("New: Level 5", "Amplifier"), "pieces": [{"src": "amp", "anchors": [["S", 0.0]], "speed": 1.0}]},
 "s08b": {"label": L("NEW · LEVEL 5", "Amplifier (Grover search)"), "pieces": [{"src": "u10", "anchors": [["S", 1.5], [2.3, 8.6], [3.9, 12.2], [5.2, 13.6], [7.4, 14.8], [8.3, 16.0], [11.0, 17.6], [12.3, 18.4], [14.0, 21.5], ["E", 25.0]]}]},
 "s09a": {"label": L("RUN ON QPU", "one job per Run"), "pieces": [{"src": "u03", "anchors": [["S", 0.0], ["E", 3.0]]}]},
 "s09b": {"label": L("RUN ON QPU", "IonQ's simulator earns the IonQ star"), "pieces": [
     {"src": "u03", "anchors": [["S", 3.0], [2.6, 4.6]]},
     {"src": "u01", "anchors": [[2.6, 1.05], ["E", 2.55]], "crop": DIALOG}]},
 "s10": {"label": L("ACCESSIBLE", "phone, keyboard, screen reader"), "pieces": [
     {"src": "u12", "anchors": [["S", 8.0], [2.7, 13.0]], "phone": True},
     {"src": "u13", "anchors": [[2.7, 2.6], ["E", 8.05]], "crop": KEYS}]},
 "s11": {"label": L("OPEN SOURCE", "MIT · Qiskit · 207 tests"), "pieces": [
     {"src": "u14", "anchors": [["S", 0.0], [7.5, 6.5]], "crop": CODE},
     {"src": "u14", "anchors": [[7.5, 7.5], [12.9, 16.9]], "crop": CODE},
     {"src": "u03", "anchors": [[12.9, 9.4], ["E", 12.8]]}]},
 "s12": {"outro": True},
}
W, H, SX, SY, SW, SH = 1920, 1080, 160, 20, 1600, 900


def esc(s):
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def render(sid):
    p = PLAN[sid]; d = VEND[sid] - V[sid]; rel0 = V[sid] - start[sid]; rel1 = rel0 + d
    out = f"{OUT}/{sid}.mp4"; inputs, chains, labels = [], [], []
    if p.get("outro"):
        txt = [("Phase Shift", FB, 120, 560), ("Five puzzles, one rule: follow the arrows.", FB, 44, 690),
               ("Play it on Qollab  ·  github.com/TPisco/quantum-interference-game", FR, 34, 770),
               ("MIT licensed  ·  This effort is supported by Qollab & IonQ", FR, 28, 830)]
        dt = ",".join(f"drawtext=fontfile={f}:text='{esc(s)}':x=(w-text_w)/2:y={y}:fontsize={z}:fontcolor=white:alpha='min(1,max(0,(t-{0.3+0.25*k})/0.5))'" for k, (s, f, z, y) in enumerate(txt))
        cmd = ["ffmpeg","-y","-v","error","-loop","1","-framerate","30","-i",f"{ROOT}/outro_bg_1080.png","-vf",f"scale={W}:{H},{dt},format=yuv420p","-t",f"{d:.3f}","-r","30","-c:v","libx264","-preset",PRESET,"-crf","18",out]
        subprocess.run(cmd, check=True); return out
    full = p.get("full"); tw, th = (W, H) if full else (SW, SH)
    for k, pc in enumerate(p["pieces"]):
        an = [list(a) for a in pc["anchors"]]
        if an[0][0] == "S": an[0][0] = rel0
        if "speed" in pc:
            an = [[rel0, an[0][1]], [rel1, an[0][1] + (rel1 - rel0) * pc["speed"]]]
        if an[-1][0] == "E": an[-1][0] = rel1
        sd = dur(SRC[pc["src"]])
        inputs += ["-i", SRC[pc["src"]]]
        parts = []
        for j in range(len(an) - 1):
            (t0, s0), (t1, s1) = an[j], an[j + 1]
            s1c = min(s1, sd - 0.05); s0c = min(s0, s1c - 0.04)
            out_d = t1 - t0
            if out_d <= 0.01: continue
            parts.append((s0c, s1c, out_d / max(0.04, s1c - s0c), out_d))
        post = []
        if pc.get("crop"):
            x, y, w, h = pc["crop"]; post.append(f"crop={w}:{h}:{x}:{y}")
        if pc.get("phone"):
            post.append(f"scale=-2:{th-40},pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:color={NAVY}")
        else:
            post.append(f"scale={tw}:{th}:flags=lanczos")
        for j, (s0, s1, f, od) in enumerate(parts):
            chain = f"[{k}:v]trim=start={s0:.3f}:end={s1:.3f},setpts=(PTS-STARTPTS)*{f:.5f},fps=30,setsar=1"
            for q, (x, y, w, h) in enumerate(BLUR.get(pc["src"], [])):
                n = f"{k}_{j}_{q}"
                chain += f",split[a{n}][b{n}];[b{n}]crop={w}:{h}:{x}:{y},boxblur=12:3[bb{n}];[a{n}][bb{n}]overlay={x}:{y}"
            chain += "," + ",".join(post) + f",setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration=1,trim=duration={od:.3f}[p{k}_{j}]"
            chains.append(chain); labels.append(f"[p{k}_{j}]")
    chains.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0,tpad=stop_mode=clone:stop_duration=5,trim=duration={d:.3f},setpts=PTS-STARTPTS[vid]")
    if full and p.get("title"):
        a, b = p["title"]
        big = 132 if sid == "s01" else 96
        chains.append(f"[vid]drawtext=fontfile={FB}:text='{esc(a)}':x=(w-text_w)/2:y=h-330:fontsize={big}:fontcolor=white:alpha='min(1,max(0,(t-0.6)/0.5))':shadowcolor=black@0.6:shadowx=0:shadowy=4,"
                      f"drawtext=fontfile={FB}:text='{esc(b)}':x=(w-text_w)/2:y=h-330+{big+16}:fontsize={int(big*0.36)}:fontcolor=0x5CE1E6:alpha='min(1,max(0,(t-0.9)/0.5))'[v]")
    elif full:
        chains.append("[vid]null[v]")
    else:
        chains.append(f"color=c={NAVY}:s={W}x{H}:r=30:d={d:.3f}[bg];[bg][vid]overlay={SX}:{SY},drawbox=x={SX-2}:y={SY-2}:w={SW+4}:h={SH+4}:color=0x34406B:t=2[c]")
        k_, t_ = p["label"]
        chains.append(f"[c]drawtext=fontfile={FB}:text='{esc(k_)}':x=60:y={SY+SH+38}:fontsize=22:fontcolor=0x5CE1E6,drawtext=fontfile={FB}:text='{esc(t_)}':x=60:y={SY+SH+70}:fontsize=30:fontcolor=white[v]")
    cmd = ["ffmpeg","-y","-v","error",*inputs,"-filter_complex",";".join(chains),"-map","[v]","-an","-r","30","-c:v","libx264","-preset",PRESET,"-crf","18","-pix_fmt","yuv420p",out]
    subprocess.run(cmd, check=True)
    return out


if __name__ == "__main__":
    for sid in ONLY or ids:
        o = render(sid); print(sid, f"{V[sid]:.2f}-{VEND[sid]:.2f}", f"{dur(o):.2f}s", flush=True)
    if not ONLY:
        with open(f"{ROOT}/edit/list.txt", "w") as fh:
            for sid in ids: fh.write(f"file '{OUT}/{sid}.mp4'\n")
        print("TOTAL", TOTAL)

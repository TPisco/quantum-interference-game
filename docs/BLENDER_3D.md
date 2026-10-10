# Optional 3D assets (Blender / Blender MCP)

## Do we need 3D?

**For the game: no.** The puzzle is about arrows and probabilities, which read best in flat 2D. A WebGL scene would add a large library and slow the first load in Qollab's in-browser Python runtime, and it adds nothing to the physics. The web UI therefore stays 2D (inline SVG, about 60 KiB of JS and CSS in total).

**For the demo video: yes, one short clip is worth it.** A 5-second 3D interferometer, in which the phase ring turns and one detector fades while the other lights up, is a memorable establishing shot. It shows the whole idea of level 1 before the screen recording starts. It costs nothing at runtime because it only lives in the video.

## The asset

`tools/blender_interferometer.py` builds the scene procedurally (no downloaded models):

* a cyan beam splitter (H) at each end of a diamond;
* the **upper path** as a solid blue tube and the **lower path** as an orange dashed tube, the same colours and line styles as the game;
* a **phase ring** (a flat torus with a bright notch) on the lower path, rotating from 0° to 180° between frames 20 and 110;
* two **detectors** |0⟩ and |1⟩ whose brightness is keyframed with the game's own formula, P(|1⟩) = sin²(φ/2);
* a top-down camera, 1920×1080, 30 fps, 150 frames; the game's hex colours converted to Blender's linear colour space, with the "Standard" view transform so the colours match exactly.

It was run headlessly with Blender's Python module (`bpy` 5.2.2): the scene builds, renders (Cycles, CPU) and exports to GLB (about 260 KiB).

## Using it

**In Blender (4.2 or newer):** open the *Scripting* workspace, open `tools/blender_interferometer.py`, press *Run Script*. Then render: *Render → Render Animation*.

**From the command line:**

```bash
blender -b -P tools/blender_interferometer.py -- --still docs/screenshots/interferometer.png --frame 110
blender -b -P tools/blender_interferometer.py -- --video renders/interferometer_ --frames 150
blender -b -P tools/blender_interferometer.py -- --glb assets/interferometer.glb
```

`--video` writes a PNG sequence; turn it into an MP4 with
`ffmpeg -framerate 30 -i renders/interferometer_%04d.png -c:v libx264 -pix_fmt yuv420p assets/video/interferometer.mp4`.

**Through Blender MCP** (for example the open-source `blender-mcp` add-on and server, connected to a running Blender):

1. Ask the assistant to call the MCP's scene-info tool (`get_scene_info`) to confirm the connection.
2. Ask it to call the code-execution tool (`execute_blender_code`) with the full contents of `tools/blender_interferometer.py`. With no command-line flags, the script builds the scene in the open file and does not render.
3. Ask for a viewport check (`get_viewport_screenshot`), then adjust: for example, "make the phase ring thicker", "move the camera to a 30° tilt", "slow the rotation to frames 20–140".
4. Render from Blender (or ask the MCP to run `bpy.ops.render.render(animation=True)` after setting `scene.render.filepath`).

Blender MCP was not connected in the session that produced this project, which is why the scene is a plain script: it works the same with or without the MCP.

## Where it goes in the video

* **0:00–0:12 (alternative opener):** use the 3D interferometer instead of, or cut together with, the Higgsfield ripple clip. The VO line "possibilities that add up, or cancel out" lands on the detector switching.
* **0:57 (arrows explanation):** a 2-second insert of frames 20 → 110 next to the arrows panel ties "the phase turns" to "the detector goes dark".

## Keeping it lightweight

* Nothing 3D is uploaded to Qollab: `tools/` is excluded by `tools/package_qollab.py`.
* If you ever want a 3D badge in the UI, export the GLB from frame 1, decimate it below 100 KiB, and show it with `<model-viewer>` only after the game has loaded (never in the critical path), with a static image fallback and `prefers-reduced-motion` respected.

## Alternative without Blender: Higgsfield 3D

Higgsfield can turn an image into a GLB mesh (`generate_3d`), for example the level 2 illustration (`level2_dark_port.png`, job `77b5db44-1e73-4071-9cf1-d41e3bf134ff`). The result is a sculpted mesh rather than an exact interferometer, so the Blender script is the better choice when the physics must be accurate.

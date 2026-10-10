"""Build the Phase Shift interferometer as a small animated 3D scene in Blender.

Optional asset for the demo video (the game itself stays 2D and lightweight).

Run it in any of three ways:

  * Blender UI:   Scripting tab -> open this file -> Run Script.
  * Command line: blender -b -P tools/blender_interferometer.py -- --still out.png
                  blender -b -P tools/blender_interferometer.py -- --video out_dir/ [--frames 150]
                  blender -b -P tools/blender_interferometer.py -- --glb orb.glb
  * Blender MCP:  send this file's contents with the MCP's code-execution tool
                  (for example ``execute_blender_code``); it builds the scene in the open file.

Scene (5 s at 30 fps): a qubit splits at a beam splitter into a blue upper path
and an orange, dashed-looking lower path; a phase ring on the lower path turns
from 0 to 180 degrees; at the second beam splitter detector |0> fades to dark
while detector |1> lights up, which is level 1 of the game in 3D.
"""

from __future__ import annotations

import math
import sys

import bpy

def hex_to_linear(hex_colour: str) -> tuple[float, float, float, float]:
    """The game's sRGB hex colours as the linear RGBA values Blender's nodes expect."""
    out = []
    for i in (1, 3, 5):
        c = int(hex_colour[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


NAVY = hex_to_linear("#0b1020")
BLUE = hex_to_linear("#4ea8ff")
AMBER = hex_to_linear("#ffb000")
CYAN = hex_to_linear("#5ce1e6")
WHITE = hex_to_linear("#e8ecf8")
FRAMES = 150


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def emission_material(name: str, color, strength: float = 3.0, alpha: float = 1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1.0)  # colour comes from emission only
    bsdf.inputs["Emission Color"].default_value = color
    bsdf.inputs["Emission Strength"].default_value = strength
    bsdf.inputs["Roughness"].default_value = 0.35
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
    return mat


def tube(name: str, points, material, radius: float = 0.06):
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 6
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, (x, y, z) in zip(spline.points, points):
        p.co = (x, y, z, 1.0)
    obj = bpy.data.objects.new(name, curve)
    obj.data.materials.append(material)
    bpy.context.collection.objects.link(obj)
    return obj


def beam_splitter(name: str, x: float, material):
    bpy.ops.mesh.primitive_cube_add(size=0.6, location=(x, 0, 0), rotation=(0, 0, math.radians(45)))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def sphere(name: str, location, radius: float, material):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=48, ring_count=24)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def key_emission(material, frame: int, strength: float) -> None:
    socket = material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    socket.default_value = strength
    socket.keyframe_insert("default_value", frame=frame)


def build() -> None:
    clear_scene()
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, FRAMES
    scene.render.fps = 30
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.view_settings.view_transform = "Standard"  # keep the game's exact colours

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = NAVY
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

    m_split = emission_material("BeamSplitter", CYAN, 0.8, alpha=0.85)
    m_upper = emission_material("UpperPath", BLUE, 1.0)
    m_lower = emission_material("LowerPath", AMBER, 1.0)
    m_input = emission_material("InputBeam", WHITE, 0.9)
    m_det0 = emission_material("Detector0", WHITE, 1.4)
    m_det1 = emission_material("Detector1", WHITE, 0.0)
    m_orb = emission_material("QubitOrb", CYAN, 1.2)

    beam_splitter("Split_H", -2.0, m_split)
    beam_splitter("Recombine_H", 2.0, m_split)
    tube("InputBeam", [(-5.0, 0, 0), (-2.0, 0, 0)], m_input, 0.05)
    tube("UpperPath", [(-2.0, 0, 0), (0, 1.6, 0), (2.0, 0, 0)], m_upper)
    # The lower path is drawn as short segments so it reads as "dashed" like in the game.
    for i in range(6):
        t0, t1 = i / 6, (i + 0.6) / 6
        a = (-2.0 + 2.0 * t0 * 2, -1.6 * (1 - abs(2 * t0 - 1)), 0)
        b = (-2.0 + 2.0 * t1 * 2, -1.6 * (1 - abs(2 * t1 - 1)), 0)
        tube(f"LowerPath_{i}", [a, b], m_lower)
    tube("Out0", [(2.0, 0, 0), (4.2, 1.2, 0)], m_input, 0.03)
    tube("Out1", [(2.0, 0, 0), (4.2, -1.2, 0)], m_input, 0.03)

    det0 = sphere("Detector_0", (4.4, 1.3, 0), 0.32, m_det0)
    det1 = sphere("Detector_1", (4.4, -1.3, 0), 0.32, m_det1)
    sphere("QubitOrb", (-5.0, 0, 0), 0.22, m_orb)
    det0["label"], det1["label"] = "|0>", "|1>"

    # Phase ring on the lower path: rotates 0 -> 180 degrees over the clip.
    # The ring lies flat (facing the top-down camera) like the game's phase dial; a bright
    # notch on its rim shows the angle.
    bpy.ops.mesh.primitive_torus_add(location=(0, -1.6, 0), major_radius=0.42, minor_radius=0.07)
    ring = bpy.context.active_object
    ring.name = "PhaseRing"
    ring.data.materials.append(emission_material("PhaseRing", AMBER, 1.0))
    bpy.ops.mesh.primitive_cube_add(size=0.14, location=(0.42, -1.6, 0.0))
    notch = bpy.context.active_object
    notch.name = "PhaseNotch"
    notch.data.materials.append(m_orb)
    bpy.context.view_layer.update()
    notch.parent = ring
    notch.matrix_parent_inverse = ring.matrix_world.inverted()
    ring.rotation_euler[2] = 0.0
    ring.keyframe_insert("rotation_euler", index=2, frame=20)
    ring.rotation_euler[2] = math.radians(180)
    ring.keyframe_insert("rotation_euler", index=2, frame=110)

    # Detector brightness follows the game's formula: P(1) = sin^2(phi/2).
    for frame in range(20, 111, 10):
        phi = math.pi * (frame - 20) / 90
        p1 = math.sin(phi / 2) ** 2
        key_emission(m_det0, frame, 1.4 * (1 - p1))
        key_emission(m_det1, frame, 1.4 * p1)

    bpy.ops.object.light_add(type="AREA", location=(0, 0, 6))
    bpy.context.active_object.data.energy = 40
    bpy.ops.object.camera_add(location=(0.0, -0.4, 9.5), rotation=(0, 0, 0))
    cam = bpy.context.active_object
    cam.data.lens = 32
    scene.camera = cam


def set_engine(scene, fast: bool) -> None:
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    if fast or scene.render.engine == "CYCLES":
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 16
        scene.cycles.device = "CPU"


def main(argv: list[str]) -> None:
    build()
    scene = bpy.context.scene
    if "--still" in argv:
        set_engine(scene, fast=True)
        scene.frame_set(int(argv[argv.index("--frame") + 1]) if "--frame" in argv else 110)
        scene.render.filepath = argv[argv.index("--still") + 1]
        bpy.ops.render.render(write_still=True)
    if "--video" in argv:
        set_engine(scene, fast=False)
        if "--frames" in argv:
            scene.frame_end = int(argv[argv.index("--frames") + 1])
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = argv[argv.index("--video") + 1]
        bpy.ops.render.render(animation=True)
    if "--glb" in argv:
        bpy.ops.export_scene.gltf(filepath=argv[argv.index("--glb") + 1], export_format="GLB")


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

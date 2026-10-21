"""Trusted Blender script: an original animated system-flow scene, no external assets."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def create(spec):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = spec["width"]
    scene.render.resolution_y = spec["height"]
    scene.render.resolution_percentage = 100
    scene.render.fps = spec["fps"]
    scene.frame_start = 1
    scene.frame_end = spec["frames"]
    scene.world.color = (0.025, 0.035, 0.055)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(Path(spec["output"]) / "frame-")
    scene.render.film_transparent = spec["transparent"]
    scene.view_settings.view_transform = "Standard"

    def material(name, color, metal=0):
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*color, 1)
        mat.use_nodes = True
        principled = mat.node_tree.nodes.get("Principled BSDF")
        principled.inputs["Base Color"].default_value = (*color, 1)
        principled.inputs["Metallic"].default_value = metal
        principled.inputs["Roughness"].default_value = 0.3
        return mat

    panel = material("Graphite ceramic", (0.055, 0.09, 0.14), 0.35)
    accent = material("Signal lime", (0.55, 0.85, 0.15), 0.2)
    white = material("Label white", (0.9, 0.93, 0.95))
    ground = material("Ground", (0.012, 0.02, 0.035))
    nodes = spec["labels"]
    points = []
    for i, label in enumerate(nodes):
        x = (i - (len(nodes) - 1) / 2) * 3.4
        points.append((x, 0, 0.7))
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 0.5))
        obj = bpy.context.object
        obj.name = "Component-" + str(i)
        obj.scale = (2.6, 1.8, 0.7)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        modifier = obj.modifiers.new("Soft machined edges", "BEVEL")
        modifier.width = 0.16
        modifier.segments = 4
        obj.data.materials.append(panel)
        bpy.ops.object.text_add(location=(x, -0.91, 1.05), rotation=(math.pi / 2, 0, 0))
        text = bpy.context.object
        text.name = "Label-" + str(i)
        text.data.body = label
        text.data.align_x = "CENTER"
        text.data.size = 0.3
        text.data.extrude = 0.008
        text.data.materials.append(white)
    for i, (a, b) in enumerate(zip(points, points[1:])):
        curve = bpy.data.curves.new("Signal path", "CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth = 0.035
        curve.bevel_resolution = 4
        spline = curve.splines.new("POLY")
        spline.points.add(1)
        spline.points[0].co = (*a, 1)
        spline.points[1].co = (*b, 1)
        edge = bpy.data.objects.new("Link-" + str(i), curve)
        scene.collection.objects.link(edge)
        edge.data.materials.append(accent)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.15, location=a)
        packet = bpy.context.object
        packet.name = "Packet-" + str(i)
        packet.data.materials.append(accent)
        packet.location = a
        packet.keyframe_insert(data_path="location", frame=1)
        packet.location = b
        packet.keyframe_insert(data_path="location", frame=scene.frame_end)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.05))
    bpy.context.object.data.materials.append(ground)
    for location, energy, size in [((0, -5, 9), 1700, 7), ((4, 4, 6), 1300, 5)]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
    bpy.ops.object.camera_add(location=(8, -13, 10))
    camera = bpy.context.object
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = max(12, len(nodes) * 3.5)
    camera.rotation_euler = (
        (Vector((0, 0, 0.4)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    camera.keyframe_insert(data_path="location", frame=1)
    camera.location.x -= 1.5
    camera.keyframe_insert(data_path="location", frame=scene.frame_end)
    for frame in (1, scene.frame_end):
        scene.frame_set(frame)
        camera.rotation_euler = (
            (Vector((0, 0, 0.4)) - camera.location).to_track_quat("-Z", "Y").to_euler()
        )
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(spec["output"]) / "Scene.blend"))
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    create(json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text()))

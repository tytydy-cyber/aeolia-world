"""Build the cloud corridor v2: a puffy vaulted shell, floor cloud banks, a layered distant gate and floating islands.

Run: Blender --background --python source/scripts/build_playroom_cloud_corridor_v2.py
Metres. All four root nodes share one origin, the floor centre of the corridor, so placing them at the same
transform assembles the scene. The corridor runs along three.js Z: the entrance is at z=+11, the far end at z=-11,
and the gates continue beyond it to z≈-20.5. Floor pieces sink 1 cm (y=-0.01).
Root nodes: CloudCorridorShell, CloudFloorBanks, DistantCloudGate, FloatingCloudIslands. The gate is backdrop beyond
the far end: its arches narrow below 8 m at 6 m height, so keep the player out of it. The islands' children
FloatingCloudIslandA/B/C sit at their own centres (node translation), ready for independent drift of ±1.5 m
horizontally and ±0.5 m vertically without reaching the shell or the 8 × 6 m flight path.
"""
from pathlib import Path
from mathutils import Vector
import bmesh
import bpy
import math
import numpy as np
import random

ROOT = Path(__file__).resolve().parents[2]
GLB = ROOT / "outputs/assets/playroom/playroom-cloud-corridor-v2.glb"
BLEND = ROOT / "source/blender/playroom-cloud-corridor-v2.blend"
PREVIEW = ROOT / "source/previews/playroom-cloud-corridor-v2-preview.png"
SINK = -.01
bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb(r, g, b):
    return tuple((c / 255) ** 2.2 for c in (r, g, b))


def material(name, color, rough):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return mat


# Faded sky, cream, pale grey-blue and a little faded coral; no pure white. Names carry the game's soft words.
SKY = material("Faded sky cloud wall", srgb(161, 186, 202), .92)
CREAM = material("Cream cloud padding", srgb(226, 212, 182), .93)
GREY = material("Pale grey-blue cloud", srgb(176, 190, 198), .93)
CORAL = material("Faded coral cloud trim", srgb(196, 128, 112), .93)


def node(name, parent=None, location=(0, 0, 0)):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent, obj.location = parent, location
    return obj


def mesh(parent, name, verts, faces, materials, indices=None, soft_angle=40):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    for mat in materials:
        data.materials.append(mat)
    if indices:
        data.polygons.foreach_set("material_index", indices)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        face.smooth = True
    for edge in bm.edges:
        edge.smooth = len(edge.link_faces) == 2 and edge.calc_face_angle(0) <= math.radians(soft_angle)
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    return obj


def puff(parent, name, loc, radii, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=9, radius=1, location=loc)
    obj = bpy.context.object
    obj.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.name, obj.parent = name, parent
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def lumps(t, count, phase, power=.6):
    return abs(math.sin(count * t + phase)) ** power


# 1. CloudCorridorShell: a 1.2–1.5 m thick vault, about 26 m wide, 14.5 m tall and 22 m deep. Its inner face swells
# into cloud puffs whose rhythm drifts along the length, so no two cross-sections repeat; the outer face is smooth.
shell = node("CloudCorridorShell")
ARC, rings, M = 56, [], 0
for i in range(41):
    y = -11 + i * .55
    a, b = 12.0 + .5 * math.sin(y * .25), 13.0 + .6 * math.sin(y * .2 + 1)
    inner, outer = [], []
    for j in range(ARC + 1):
        t = j / ARC * math.pi                                       # right floor → crown → left floor
        f = 1 - .055 * lumps(t, 5, .9 * math.sin(y * .3) + i * .07)
        z = SINK if j in (0, ARC) else b * math.sin(t) * f
        inner.append((a * math.cos(t) * f, y, z))
        outer.append(((a + 1.3) * math.cos(t), y, SINK if j in (0, ARC) else (b + 1.4) * math.sin(t)))
    rings.append(inner + outer[::-1])
M = len(rings[0])
verts = [p for ring in rings for p in ring]
faces, indices = [], []
for i in range(len(rings) - 1):
    for j in range(M):
        faces.append((i * M + j, i * M + (j + 1) % M, (i + 1) * M + (j + 1) % M, (i + 1) * M + j))
        indices.append(0 if j < ARC else 1 if ARC < j < M - 1 else 2)  # inner sky, outer grey-blue, floor strips cream
faces += [tuple(range(M)), tuple(range((len(rings) - 1) * M, len(rings) * M))]
indices += [2, 2]                                                    # cream end faces
mesh(shell, "Vault", verts, faces, [SKY, GREY, CREAM], indices)

# 2. CloudFloorBanks: puffy banks on both sides, a bigger rolling bank on the left and a lower broken one on the right,
# leaving the middle 7 m (|x| < 3.5) and the floor between them clear.
banks = node("CloudFloorBanks")
LEFT = ((-6.2, -8.5, 1.9, 1.3, 1.6), (-7.6, -5.6, 2.3, 1.6, 2.2), (-5.6, -2.4, 1.6, 1.2, 1.3), (-7.9, .4, 2.0, 1.8, 2.5),
        (-6.0, 3.4, 1.8, 1.3, 1.5), (-8.2, 6.0, 2.1, 1.5, 2.0), (-5.9, 8.8, 1.5, 1.2, 1.1))
RIGHT = ((6.4, -7.4, 1.6, 1.4, 1.2), (8.0, -4.9, 1.9, 1.3, 1.6), (6.1, 1.6, 1.4, 1.2, .9), (7.8, 4.2, 1.8, 1.5, 1.4), (6.6, 9.0, 1.5, 1.2, 1.0))
for index, (x, y, rx, ry, rz) in enumerate(LEFT + RIGHT):
    puff(banks, "Floor bank puff", (x, y, rz * .42), (rx, ry * 1.25, rz), CREAM if index % 3 else GREY)

# 3. DistantCloudGate: three arches of overlapping cloud puffs stepping away and shrinking beyond the far end, so the
# end of the corridor reads as layered cloud openings with real depth rather than a cut-out board. The middle arch
# carries a few faded coral puffs.
gate = node("DistantCloudGate")

random.seed(21)
for name, y, a, b, size, base, accent in (("Near gate", 13.4, 9.4, 12.0, 2.0, CREAM, CREAM), ("Middle gate", 16.4, 8.0, 10.3, 1.6, GREY, CORAL),
                                         ("Far gate", 19.3, 6.7, 8.7, 1.3, SKY, CREAM)):
    count = 15
    for j in range(count):
        t = j / (count - 1) * math.pi
        r = size * random.uniform(.8, 1.15)
        z = max(b * math.sin(t), r * .55)
        puff(gate, f"{name} puff", (a * math.cos(t), y + random.uniform(-.35, .35), z), (r, r * .75, r * random.uniform(.8, 1.0)),
             accent if j in (4, 9) else base)

# 4. FloatingCloudIslands: three puff groups at different heights and depths, outside the flight path and the shell
# even when drifting. Each group's node sits at its centre.
islands = node("FloatingCloudIslands")
GROUPS = (("FloatingCloudIslandA", (-6.85, -4.2, 4.3), .85, CREAM), ("FloatingCloudIslandB", (7.0, 3.6, 5.2), .9, GREY),
          ("FloatingCloudIslandC", (.6, 7.4, 9.1), 1.9, CREAM))
PUFFS = ((0, 0, 0, 1.0, .8, .62), (-.8, .2, -.08, .7, .6, .46), (.85, -.15, -.1, .72, .62, .5), (.2, .4, .3, .55, .45, .42), (-.3, -.45, .25, .5, .42, .38))
for name, centre, size, mat in GROUPS:
    group = node(name, islands, centre)
    for k, (dx, dy, dz, rx, ry, rz) in enumerate(PUFFS):
        puff(group, f"{name} puff", (dx * size, dy * size, dz * size), (rx * size, ry * size, rz * size), CORAL if name.endswith("B") and k == 3 else mat)

MODULES = (shell, banks, gate, islands)


def meshes(parent):
    return [obj for obj in parent.children_recursive if obj.type == "MESH"]


for obj in [o for m in MODULES for o in meshes(m)]:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for parent in (shell, banks, gate) + tuple(islands.children):             # join each group's puffs into one mesh
    objects = [o for o in parent.children if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects) > 1:
        bpy.ops.object.join()
    objects[0].name = objects[0].data.name = f"{parent.name} body"
bpy.context.view_layer.update()
triangles = 0
for obj in bpy.data.objects:
    if obj.type == "MESH":
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
assert triangles <= 32_000 and len(bpy.data.materials) <= 6, (triangles, len(bpy.data.materials))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_materials="EXPORT")
print(f"ASSET_CHECK: {GLB.name}: {triangles} triangles, {len(bpy.data.materials)} materials")
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

# Preview: the player's view from the entrance (foreground banks, mid islands, far gates), an outside three-quarter
# view, the gates on their own, and the islands seen from below.
scene = bpy.context.scene
floor = bpy.data.objects.new("Preview floor", bpy.data.meshes.new("Preview floor"))
floor.data.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
floor.data.materials.append(material("Preview floor", (.06, .26, .31), .98))
scene.collection.objects.link(floor)
camera = bpy.data.objects.new("Preview camera", bpy.data.cameras.new("Preview camera"))
scene.collection.objects.link(camera)
sun = bpy.data.objects.new("Preview key", bpy.data.lights.new("Preview key", "SUN"))
scene.collection.objects.link(sun)
sun.data.energy = 2.0
sun.rotation_euler = (math.radians(35), 0, math.radians(-20))
fill = bpy.data.objects.new("Preview fill", bpy.data.lights.new("Preview fill", "POINT"))
scene.collection.objects.link(fill)
fill.data.energy, fill.location = 4000, (0, 2, 9)
scene.world = bpy.data.worlds.new("Preview world")
scene.world.color = (.3, .33, .34)
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 700, 550
scene.render.image_settings.file_format = "PNG"
scene.view_settings.look = "AgX - Medium High Contrast"
everything = [o for m in MODULES for o in meshes(m)]
shots = [(everything, (0, -10.5, 3.2), (0, 12, 4.5), 30), (everything, (30, -34, 22), (0, 3, 5), 28),
         (meshes(gate), (5, 1, 4), (0, 16, 6), 30), (meshes(islands) + meshes(banks), (2, -9, 1.5), (0, 3, 7), 22)]
tiles = []
for shown, eye, target, lens in shots:
    for obj in everything:
        obj.hide_render = obj not in shown
    camera.data.lens = lens
    camera.location = eye
    camera.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEW.parent / f".corridor-tile-{len(tiles)}.png")
    bpy.ops.render.render(write_still=True)
    tiles.append(scene.render.filepath)
sheet = np.zeros((1100, 1400, 4), dtype=np.float32)
for index, path in enumerate(tiles):
    image = bpy.data.images.load(path)
    row = 1 - index // 2
    sheet[row * 550:(row + 1) * 550, (index % 2) * 700:(index % 2 + 1) * 700] = np.array(image.pixels[:], dtype=np.float32).reshape(550, 700, 4)
    bpy.data.images.remove(image)
    Path(path).unlink()
overview = bpy.data.images.new("Playroom cloud corridor v2 overview", 1400, 1100, alpha=True)
overview.pixels = sheet.ravel()
overview.filepath_raw, overview.file_format = str(PREVIEW), "PNG"
overview.save()

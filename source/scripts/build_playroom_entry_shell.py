"""Build the playroom entry shell: a thick portal wall that the rainbow sits in, and three wall-mounted clouds.

Run: Blender --background --python source/scripts/build_playroom_entry_shell.py
Root nodes (getObjectByName): RainbowPortalWall, CloudReliefA, CloudReliefB, CloudReliefC. Front is +Z in three.js.
RainbowPortalWall is in the rainbow's own units (inner radius 4.8, outer 7.48, 1.9 deep): give it the same position,
scale and rotation as playroom-rainbow.glb. Its bottom is at y=-0.01 so it sinks 1 cm into the floor.
The clouds are in metres, about 1 m deep, with their closed flat back at z=-0.01: placed on a wall plane they sink\n1 cm into it. They carry a COLOR_0 shade (lit top, cool belly) that multiplies the material colour.
"""
from pathlib import Path
from mathutils import Vector
import bmesh
import bpy
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GLB = ROOT / "outputs/assets/playroom/playroom-entry-shell.glb"
BLEND = ROOT / "source/blender/playroom-entry-shell.blend"
PREVIEW = ROOT / "source/previews/playroom-entry-shell-preview.png"
RAINBOW = ROOT / "outputs/assets/playroom/playroom-rainbow.glb"
SINK = -.01
bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb(r, g, b):
    return tuple((c / 255) ** 2.2 for c in (r, g, b))


def material(name, color, rough):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    mat.use_backface_culling = False  # exported double-sided, so both faces of the shell render
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return mat


# Mural colours; every name contains a word the game files under its soft group (wall / cloud).
SKY = material("Faded sky wall plaster", srgb(161, 186, 202), .9)
REVEAL = material("Cream wall reveal", srgb(226, 212, 182), .88)
CLOUD = material("Painted cloud relief", srgb(232, 224, 207), .92)


def module(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    return obj


def mesh(parent, name, verts, faces, materials, indices=None):
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
        edge.smooth = len(edge.link_faces) == 2 and edge.calc_face_angle(0) <= math.radians(40)
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    return obj


# 1. RainbowPortalWall: 38 m wide, about 13 m tall, 1.5 m deep, with an asymmetric wavy top and bowed sides.
# The opening is a half disc whose radius splays from 8.5 at both faces to 7.40 at mid-depth, inside the rainbow's
# outer band (7.48), so the cream reveal frames the rainbow and nothing is coplanar with it.
portal = module("RainbowPortalWall")
LEFT, RIGHT, DEPTH = -17.5, 20.5, .75
outline = []                                                     # right floor corner, up, over the top, down to the left
for i in range(9):
    z = SINK + i / 8 * 10.6
    outline.append((RIGHT - .45 * math.sin(math.pi * z / 12), z))
for i in range(1, 41):
    u = i / 40                                                    # right to left along the top
    x = RIGHT - 1.2 - u * (RIGHT - LEFT - 2.4)
    outline.append((x, 12.3 + .65 * math.sin(u * math.pi * 1.6 + .5) + .45 * math.sin(u * math.pi * 3.4)))
for i in range(9):
    z = 10.2 - i / 8 * (10.2 - SINK)
    outline.append((LEFT + .35 * math.sin(math.pi * z / 11), z))
outline.insert(9, (RIGHT - .3, 11.6))                            # rounded upper corners
outline.insert(len(outline) - 9, (LEFT + .35, 11.2))
ARC, LEVELS = 48, [-.75, -.5, -.25, 0, .25, .5, .75]
radius = lambda y: 7.40 + 1.1 * (abs(y) / DEPTH) ** 1.5
rings = []
for y in LEVELS:
    ring = []
    for j in range(ARC + 1):
        a = math.pi - j / ARC * math.pi                           # left floor to right floor
        ring.append((radius(y) * math.cos(a), y, SINK if j in (0, ARC) else radius(y) * math.sin(a)))
    rings.append(ring)
M, R = len(outline), ARC + 1
verts = [(x, -DEPTH, z) for x, z in outline] + [(x, DEPTH, z) for x, z in outline] + [p for ring in rings for p in ring]
front, back = range(M), range(M, 2 * M)
ring = lambda level, j: 2 * M + level * R + j
faces, indices = [], []
faces.append(tuple(front) + tuple(ring(0, j) for j in range(R)));                 indices.append(0)
faces.append(tuple(back) + tuple(ring(len(LEVELS) - 1, j) for j in range(R)));    indices.append(0)
for i in range(M - 1):
    faces.append((front[i], front[i + 1], back[i + 1], back[i]));                 indices.append(0)
for level in range(len(LEVELS) - 1):
    for j in range(ARC):
        faces.append((ring(level, j), ring(level, j + 1), ring(level + 1, j + 1), ring(level + 1, j))); indices.append(1)
faces.append((front[0], back[0]) + tuple(ring(level, ARC) for level in reversed(range(len(LEVELS))))); indices.append(0)
faces.append((front[M - 1],) + tuple(ring(level, 0) for level in range(len(LEVELS))) + (back[M - 1],)); indices.append(0)
wall = mesh(portal, "Portal wall", verts, faces, [SKY, REVEAL], indices)
bevel = wall.modifiers.new("Soft edge", "BEVEL")
bevel.width, bevel.segments, bevel.limit_method, bevel.angle_limit = .22, 3, "ANGLE", math.radians(50)
bpy.context.view_layer.objects.active = wall
bpy.ops.object.modifier_apply(modifier=bevel.name)


# 2. Cloud reliefs: fused cumulus volumes (see cloud_volume.py) cut flat at the back, about 1 m deep, with a lit top
# and a cool shadowed belly baked into vertex colour. Different lobe layouts give three outlines.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cloud_volume import cloud as cumulus

RELIEFS = {
    "CloudReliefA": ((-2.3, -.15, .9), (-1.1, .25, 1.15), (.3, .5, 1.3), (1.6, .2, 1.05), (2.6, -.2, .75), (-.4, -.45, .95), (1.0, -.5, .85)),
    "CloudReliefB": ((-1.7, -.1, .8), (-.5, .3, 1.0), (.8, .1, .95), (1.8, -.25, .7), (.1, -.45, .8)),
    "CloudReliefC": ((-3.6, -.3, .8), (-2.4, .2, 1.1), (-.9, .55, 1.3), (.7, .45, 1.25), (2.2, .1, 1.05), (3.5, -.35, .75), (-1.6, -.6, .9), (1.4, -.6, .95)),
}
reliefs = []
for index, (name, lobes) in enumerate(RELIEFS.items()):
    root = module(name)
    cumulus(root, f"{name}Relief", [((x, -.3, z), r) for x, z, r in lobes], CLOUD, resolution=.24, faces=2400,
            cut=(1, .01, False), seed=7 + index)
    reliefs.append(root)
MODULES = [portal] + reliefs

for parent in MODULES:
    for obj in parent.children_recursive:
        obj.name = obj.data.name = f"{parent.name} — {obj.name}"
bpy.context.view_layer.update()
triangles = 0
for obj in bpy.data.objects:
    if obj.type == "MESH":
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
assert triangles <= 28_000 and len(bpy.data.materials) <= 6, (triangles, len(bpy.data.materials))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_materials="EXPORT", export_vertex_color="ACTIVE")
print(f"ASSET_CHECK: {GLB.name}: {triangles} triangles, {len(bpy.data.materials)} materials")
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
from cloud_volume import preview_tint
preview_tint(CLOUD)


# Preview: the portal with the real rainbow seen front and back, and the three clouds on a wall strip.
def meshes(parent):
    return [obj for obj in parent.children_recursive if obj.type == "MESH"]


def bounds(objects):
    points = [obj.matrix_world @ Vector(c) for obj in objects for c in obj.bound_box]
    return Vector([min(p[i] for p in points) for i in range(3)]), Vector([max(p[i] for p in points) for i in range(3)])


bpy.ops.import_scene.gltf(filepath=str(RAINBOW))
rainbow = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
for index, root in enumerate(reliefs):
    root.location = (-8 + index * 7.5, 30, 2.5 + (index % 2) * 1.4)
scene = bpy.context.scene
floor = bpy.data.objects.new("Preview floor", bpy.data.meshes.new("Preview floor"))
floor.data.from_pydata([(-80, -80, 0), (80, -80, 0), (80, 80, 0), (-80, 80, 0)], [], [(0, 1, 2, 3)])
floor.data.materials.append(material("Preview floor", (.06, .26, .31), .98))
backing = bpy.data.objects.new("Preview wall", bpy.data.meshes.new("Preview wall"))
backing.data.from_pydata([(-14, 30, 0), (14, 30, 0), (14, 30, 9), (-14, 30, 9)], [], [(0, 1, 2, 3)])
backing.data.materials.append(SKY)
for obj in (floor, backing):
    scene.collection.objects.link(obj)
camera = bpy.data.objects.new("Preview camera", bpy.data.cameras.new("Preview camera"))
scene.collection.objects.link(camera)
camera.data.lens = 35
sun = bpy.data.objects.new("Preview key", bpy.data.lights.new("Preview key", "SUN"))
scene.collection.objects.link(sun)
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
scene.world = bpy.data.worlds.new("Preview world")
scene.world.color = (.42, .46, .47)
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 700, 550
scene.render.image_settings.file_format = "PNG"
scene.view_settings.look = "AgX - Medium High Contrast"
cloud_objects = [o for r in reliefs for o in meshes(r)]
shots = [(meshes(portal) + rainbow, (.35, -1, .3), 1.9), (meshes(portal) + rainbow, (-.3, 1, .25), 1.9),
         (meshes(portal) + rainbow, (.15, -1, .05), .55), (cloud_objects + [backing], (.25, -1, .25), 1.6)]
tiles = []
for shown, direction, distance in shots:
    for obj in meshes(portal) + rainbow + cloud_objects + [backing]:
        obj.hide_render = obj not in shown
    low, high = bounds([o for o in shown if o is not backing])
    centre, size = (low + high) / 2, (high - low).length / 2
    if distance < 1:
        centre = Vector((0, 0, 3.0))                              # a player's-eye view through the opening
    direction = Vector(direction).normalized()
    camera.location = centre + direction * size * distance
    camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEW.parent / f".entry-tile-{len(tiles)}.png")
    bpy.ops.render.render(write_still=True)
    tiles.append(scene.render.filepath)
sheet = np.zeros((1100, 1400, 4), dtype=np.float32)
for index, path in enumerate(tiles):
    image = bpy.data.images.load(path)
    row = 1 - index // 2
    sheet[row * 550:(row + 1) * 550, (index % 2) * 700:(index % 2 + 1) * 700] = np.array(image.pixels[:], dtype=np.float32).reshape(550, 700, 4)
    bpy.data.images.remove(image)
    Path(path).unlink()
overview = bpy.data.images.new("Playroom entry shell overview", 1400, 1100, alpha=True)
overview.pixels = sheet.ravel()
overview.filepath_raw, overview.file_format = str(PREVIEW), "PNG"
overview.save()

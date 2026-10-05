"""Build the playroom floor kit: rainbow wall joins, cloud carpet, meadow berm, padded fence island.

Run: Blender --background --python source/scripts/build_playroom_floor_modules.py
Each module is a root node at the GLB origin (getObjectByName: RainbowWallJoin, CloudCarpet, SoftMeadowBerm,
PaddedFenceIsland). Front is +Z in three.js. Every module's lowest face is already at y=-0.01, so placing the
node at floor height sinks it 1 cm and nothing flickers against the floor. RainbowWallJoin is in the rainbow's
own units: give it the same position, scale and rotation as playroom-rainbow.glb.
"""
from pathlib import Path
from mathutils import Vector
import bmesh
import bpy
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GLB = ROOT / "outputs/assets/playroom/playroom-floor-modules.glb"
BLEND = ROOT / "source/blender/playroom-floor-modules.blend"
PREVIEW = ROOT / "source/previews/playroom-floor-modules-preview.png"
RAINBOW = ROOT / "outputs/assets/playroom/playroom-rainbow.glb"
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


# Colours sampled from the three murals (wall-clouds / wall-hills / wall-meadow): faded sky blue, meadow green,
# warm cream, and the faded coral of the painted flowers. Names carry the game's soft / plastic grouping words.
BLUE = material("Faded blue soft vinyl", srgb(160, 182, 196), .9)
GRASS = material("Meadow grass carpet", srgb(146, 160, 118), .97)
CREAM = material("Cream soft padding", srgb(226, 212, 182), .92)
CORAL = material("Faded coral fabric", srgb(196, 128, 112), .95)
POST = material("Cream plastic post", srgb(226, 212, 182), .45)


def module(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    return obj


def mesh(parent, name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(data)
    bm.free()
    return obj


def bevel(obj, width, segments=4):
    mod = obj.modifiers.new("Soft edge", "BEVEL")
    mod.width, mod.segments, mod.limit_method = width, segments, "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def loft(parent, name, rings, mat):
    """Rings of equal length joined into a tube, closed by a cap at each end."""
    count = len(rings[0])
    verts = [p for ring in rings for p in ring]
    faces = [(i * count + j, i * count + (j + 1) % count, (i + 1) * count + (j + 1) % count, (i + 1) * count + j)
             for i in range(len(rings) - 1) for j in range(count)]
    faces += [tuple(range(count)), tuple(range((len(rings) - 1) * count, len(rings) * count))]
    return mesh(parent, name, verts, faces, mat)


def rounded_section(width, height, count=14, power=5):
    """A soft rounded-rectangle cross-section, as (across, up) offsets around its centre."""
    points = []
    for k in range(count):
        a = k / count * math.tau
        c, s = math.cos(a), math.sin(a)
        points.append((width / 2 * math.copysign(abs(c) ** (2 / power), c), height / 2 * math.copysign(abs(s) ** (2 / power), s)))
    return points


def arc_loft(parent, name, radius, z, a0, a1, section, mat, steps):
    rings = []
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        rings.append([(math.cos(a) * (radius + u), math.sin(a) * (radius + u), z + v) for u, v in section])
    return loft(parent, name, rings, mat)


def pipe(parent, name, points, radius, mat):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth, curve.bevel_resolution, curve.use_fill_caps = radius, 2, True
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return obj


def ball(parent, name, loc, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=radius, location=loc)
    obj = bpy.context.object
    obj.name, obj.parent = name, parent
    obj.data.materials.append(mat)
    return obj


# 1. RainbowWallJoin: soft padded wing walls hugging the rainbow's outer band (radius 6.38 in rainbow units)
# from the floor to 55°, then rolling down outward to a flat end at |x| = 11 where a room wall can butt on.
# They overlap the outer band by 6 cm and stand 0.2 m proud of its faces, so the rainbow reads as growing
# out of them; the opening inside radius 6.2 stays clear.
join = module("RainbowWallJoin")
INNER, TOP_ANGLE = 6.32, math.radians(55)
for side in (-1, 1):
    arc = [(INNER * math.cos(TOP_ANGLE * (1 - i / 10)), INNER * math.sin(TOP_ANGLE * (1 - i / 10))) for i in range(10)]
    end = [(11.0, SINK), (11.0, 3.6), (10.8, 4.0)]
    top = []
    for i in range(1, 12):
        u = i / 12
        x = 10.8 - u * (10.8 - arc[0][0] - .25)
        top.append((x, 4.0 + 1.3 * u ** 1.4 + .16 * math.sin(u * math.pi * 2)))
    outline = [arc[0]] + arc[1:] + [(INNER, SINK)] + end + top
    count = len(outline)
    verts = [(side * x, y, z) for y in (-1.15, 1.15) for x, z in outline]
    faces = [tuple(range(count)), tuple(range(count, count * 2))]
    faces += [(i, (i + 1) % count, count + (i + 1) % count, count + i) for i in range(count)]
    bevel(mesh(join, "Padded wing wall", verts, faces, BLUE), .28)
    for y in (-1.17, 1.17):
        pipe(join, "Cream piping", [(side * INNER, y, .12)] + [(side * x, y, z) for x, z in arc[::-1]], .12, CREAM)

# 2. CloudCarpet: an asymmetric cloud outline, 9.5 cm thick at the rounded rim, swelling to about 15 cm inside.
carpet = module("CloudCarpet")
N = 64


def cloud_radius(t):
    return 1 + .22 * abs(math.sin(3 * t + .4)) + .08 * math.cos(t - .6)  # six uneven lobes, fuller on one side


rings = []
for inset, z in ((0, SINK), (0, .03), (.025, .068), (.07, .085)):
    rings.append([((3.2 * cloud_radius(t) - inset) * math.cos(t), (2.1 * cloud_radius(t) - inset * .66) * math.sin(t), z)
                  for t in (k / N * math.tau for k in range(N))])
for f in (.85, .65, .45, .25):
    rings.append([(3.1 * cloud_radius(t) * f * math.cos(t), 2.05 * cloud_radius(t) * f * math.sin(t),
                   .085 + .05 * (1 - f) + .012 * math.sin(3 * t + 6 * f)) for t in (k / N * math.tau for k in range(N))])
verts = [p for ring in rings for p in ring] + [(0, 0, .148)]
faces = [tuple(range(N - 1, -1, -1))]
faces += [(i * N + k, i * N + (k + 1) % N, (i + 1) * N + (k + 1) % N, (i + 1) * N + k) for i in range(len(rings) - 1) for k in range(N)]
centre, last = len(verts) - 1, (len(rings) - 1) * N
faces += [(last + k, last + (k + 1) % N, centre) for k in range(N)]
mesh(carpet, "Cloud carpet", verts, faces, CREAM)

# 3. SoftMeadowBerm: a 12 m S-curved low hill, 25–65 cm high along its crest, rounded down to the floor at both ends.
berm = module("SoftMeadowBerm")
rings = []
for i in range(49):
    t = i / 48
    x, y = -6 + 12 * t, 1.2 * math.sin((-6 + 12 * t) * .45)
    tangent = Vector((1, 1.2 * .45 * math.cos(x * .45), 0)).normalized()
    normal = Vector((-tangent.y, tangent.x, 0))
    envelope = max(math.sin(math.pi * t) ** .5, .06)
    height = envelope * (.45 + .2 * math.sin(math.tau * 1.5 * t + .3))
    half = envelope * 1.25 * (1 + .25 * math.cos(3 * t))
    section = [(-half, SINK)] + [(s * half, height * max(1 - s * s, 0) ** .7) for s in (j / 6 - 1 for j in range(13))] + [(half, SINK)]
    rings.append([(x + normal.x * u, y + normal.y * u, z) for u, z in section])
loft(berm, "Meadow berm", rings, GRASS)

# 4. PaddedFenceIsland: a soft round base, a 280° curved padded rail open to the front, and a curved bench inside.
island = module("PaddedFenceIsland")
base = []
for k in range(56):
    t = k / 56 * math.tau
    base.append((3.45 * (1 + .04 * math.sin(3 * t + 1)) * math.cos(t), 3.45 * (1 + .04 * math.sin(3 * t + 1)) * math.sin(t)))
verts = [(x, y, SINK) for x, y in base] + [(x, y, .09) for x, y in base]
faces = [tuple(range(55, -1, -1)), tuple(range(56, 112))] + [(k, (k + 1) % 56, 56 + (k + 1) % 56, 56 + k) for k in range(56)]
bevel(mesh(island, "Soft island base", verts, faces, BLUE), .04, 2)
A0, A1 = math.radians(-40), math.radians(220)  # the gap faces -Y, the front
arc_loft(island, "Padded top rail", 3.0, .84, A0, A1, rounded_section(.26, .22), CORAL, 52)
arc_loft(island, "Padded low rail", 3.0, .44, A0, A1, rounded_section(.16, .14), CORAL, 52)
for k in range(11):
    a = A0 + (A1 - A0) * k / 10
    arc_loft(island, "Soft fence post", 3.0, .45, a - .035, a + .035, rounded_section(.2, .76, 10), POST, 2)
for a in (A0, A1):
    ball(island, "Rail end cap", (3.0 * math.cos(a), 3.0 * math.sin(a), .84), .17, CORAL)
arc_loft(island, "Bench plinth", 2.35, .28, math.radians(15), math.radians(165), rounded_section(.42, .34), POST, 30)
arc_loft(island, "Bench cushion", 2.35, .49, math.radians(12), math.radians(168), rounded_section(.6, .16), CORAL, 34)

MODULES = (join, carpet, berm, island)


def meshes(parent):
    return [obj for obj in parent.children_recursive if obj.type == "MESH"]


def smooth(obj, angle=math.radians(40)):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for face in bm.faces:
        face.smooth = True
    for edge in bm.edges:
        edge.smooth = len(edge.link_faces) == 2 and edge.calc_face_angle(0) <= angle
    bm.to_mesh(obj.data)
    bm.free()


for parent in MODULES:
    groups = {}
    for obj in meshes(parent):
        smooth(obj)
        groups.setdefault(obj.data.materials[0].name, []).append(obj)
    for name, objects in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        if len(objects) > 1:
            bpy.ops.object.join()
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        objects[0].name = objects[0].data.name = f"{parent.name} — {name}"

bpy.context.view_layer.update()
triangles = 0
for obj in bpy.data.objects:
    if obj.type == "MESH":
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
assert triangles <= 24_000 and len(bpy.data.materials) <= 6, (triangles, len(bpy.data.materials))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_materials="EXPORT")
print(f"ASSET_CHECK: {GLB.name}: {triangles} triangles, {len(bpy.data.materials)} materials")
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))


# 2×2 overview: each module alone and framed to its bounds; the wall join is shown with the real rainbow.
def bounds(objects):
    points = [obj.matrix_world @ Vector(c) for obj in objects for c in obj.bound_box]
    return Vector([min(p[i] for p in points) for i in range(3)]), Vector([max(p[i] for p in points) for i in range(3)])


bpy.ops.import_scene.gltf(filepath=str(RAINBOW))
rainbow = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
scene = bpy.context.scene
floor = bpy.data.objects.new("Preview floor", bpy.data.meshes.new("Preview floor"))
floor.data.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
floor.data.materials.append(material("Preview floor", (.06, .26, .31), .98))
scene.collection.objects.link(floor)
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
tiles = []
for parent in MODULES:
    shown = meshes(parent) + (rainbow if parent is join else [])
    for obj in [o for m in MODULES for o in meshes(m)] + rainbow:
        obj.hide_render = obj not in shown
    low, high = bounds(shown)
    centre, radius = (low + high) / 2, (high - low).length / 2
    direction = Vector((.5, -1, .55 if parent is join else .9)).normalized()
    camera.location = centre + direction * radius * 2.3
    camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEW.parent / f".floor-tile-{len(tiles)}.png")
    bpy.ops.render.render(write_still=True)
    tiles.append(scene.render.filepath)
sheet = np.zeros((1100, 1400, 4), dtype=np.float32)
for index, path in enumerate(tiles):
    image = bpy.data.images.load(path)
    row = 1 - index // 2
    sheet[row * 550:(row + 1) * 550, (index % 2) * 700:(index % 2 + 1) * 700] = np.array(image.pixels[:], dtype=np.float32).reshape(550, 700, 4)
    bpy.data.images.remove(image)
    Path(path).unlink()
overview = bpy.data.images.new("Playroom floor overview", 1400, 1100, alpha=True)
overview.pixels = sheet.ravel()
overview.filepath_raw, overview.file_format = str(PREVIEW), "PNG"
overview.save()

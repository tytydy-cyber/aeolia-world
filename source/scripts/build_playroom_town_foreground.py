"""Build the child-town foreground kit: a bench cluster, a sign cluster and a small ride-on vehicle.

Run: Blender --background --python source/scripts/build_playroom_town_foreground.py
Root nodes (getObjectByName): TownBenchCluster, TownSignCluster, TownVehicleSilhouette. Game metres at scale 1 for the
3.6 m traveler; each node's origin is its floor centre, each footprint is at most 5.2 × 3.4 m so a 1.5 m path fits
around it, and bottoms sit at y=-0.01. Front is +Z in three.js. No lettering: signs are faded shapes.
"""
from pathlib import Path
from mathutils import Vector
import bmesh
import bpy
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GLB = ROOT / "outputs/assets/playroom/playroom-town-foreground.glb"
BLEND = ROOT / "source/blender/playroom-town-foreground.blend"
PREVIEW = ROOT / "source/previews/playroom-town-foreground-preview.png"
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


# Faded coral, meadow green, cream and dull blue; names carry the game's soft / plastic words.
CORAL = material("Faded coral plastic", srgb(196, 128, 112), .45)
GREEN = material("Meadow green soft foliage", srgb(146, 160, 118), .95)
CREAM = material("Cream soft padding", srgb(226, 212, 182), .92)
BLUE = material("Dull blue plastic", srgb(112, 138, 160), .45)


def node(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    return obj


def mesh(parent, name, verts, faces, mat, soft=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    obj["soft"] = soft
    return obj


def loft(parent, name, rings, mat, soft=False):
    n = len(rings[0])
    verts = [p for ring in rings for p in ring]
    faces = [(i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j) for i in range(len(rings) - 1) for j in range(n)]
    faces += [tuple(range(n)), tuple(range((len(rings) - 1) * n, len(rings) * n))]
    return mesh(parent, name, verts, faces, mat, soft)


def rounded(width, height, count=12, power=5):
    out = []
    for k in range(count):
        a = k / count * math.tau
        c, s = math.cos(a), math.sin(a)
        out.append((width / 2 * math.copysign(abs(c) ** (2 / power), c), height / 2 * math.copysign(abs(s) ** (2 / power), s)))
    return out


def sweep(parent, name, path, section, mat, soft=False, ref=None):
    """Sweep a (side, up) section along a path. 'up' stays near world Z, or near world Y on vertical stretches."""
    rings = []
    for i, p in enumerate(path):
        tangent = (Vector(path[min(i + 1, len(path) - 1)]) - Vector(path[max(i - 1, 0)])).normalized()
        axis = Vector(ref or ((0, 1, 0) if abs(tangent.z) > .9 else (0, 0, 1)))
        side = tangent.cross(axis).normalized()
        up = side.cross(tangent).normalized()
        rings.append([tuple(Vector(p) + side * u + up * v) for u, v in section])
    return loft(parent, name, rings, mat, soft)


def tub(parent, name, centre, radius, height, mat, flare=.12):
    """A rounded planter or wheel-like drum: superellipse rings from base to rim."""
    rings = []
    for z, scale in ((SINK, 1 - flare), (.08, 1 - flare / 2), (height - .1, 1), (height, .96), (height - .04, .9)):
        rings.append([(centre[0] + radius * scale * c, centre[1] + radius * scale * s, z)
                      for c, s in ((math.copysign(abs(math.cos(a)) ** .7, math.cos(a)), math.copysign(abs(math.sin(a)) ** .7, math.sin(a))) for a in (k / 20 * math.tau for k in range(20)))])
    return loft(parent, name, rings, mat)


def blob(parent, name, loc, radii, mat, segments=12, rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=loc)
    obj = bpy.context.object
    obj.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.name, obj.parent = name, parent
    obj.data.materials.append(mat)
    obj["soft"] = True
    return obj


def disc(parent, name, centre, axis_y_angle, radius, thick, mat, sides=20, shape=None):
    """A thick flat shape facing the front (local XZ outline, thickness along Y), turned about Z."""
    outline = shape or [(radius * math.cos(a), radius * math.sin(a)) for a in (k / sides * math.tau for k in range(sides))]
    c, s = math.cos(axis_y_angle), math.sin(axis_y_angle)
    to_world = lambda x, y, z: (centre[0] + x * c - y * s, centre[1] + x * s + y * c, centre[2] + z)
    n = len(outline)
    verts = [to_world(x, y, z) for y in (-thick / 2, thick / 2) for x, z in outline]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    obj = mesh(parent, name, verts, faces, mat)
    mod = obj.modifiers.new("Soft edge", "BEVEL")
    mod.width, mod.segments = min(.04, thick * .3), 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


# 1. TownBenchCluster: a curved bench with a rolled back, two rounded planters with soft shrubs, and a cream bolster.
bench = node("TownBenchCluster")
arc = [(1.9 * math.sin(t) - .3, -.2 - 1.9 * (1 - math.cos(t)) * .45, 0) for t in (math.radians(-48 + i * 6) for i in range(17))]
sweep(bench, "Curved bench seat", [(x, y, .8) for x, y, _ in arc], rounded(.95, .22), CORAL)
sweep(bench, "Rolled bench back", [(x - .42 * math.sin(math.radians(-48 + i * 6)) * .2, y + .46, 1.35) for i, (x, y, _) in enumerate(arc)], rounded(.22, .78), CORAL)
for i in (2, 14):
    x, y, _ = arc[i]
    sweep(bench, "Bench foot", [(x, y + .1, SINK), (x, y + .1, .72)], [(u, v) for v, u in rounded(.75, .3)], CREAM)
for (x, y), r, h in (((-2.0, .9), .62, .75), ((1.9, 1.05), .5, .6)):
    tub(bench, "Rounded planter", (x, y), r, h, BLUE)
    for k, (dx, dy, dz, s) in enumerate(((0, 0, .45, .55), (-.25, .15, .3, .4), (.22, -.12, .32, .42))):
        blob(bench, "Soft shrub", (x + dx, y + dy, h + dz * (r / .62)), (s * r / .62, s * r / .62, s * .8 * r / .62), GREEN)
sweep(bench, "Soft bolster", [(-1.2 + i * .25, 1.15, .3) for i in range(8)], [(.3 * math.cos(a), .3 * math.sin(a)) for a in (k / 14 * math.tau for k in range(14))], CREAM)

# 2. TownSignCluster: a slightly leaning post with three thick faded shapes (circle, arrow, pennant) set at uneven
# heights and angles, and a low lamp with a curved neck.
signs = node("TownSignCluster")
sweep(signs, "Leaning sign post", [(-.6 + .05 * i, 0, .05 + i * .4) for i in range(10)], rounded(.18, .18, 10), CREAM)
disc(signs, "Circle sign", (-.05, -.05, 3.25), .25, .55, .14, CORAL)
disc(signs, "Arrow sign", (-.35, -.05, 2.45), -.12, 0, .14, BLUE, shape=[(-.1, -.28), (.9, -.28), (1.3, 0), (.9, .28), (-.1, .28)])
disc(signs, "Pennant sign", (-.3, -.04, 1.75), .35, 0, .12, GREEN, shape=[(-.1, -.32), (-.1, .32), (-.95, 0)])
lamp = [(1.3, .2, SINK + i * .32) for i in range(8)] + [(1.3 + .25 * math.sin(i / 5 * math.pi / 2), .2, 2.25 + .35 * math.sin(i / 5 * math.pi)) for i in range(1, 6)]
sweep(signs, "Low lamp post", lamp, [(.08 * math.cos(a), .08 * math.sin(a)) for a in (k / 10 * math.tau for k in range(10))], BLUE)
blob(signs, "Lamp shade", (1.62, .2, 2.32), (.32, .32, .22), CREAM)
tub(signs, "Sign base", (-.6, 0), .38, .22, BLUE)

# 3. TownVehicleSilhouette: a small ride-on car about 3 m long and 1.8 m tall, with a lofted body, a cream seat,
# four thick wheels and a steering ring, readable from every side.
car = node("TownVehicleSilhouette")
body = []
for i in range(13):
    t = i / 12
    x = -1.45 + 2.9 * t
    top = .95 + .35 * math.sin(math.pi * min(1, t * 1.6)) - .25 * max(0, t - .7) / .3
    half = .72 * (1 - .18 * (2 * t - 1) ** 4)
    body.append([(x, half * u, .32 + (top - .32) * (v + 1) / 2) for u, v in rounded(2, 2, 14, 4)])
loft(car, "Rounded car body", body, CORAL)
blob(car, "Car seat", (-.45, 0, 1.2), (.45, .5, .32), CREAM)
blob(car, "Seat back", (-.85, 0, 1.55), (.18, .5, .45), CREAM)
for x in (-.95, .95):
    for y in (-.78, .78):
        rings = [[(x + r * math.cos(a), y + w, .39 + r * math.sin(a)) for a in (k / 20 * math.tau for k in range(20))]
                 for r, w in ((.3, -.16), (.38, -.12), (.4, 0), (.38, .12), (.3, .16))]
        loft(car, "Thick wheel", rings, BLUE)
sweep(car, "Steering column", [(.15, 0, 1.1), (.05, 0, 1.55)], [(.05 * math.cos(a), .05 * math.sin(a)) for a in (k / 8 * math.tau for k in range(8))], CREAM)
ring = [(.02 + .03 * math.sin(a), .28 * math.cos(a), 1.6 + .28 * math.sin(a)) for a in (k / 20 * math.tau for k in range(21))]
sweep(car, "Steering ring", ring[:-1], [(.045 * math.cos(a), .045 * math.sin(a)) for a in (k / 8 * math.tau for k in range(8))], CREAM, ref=(1, 0, 0))

MODULES = (bench, signs, car)


def meshes(parent):
    return [obj for obj in parent.children_recursive if obj.type == "MESH"]


for parent in MODULES:
    objects = meshes(parent)
    for obj in objects:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        for face in bm.faces:
            face.smooth = True
        for edge in bm.edges:
            edge.smooth = obj.get("soft") or (len(edge.link_faces) == 2 and edge.calc_face_angle(0) <= math.radians(45))
        bm.to_mesh(obj.data)
        bm.free()
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    objects[0].name = objects[0].data.name = f"{parent.name} body"

bpy.context.view_layer.update()
triangles = 0
for obj in bpy.data.objects:
    if obj.type == "MESH":
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
assert triangles <= 8_000 and len(bpy.data.materials) <= 5, (triangles, len(bpy.data.materials))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_materials="EXPORT")
print(f"ASSET_CHECK: {GLB.name}: {triangles} triangles, {len(bpy.data.materials)} materials")
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

# Preview: the three groups side by side with a 3.6 m figure, then each from closer.
scene = bpy.context.scene
for parent, x in zip(MODULES, (-6.5, 0, 6.5)):
    parent.location.x = x
floor = bpy.data.objects.new("Preview floor", bpy.data.meshes.new("Preview floor"))
floor.data.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
floor.data.materials.append(material("Preview floor", (.06, .26, .31), .98))
scene.collection.objects.link(floor)
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=.45, depth=3.6, location=(-3.2, 1.5, 1.8))
bpy.context.object.data.materials.append(material("Preview figure", (.5, .2, .15), .8))
camera = bpy.data.objects.new("Preview camera", bpy.data.cameras.new("Preview camera"))
scene.collection.objects.link(camera)
camera.data.lens = 30
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
shots = [((3, -17, 7), (0, 0, 1.2)), ((-4.5, -6.5, 3.2), (-6.5, 0, .9)), ((2.2, -6, 3.4), (0, 0, 1.8)), ((9.2, -5.2, 3), (6.5, 0, .9))]
tiles = []
for eye, target in shots:
    camera.location = eye
    camera.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEW.parent / f".town-tile-{len(tiles)}.png")
    bpy.ops.render.render(write_still=True)
    tiles.append(scene.render.filepath)
sheet = np.zeros((1100, 1400, 4), dtype=np.float32)
for index, path in enumerate(tiles):
    image = bpy.data.images.load(path)
    row = 1 - index // 2
    sheet[row * 550:(row + 1) * 550, (index % 2) * 700:(index % 2 + 1) * 700] = np.array(image.pixels[:], dtype=np.float32).reshape(550, 700, 4)
    bpy.data.images.remove(image)
    Path(path).unlink()
overview = bpy.data.images.new("Playroom town foreground overview", 1400, 1100, alpha=True)
overview.pixels = sheet.ravel()
overview.filepath_raw, overview.file_format = str(PREVIEW), "PNG"
overview.save()

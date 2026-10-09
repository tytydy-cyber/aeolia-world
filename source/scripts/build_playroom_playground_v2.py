"""Build the playground v2 hero pieces: a two-cluster tower joined by a thick tunnel, a rope net and a soft-block cluster.

Run: Blender --background --python source/scripts/build_playroom_playground_v2.py
Root nodes (getObjectByName): PlaygroundTowerV2, PlaygroundNetV2, PlaygroundSoftClusterV2. Game metres at scale 1 for
the 3.6 m traveler; each node's origin is its floor centre and bottoms sit at y=-0.01. Front is +Z in three.js.
No floor, backdrop, lights or collision. The tower keeps a clear 4 m wide x 4.2 m high passage through x=0 along Z;
the tunnel crosses above it. Rope spacing and post placement are deliberately uneven.
"""
from pathlib import Path
from mathutils import Matrix, Vector
import bmesh
import bpy
import math
import random
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GLB = ROOT / "outputs/assets/playroom/playroom-playground-v2.glb"
BLEND = ROOT / "source/blender/playroom-playground-v2.blend"
PREVIEW = ROOT / "source/previews/playroom-playground-v2-preview.png"
SINK = -.01
rng = random.Random(7)
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


# Faded blue, meadow green, faded yellow and coral as in the entry and town; cream for rope and padding.
BLUE = material("Dull blue plastic", srgb(112, 138, 160), .45)
GREEN = material("Meadow green soft vinyl", srgb(146, 160, 118), .9)
YELLOW = material("Faded yellow plastic", srgb(232, 203, 139), .5)
CORAL = material("Faded coral soft padding", srgb(196, 128, 112), .92)
CREAM = material("Cream rope and padding", srgb(226, 212, 182), .95)


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


def circle(r, sides):
    return [(r * math.cos(a), r * math.sin(a)) for a in (k / sides * math.tau for k in range(sides))]


def frames(path, ref=None):
    """Per-point (side, up) axes for a path: 'up' stays near world Z, or near world Y on vertical stretches."""
    out = []
    for i, p in enumerate(path):
        tangent = (Vector(path[min(i + 1, len(path) - 1)]) - Vector(path[max(i - 1, 0)])).normalized()
        axis = Vector(ref or ((0, 1, 0) if abs(tangent.z) > .9 else (0, 0, 1)))
        side = tangent.cross(axis).normalized()
        out.append((Vector(p), side, side.cross(tangent).normalized()))
    return out


def sweep(parent, name, path, section, mat, soft=False, ref=None):
    return loft(parent, name, [[tuple(p + side * u + up * v) for u, v in section] for p, side, up in frames(path, ref)], mat, soft)


def tube(parent, name, path, outer, inner, mat, sides=18):
    """A hollow tube: outer and inner walls joined by ring faces at both open ends."""
    rings = [[tuple(p + side * math.cos(a) * r + up * math.sin(a) * r) for a in (k / sides * math.tau for k in range(sides))]
             for r in (outer, inner) for p, side, up in frames(path)]
    m, n = len(path), sides
    verts = [v for ring in rings for v in ring]
    at = lambda wall, i, j: (wall * m + i) * n + j % n
    faces = [(at(w, i, j), at(w, i, j + 1), at(w, i + 1, j + 1), at(w, i + 1, j)) for w in (0, 1) for i in range(m - 1) for j in range(n)]
    faces += [(at(0, i, j), at(0, i, j + 1), at(1, i, j + 1), at(1, i, j)) for i in (0, m - 1) for j in range(n)]
    return mesh(parent, name, verts, faces, mat, True)


def pad(parent, name, centre, w, d, z, thick, mat, rot=0, power=4, count=28):
    """A rounded landing whose top swells gently: superellipse rings from the underside to a soft crown at height z."""
    c, s = math.cos(rot), math.sin(rot)
    ring = rounded(w, d, count, power)
    rings = [[(centre[0] + k * (x * c - y * s), centre[1] + k * (x * s + y * c), z + dz) for x, y in ring]
             for dz, k in ((-thick, .9), (-thick * .55, 1), (-.05, .99), (0, .9), (.06, .55))]
    return loft(parent, name, rings, mat, True)


def block(parent, name, centre, size, rot, mat, z0=SINK, power=4):
    """A soft foam block: rounded superellipse plan with eased top and bottom edges."""
    w, d, h = size
    c, s = math.cos(rot), math.sin(rot)
    ring = rounded(w, d, 24, power)
    rings = [[(centre[0] + k * (x * c - y * s), centre[1] + k * (x * s + y * c), z0 + f * h) for x, y in ring]
             for f, k in ((0, .86), (.06, .97), (.16, 1), (.84, 1), (.94, .97), (1, .86))]
    return loft(parent, name, rings, mat, True)


def blob(parent, name, loc, radii, mat, segments=12, rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=loc)
    obj = bpy.context.object
    obj.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.name, obj.parent = name, parent
    obj.data.materials.append(mat)
    obj["soft"] = True
    return obj


def slab(parent, name, centre, angle, outline, thick, mat):
    """A thick shape from a local XZ outline, thickness along local Y, turned about Z."""
    c, s = math.cos(angle), math.sin(angle)
    to_world = lambda x, y, z: (centre[0] + x * c - y * s, centre[1] + x * s + y * c, centre[2] + z)
    n = len(outline)
    verts = [to_world(x, y, z) for y in (-thick / 2, thick / 2) for x, z in outline]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh(parent, name, verts, faces, mat, True)


def post(parent, centre, radius, height, lean, mat):
    """A round post that bows slightly and leans, never a straight square column."""
    bow = rng.uniform(-.12, .12)
    path = [(centre[0] + lean[0] * t + bow * math.sin(math.pi * t), centre[1] + lean[1] * t, SINK + height * t) for t in (i / 9 for i in range(10))]
    return sweep(parent, "Round post", path, circle(radius, 12), mat)


# 1. PlaygroundTowerV2: two uneven post clusters with domed landings, a thick hollow tunnel arching over the central
# passage, a curving climbing ramp with knobs at front left and a spiral of stepping pods at back right.
tower = node("PlaygroundTowerV2")
for centre, r, h, lean in (((-9.1, -2.0), .34, 8.5, (.2, -.1)), ((-5.3, -2.2), .28, 8.1, (-.25, .1)),
                           ((-9.4, 2.5), .38, 8.6, (.15, .2)), ((-5.6, 2.7), .31, 8.0, (-.1, -.25)),
                           ((5.0, -2.3), .30, 7.4, (.2, .15)), ((9.2, -2.0), .36, 7.6, (-.2, .1)),
                           ((8.8, 2.6), .33, 7.5, (-.15, -.2)), ((5.4, 2.3), .40, 7.3, (.25, -.1))):
    post(tower, centre, r, h, lean, BLUE)
pad(tower, "Left lower landing", (-7.3, .2), 5.2, 5.6, 3.0, .38, CORAL, .12)
pad(tower, "Left upper landing", (-7.7, .7), 3.9, 4.2, 5.6, .34, YELLOW, -.2, 3)
pad(tower, "Right landing", (7.0, 0), 4.8, 5.2, 4.4, .38, CORAL, -.1, 5)
# Padded edge walls on the landings, left open where the ramp, tunnel and pods arrive.
for (cx, cy), w, d, z, rot, gap in (((-7.3, .2), 5.2, 5.6, 3.0, .12, (.45, 1.25)), ((7.0, 0), 4.8, 5.2, 4.4, -.1, (2.6, 3.7))):
    # Start just after the gap so the open wall is one continuous run.
    angles = [gap[1] + k / 40 * math.tau for k in range(41)]
    run = []
    for a in angles:
        if gap[0] <= a % math.tau <= gap[1]:
            continue
        x = .45 * w * math.copysign(abs(math.cos(a)) ** .5, math.cos(a))
        y = .45 * d * math.copysign(abs(math.sin(a)) ** .5, math.sin(a))
        run.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot), z + .3))
    sweep(tower, "Padded landing edge", run, rounded(.32, .6, 10, 3), CREAM)
tunnel = [(-6.0 + 11.6 * t, .6 - .9 * t + .5 * math.sin(math.pi * t), 6.6 - 1.0 * t + .8 * math.sin(math.pi * t)) for t in (i / 35 for i in range(36))]
tube(tower, "Thick crossing tunnel", tunnel, 1.25, 1.0, YELLOW)
for t in (.22, .5, .78):
    i = round(t * 35)
    tangent = Vector(tunnel[i + 1]) - Vector(tunnel[i - 1])
    bpy.ops.mesh.primitive_torus_add(major_radius=1.38, minor_radius=.16, major_segments=20, minor_segments=8, location=tunnel[i],
                                     rotation=tangent.to_track_quat("Z", "Y").to_euler())
    hoop = bpy.context.object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    hoop.name, hoop.parent, hoop["soft"] = "Tunnel hoop", tower, True
    hoop.data.materials.append(CORAL)
ramp = [(-3.4 - 2.4 * math.sin(t * 1.15), -4.8 + 2.7 * t, .13 + 2.9 * t ** 1.3) for t in (i / 24 for i in range(25))]
sweep(tower, "Curved climbing ramp", ramp, rounded(1.8, .28, 14, 4), GREEN, True)
for p, side, up in frames(ramp)[2:-2:2]:
    for _ in range(2):
        blob(tower, "Climbing knob", tuple(p + side * rng.uniform(-.65, .65) + up * .2), (.17, .17, .11), YELLOW, 8, 4)
sweep(tower, "Helix pole", [(9.0, 3.7, SINK), (9.0, 3.7, 5.0)], circle(.22, 10), BLUE)
for i in range(7):
    a = 2.2 + i * .85
    pad(tower, "Stepping pod", (9.0 + 1.25 * math.cos(a), 3.7 + 1.25 * math.sin(a)), 1.2, 1.2, .7 + i * .6, .3, [GREEN, YELLOW, CORAL][i % 3], a, 2.4, 16)
blob(tower, "Left soft roof", (-7.4, .4, 8.75), (2.5, 2.8, .75), GREEN, 16, 8)
blob(tower, "Right dome roof", (7.1, .1, 7.75), (2.6, 2.9, 1.3), YELLOW, 16, 8)

# 2. PlaygroundNetV2: a bellied cargo net of thick rope with uneven spacing between two unequal leaning posts.
net = node("PlaygroundNetV2")
post(net, (-3.4, 0), .26, 6.4, (.25, .3), BLUE)
post(net, (3.2, 0), .3, 5.6, (-.25, -.2), BLUE)
corners = {(0, 0): Vector((-3.05, 0, .7)), (1, 0): Vector((2.9, 0, .7)), (0, 1): Vector((-3.1, .25, 6.0)), (1, 1): Vector((2.9, -.15, 5.2))}


def surface(u, v):
    p = sum(((corners[k] * ((u if k[0] else 1 - u) * (v if k[1] else 1 - v))) for k in corners), Vector())
    return tuple(p + Vector((0, -.85 * math.sin(math.pi * u) * math.sin(math.pi * v), -.45 * math.sin(math.pi * u) * v)))


columns = [.09, .2, .27, .41, .55, .63, .8, .9]
rows = [.08, .15, .26, .33, .47, .62, .7, .84]
wave = lambda i, v: columns[i] + .02 * math.sin(2.7 * math.pi * v + i * 1.7)
for i in range(len(columns)):
    sweep(net, "Vertical rope", [surface(wave(i, v), v) for v in (k / 13 for k in range(14))], circle(.07, 6), CREAM)
for j, v in enumerate(rows):
    sweep(net, "Cross rope", [surface(u, v) for u in (k / 15 for k in range(16))], circle(.06 + .01 * (j % 2), 6), CREAM)
for u, v in ((0, None), (1, None), (None, 0), (None, 1)):
    path = [surface(u, t) if u is not None else surface(t, v) for t in (k / 15 for k in range(16))]
    sweep(net, "Frame rope", path, circle(.11, 8), CREAM)
for i in range(len(columns)):
    for v in rows:
        blob(net, "Rope knot", surface(wave(i, v), v), (.12, .12, .12), CREAM, 5, 3)

# 3. PlaygroundSoftClusterV2: foam blocks, a wedge, an arch, a drum, a column and balls, stacked to about 1.5 traveler
# heights with gaps between groups.
soft = node("PlaygroundSoftClusterV2")
block(soft, "Large foam block", (-2.8, .6), (2.8, 2.4, 2.3), .15, CORAL)
block(soft, "Stacked foam block", (-2.5, .4), (2.0, 1.7, 1.6), -.35, YELLOW, 2.2)
blob(soft, "Top foam ball", (-2.6, .5, 4.75), (.85, .85, .85), GREEN)
slab(soft, "Foam wedge", (.1, .8, SINK), 0, [(1.4, 0), (-1.4, 0), (-1.4, 1.5), (-1.0, 1.6), (1.4, .12)], 1.8, BLUE)
arch = [(1.6 * math.copysign(abs(math.cos(a)) ** .7, math.cos(a)), 2.6 * math.sin(a) ** .8) for a in (k / 12 * math.pi for k in range(13))]
arch += [(.85 * math.copysign(abs(math.cos(a)) ** .7, math.cos(a)), 1.5 * math.sin(a) ** .8) for a in (math.pi - k / 12 * math.pi for k in range(13))]
slab(soft, "Foam arch", (3.4, -.8, SINK), .2, arch, 1.6, GREEN)
block(soft, "Foam drum", (5.2, 1.8), (1.7, 1.7, 1.3), 0, YELLOW, power=2)
block(soft, "Foam column", (5.9, -1.3), (1.1, 1.1, 3.2), .4, BLUE)
for loc, r in (((1.2, -2.2), .62), ((-.9, -2.1), .5)):
    blob(soft, "Soft ball", (*loc, r + SINK), (r, r, r), CORAL)

MODULES = (tower, net, soft)


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
    body = objects[0]
    body.name = body.data.name = f"{parent.name} body"
    for v in body.data.vertices:  # tilted end rings of leaning posts and the ramp foot dip a little; rest them on the floor
        v.co.z = max(v.co.z, SINK)
    if parent is not tower:  # the tower is already centred on its passage; recentre the others on their footprint
        xs, ys = [v.co.x for v in body.data.vertices], [v.co.y for v in body.data.vertices]
        shift = Vector(((min(xs) + max(xs)) / -2, (min(ys) + max(ys)) / -2, 0))
        body.data.transform(Matrix.Translation(shift))

bpy.context.view_layer.update()
triangles = 0
for obj in bpy.data.objects:
    if obj.type == "MESH":
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
assert triangles <= 24_000 and len(bpy.data.materials) <= 5, (triangles, len(bpy.data.materials))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_materials="EXPORT")
print(f"ASSET_CHECK: {GLB.name}: {triangles} triangles, {len(bpy.data.materials)} materials")
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

# Preview: all three with a 3.6 m figure, the tower from the front, the view along the passage, and net + cluster.
scene = bpy.context.scene
for parent, (x, y) in zip(MODULES, ((0, 0), (-15, -6), (15, -6))):
    parent.location.x, parent.location.y = x, y
floor = bpy.data.objects.new("Preview floor", bpy.data.meshes.new("Preview floor"))
floor.data.from_pydata([(-80, -80, 0), (80, -80, 0), (80, 80, 0), (-80, 80, 0)], [], [(0, 1, 2, 3)])
floor.data.materials.append(material("Preview floor", (.06, .26, .31), .98))
scene.collection.objects.link(floor)
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=.45, depth=3.6, location=(0, -6, 1.8))
bpy.context.object.data.materials.append(material("Preview figure", (.5, .2, .15), .8))
camera = bpy.data.objects.new("Preview camera", bpy.data.cameras.new("Preview camera"))
scene.collection.objects.link(camera)
camera.data.lens = 28
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
shots = [((0, -42, 16), (0, -3, 3)), ((6, -21, 7), (0, 0, 4)), ((0, -13, 2.2), (0, 6, 3.4)), ((-6, -20, 5), (-15, -6, 2.8))]
tiles = []
for eye, target in shots:
    camera.location = eye
    camera.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEW.parent / f".playground-tile-{len(tiles)}.png")
    bpy.ops.render.render(write_still=True)
    tiles.append(scene.render.filepath)
sheet = np.zeros((1100, 1400, 4), dtype=np.float32)
for index, path in enumerate(tiles):
    image = bpy.data.images.load(path)
    row = 1 - index // 2
    sheet[row * 550:(row + 1) * 550, (index % 2) * 700:(index % 2 + 1) * 700] = np.array(image.pixels[:], dtype=np.float32).reshape(550, 700, 4)
    bpy.data.images.remove(image)
    Path(path).unlink()
overview = bpy.data.images.new("Playroom playground v2 overview", 1400, 1100, alpha=True)
overview.pixels = sheet.ravel()
overview.filepath_raw, overview.file_format = str(PREVIEW), "PNG"
overview.save()

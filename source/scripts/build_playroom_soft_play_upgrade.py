"""Build soft-play replacements for the slide tower and the ball pit, inside the current assets' bounds.

Run: Blender --background --python source/scripts/build_playroom_soft_play_upgrade.py
Root nodes (getObjectByName): SoftSlideTower, RoundedBallPit. Both use the same units, origin and facing as
playroom-slide.glb and playroom-ball-pit.glb, so they drop into the existing placements and colliders. Front is +Z
in three.js. Bottoms sit at y=-0.01 so they sink 1 cm into the floor.
"""
from pathlib import Path
from mathutils import Vector
import bmesh
import bpy
import math
import numpy as np
import random

ROOT = Path(__file__).resolve().parents[2]
GLB = ROOT / "outputs/assets/playroom/playroom-soft-play-upgrade.glb"
BLEND = ROOT / "source/blender/playroom-soft-play-upgrade.blend"
PREVIEW = ROOT / "source/previews/playroom-soft-play-upgrade-preview.png"
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


# Faded coral, cream, dull blue and meadow green; no primary colours. Names carry the game's soft / plastic words.
CORAL_SOFT = material("Faded coral soft padding", srgb(196, 128, 112), .93)
CREAM = material("Cream soft padding", srgb(226, 212, 182), .92)
BLUE_SOFT = material("Dull blue soft vinyl", srgb(112, 138, 160), .86)
CORAL = material("Faded coral plastic", srgb(196, 128, 112), .4)
BLUE = material("Dull blue plastic", srgb(112, 138, 160), .4)
GREEN = material("Meadow green plastic", srgb(146, 160, 118), .42)


def module(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    return obj


def mesh(parent, name, verts, faces, materials, indices=None, soft=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    for mat in materials:
        data.materials.append(mat)
    if indices:
        data.polygons.foreach_set("material_index", indices)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj["soft"] = soft
    return obj


def bevelled_box(parent, name, loc, size, mat, radius, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.name, obj.parent = name, parent
    obj.data.materials.append(mat)
    mod = obj.modifiers.new("Soft edge", "BEVEL")
    mod.width, mod.segments = min(radius, min(size) * .45), 3
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def column(parent, name, x, y, z0, z1, radius, mat, sides=16):
    """A padded post: a cylinder with rounded ends."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=radius, depth=z1 - z0, location=(x, y, (z0 + z1) / 2))
    obj = bpy.context.object
    obj.name, obj.parent = name, parent
    obj.data.materials.append(mat)
    mod = obj.modifiers.new("Soft edge", "BEVEL")
    mod.width, mod.segments = radius * .6, 3
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj["soft"] = True
    return obj


def ball(parent, loc, radius, mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=loc)
    obj = bpy.context.object
    obj.parent = parent
    obj.data.materials.append(mat)
    obj["soft"] = True
    return obj


def tube_loft(parent, name, rings, materials, indices_for, cyclic_rings=False, caps=True):
    """Rings of equal length joined into a surface; cyclic_rings closes the sweep into a loop (no caps)."""
    count, total = len(rings[0]), len(rings)
    verts = [p for ring in rings for p in ring]
    faces, indices = [], []
    for i in range(total if cyclic_rings else total - 1):
        n = (i + 1) % total
        for j in range(count):
            faces.append((i * count + j, i * count + (j + 1) % count, n * count + (j + 1) % count, n * count + j))
            indices.append(indices_for(j))
    if caps and not cyclic_rings:
        faces += [tuple(range(count)), tuple(range((total - 1) * count, total * count))]
        indices += [indices_for(0)] * 2
    return mesh(parent, name, verts, faces, materials, indices)


# 1. SoftSlideTower: the same footprint as the old tower (posts at ±1.4, ±1.05, deck at 2.6 m, chute to x 5.95),
# but padded round posts with cushioned collars, a soft deck, an arched back panel, a pillow roof and a
# U-section chute of continuous curvature and real thickness.
tower = module("SoftSlideTower")
for x in (-1.4, 1.4):
    for y in (-1.05, 1.05):
        column(tower, "Padded post", x, y, SINK, 5.0, .2, BLUE_SOFT)
        for z in (2.6, 4.9):
            column(tower, "Joint cushion collar", x, y, z - .2, z + .2, .3, CREAM)
bevelled_box(tower, "Soft deck", (0, 0, 2.6), (3.2, 2.5, .32), CREAM, .14)
panel = [(-1.35, 2.75), (1.35, 2.75)] + [(1.35 - i / 12 * 2.7, 3.85 + .45 * math.sin(i / 12 * math.pi)) for i in range(13)]
count = len(panel)
verts = [(x, y, z) for y in (1.01, 1.15) for x, z in panel]
faces = [tuple(range(count)), tuple(range(count, 2 * count))] + [(i, (i + 1) % count, count + (i + 1) % count, count + i) for i in range(count)]
back = mesh(tower, "Arched back panel", verts, faces, [BLUE_SOFT])
roof_rings = []
for z, scale in ((4.95, 1.0), (5.12, 1.04), (5.35, .96), (5.6, .78), (5.85, .5), (6.05, .2), (6.12, .05)):
    ring = []
    for k in range(32):
        a = k / 32 * math.tau
        c, s = math.cos(a), math.sin(a)
        pillow = 1 + .05 * math.cos(4 * a) * (1 - abs(z - 5.3) / 1.2)   # four soft pillow corners
        ring.append((1.66 * scale * pillow * math.copysign(abs(c) ** .5, c), 1.5 * scale * pillow * math.copysign(abs(s) ** .5, s), z))
    roof_rings.append(ring)
tube_loft(tower, "Pillow roof", roof_rings, [CORAL_SOFT], lambda j: 0)
for z in (.55, 1.05, 1.55, 2.05):
    bevelled_box(tower, "Cushioned rung", (-1.65, 1.45, z), (1.0, .2, .16), CREAM, .07)
for x in (-2.12, -1.18):
    column(tower, "Padded ladder rail", x, 1.45, SINK, 2.75, .09, CORAL_SOFT, 12)

HALF, DEPTH, THICK = .74, .3, .1
section = [(s * HALF, DEPTH * abs(s) ** 4) for s in (i / 6 - 1 for i in range(13))]                     # inner trough
section += [(HALF + .05, DEPTH + .05)]                                                              # rolled right rim
section += [(s * (HALF + THICK), DEPTH * abs(s) ** 4 - THICK) for s in (1 - i / 6 for i in range(13))]  # outer shell
section += [(-HALF - .05, DEPTH + .05)]                                                             # rolled left rim
path = [Vector((1.35 + t * 4.6, -1.15, .3 + 2.42 * (1 - t) ** 2)) for t in (i / 30 for i in range(31))]
chute_rings = []
for i, centre in enumerate(path):
    tangent = (path[min(i + 1, 30)] - path[max(i - 1, 0)]).normalized()
    normal = Vector((-tangent.z, 0, tangent.x)).normalized()
    chute_rings.append([tuple(centre + Vector((0, s, 0)) + normal * (h - DEPTH * .5)) for s, h in section])
tube_loft(tower, "Continuous chute", chute_rings, [CORAL], lambda j: 0)
bevelled_box(tower, "Chute support cushion", (4.2, -1.15, .3), (.9, 1.0, .62), CREAM, .2)

# 2. RoundedBallPit: rounded soft walls on the old footprint (outer ±3.78 × ±2.75, inner ±3.36 × ±2.33), a top edge
# that sags between eight cushions, a cream rolled rim, a soft floor, and smooth balls heaped densely in two
# corners and scattered thinly elsewhere.
pit = module("RoundedBallPit")


def superellipse(a, b, t, n=6):
    c, s = math.cos(t), math.sin(t)
    return a * math.copysign(abs(c) ** (2 / n), c), b * math.copysign(abs(s) ** (2 / n), s)


WALL_SEGMENTS, OUT_A, OUT_B, WALL = 96, 3.78, 2.75, .42
wall_section = []                                    # (inset from the outer face, height key); height is filled per ring
for inset, kind in ((0, "floor"), (0, "low"), (0, "high"), (.06, "roll1"), (.21, "roll2"), (.36, "roll1"), (WALL, "high"), (WALL, "inner")):
    wall_section.append((inset, kind))
wall_rings = []
for k in range(WALL_SEGMENTS):
    t = k / WALL_SEGMENTS * math.tau
    top = .92 - .1 * abs(math.sin(4 * t)) ** 1.5      # eight cushions pressed down between their seams
    heights = {"floor": SINK, "low": .3, "high": top - .14, "roll1": top - .04, "roll2": top, "inner": .14}
    ring = []
    for inset, kind in wall_section:
        x, y = superellipse(OUT_A - inset, OUT_B - inset, t)
        ring.append((x, y, heights[kind]))
    ring.append((*superellipse(OUT_A - WALL, OUT_B - WALL, t), SINK))
    wall_rings.append(ring)
tube_loft(pit, "Rounded soft wall", wall_rings, [BLUE_SOFT, CREAM], lambda j: 1 if 2 <= j <= 5 else 0, cyclic_rings=True)
floor = [superellipse(OUT_A - WALL - .02, OUT_B - WALL - .02, k / 64 * math.tau) for k in range(64)]
verts = [(x, y, SINK) for x, y in floor] + [(x, y, .14) for x, y in floor]
faces = [tuple(range(63, -1, -1)), tuple(range(64, 128))] + [(k, (k + 1) % 64, 64 + (k + 1) % 64, 64 + k) for k in range(64)]
mesh(pit, "Soft pit floor", verts, faces, [CREAM])
random.seed(14)
colours, placed = (CORAL, BLUE, GREEN), []
# Two heaps two balls deep (below the old 0.77 collider top) and a thinner single layer elsewhere; balls may rest
# on one another but never coincide.
for cx, cy, spread, count, layers in ((-2.2, 1.2, 1.7, 150, 2), (2.3, -1.2, 1.5, 130, 2), (0, 0, 4.0, 90, 1)):
    for _ in range(count * 8):
        if count == 0:
            break
        r = random.uniform(.19, .23)
        x = max(-OUT_A + WALL + r + .03, min(OUT_A - WALL - r - .03, cx + random.gauss(0, spread * .5)))
        y = max(-OUT_B + WALL + r + .03, min(OUT_B - WALL - r - .03, cy + random.gauss(0, spread * .4)))
        # Rest on the floor or on the balls below, never inside another ball, so no facets can coincide.
        z = .14 + r
        for px, py, pz, pr in placed:
            reach = pr + r + .005
            if math.hypot(x - px, y - py) < reach:
                z = max(z, pz + math.sqrt(reach ** 2 - (x - px) ** 2 - (y - py) ** 2))
        if z > .14 + r + (layers - 1) * .36 + .01 or any(math.dist((x, y, z), p[:3]) < p[3] + r + .004 for p in placed):
            continue
        placed.append((x, y, z, r))
        ball(pit, (x, y, z), r, random.choice(colours))
        count -= 1

MODULES = (tower, pit)


def smooth(obj, angle=math.radians(40)):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        face.smooth = True
    for edge in bm.edges:
        edge.smooth = obj.get("soft") or (len(edge.link_faces) == 2 and edge.calc_face_angle(0) <= angle)
    bm.to_mesh(obj.data)
    bm.free()


for parent in MODULES:
    objects = [obj for obj in parent.children_recursive if obj.type == "MESH"]
    for obj in objects:
        smooth(obj)
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
assert triangles <= 35_000 and len(bpy.data.materials) <= 6, (triangles, len(bpy.data.materials))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_materials="EXPORT")
print(f"ASSET_CHECK: {GLB.name}: {triangles} triangles, {len(bpy.data.materials)} materials")
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))


# Preview: each module alone from a game-like three-quarter view and from closer, as a 2×2 sheet.
def bounds(objects):
    points = [obj.matrix_world @ Vector(c) for obj in objects for c in obj.bound_box]
    return Vector([min(p[i] for p in points) for i in range(3)]), Vector([max(p[i] for p in points) for i in range(3)])


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
bodies = {parent: [obj for obj in parent.children_recursive if obj.type == "MESH"] for parent in MODULES}
shots = [(tower, (.6, -1, .45), 2.4), (tower, (-.7, -1, .3), 1.7), (pit, (.4, -1, .8), 2.0), (pit, (-.3, -1, .45), 1.25)]
tiles = []
for parent, direction, distance in shots:
    for other, objects in bodies.items():
        for obj in objects:
            obj.hide_render = other is not parent
    low, high = bounds(bodies[parent])
    centre, size = (low + high) / 2, (high - low).length / 2
    direction = Vector(direction).normalized()
    camera.location = centre + direction * size * distance
    camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEW.parent / f".soft-tile-{len(tiles)}.png")
    bpy.ops.render.render(write_still=True)
    tiles.append(scene.render.filepath)
sheet = np.zeros((1100, 1400, 4), dtype=np.float32)
for index, path in enumerate(tiles):
    image = bpy.data.images.load(path)
    row = 1 - index // 2
    sheet[row * 550:(row + 1) * 550, (index % 2) * 700:(index % 2 + 1) * 700] = np.array(image.pixels[:], dtype=np.float32).reshape(550, 700, 4)
    bpy.data.images.remove(image)
    Path(path).unlink()
overview = bpy.data.images.new("Playroom soft play overview", 1400, 1100, alpha=True)
overview.pixels = sheet.ravel()
overview.filepath_raw, overview.file_format = str(PREVIEW), "PNG"
overview.save()

"""Build the quiet rooms as two separate sets: a nap room and a birthday room.

Run: Blender --background --python source/scripts/build_playroom_quiet_split.py
Root nodes (getObjectByName): NapRoomSet, BirthdayRoomSet. Game metres at scale 1, sized for the 3.6 m traveler
(about twice real size): beds 3.8 m long, table top 1.2 m, chair seats 0.7 m. Each node's origin is its floor centre,
each fits in 22 × 8 m, keeps a 3 m aisle clear along the middle (|x| < 1.5), and sinks 1 cm into the floor.
Front is +Z in three.js. The nap set's discovery bed is the one set apart on the right behind the screen.
"""
from pathlib import Path
from mathutils import Vector
import bmesh
import bpy
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GLB = ROOT / "outputs/assets/playroom/playroom-quiet-split.glb"
BLEND = ROOT / "source/blender/playroom-quiet-split.blend"
PREVIEW = ROOT / "source/previews/playroom-quiet-split-preview.png"
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


# The playroom's shared faded palette; names carry the game's soft / fabric / plastic words.
CREAM = material("Cream soft fabric", srgb(226, 212, 182), .95)
CORAL = material("Faded coral fabric", srgb(196, 128, 112), .95)
SKY = material("Faded sky fabric", srgb(161, 186, 202), .95)
BLUE = material("Dull blue soft vinyl", srgb(112, 138, 160), .86)
WOOD = material("Pale sealed wood", srgb(186, 150, 110), .7)
GREEN = material("Meadow green plastic", srgb(146, 160, 118), .42)


def node(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    return obj


def finish(obj, parent, mat, loc=(0, 0, 0), angle=0, soft=False):
    obj.parent = parent
    obj.data.materials.append(mat)
    obj.location, obj.rotation_euler = loc, (0, 0, angle)
    obj["soft"] = soft
    return obj


def mesh(parent, name, verts, faces, mat, loc=(0, 0, 0), angle=0, soft=False):
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
    return finish(obj, parent, mat, loc, angle, soft)


def bevel(obj, width, segments=3):
    mod = obj.modifiers.new("Soft edge", "BEVEL")
    mod.width, mod.segments, mod.limit_method = width, segments, "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def soft_box(parent, name, centre, size, mat, radius, loc=(0, 0, 0), angle=0, tilt=(0, 0)):
    """A rounded box placed in a local frame (loc, angle), so whole pieces of furniture can be turned."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre, rotation=(tilt[0], tilt[1], 0))
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.name = name
    finish(obj, parent, mat, loc, angle)
    return bevel(obj, min(radius, min(size) * .45))


def rod(parent, name, a, b, radius, mat, loc=(0, 0, 0), angle=0):
    direction = Vector(b) - Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=radius, depth=direction.length, location=(Vector(a) + Vector(b)) / 2)
    obj = bpy.context.object
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
    obj.name = name
    return finish(obj, parent, mat, loc, angle)


def blob(parent, name, centre, radii, mat, loc=(0, 0, 0), angle=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=7, radius=1, location=centre)
    obj = bpy.context.object
    obj.scale = radii
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
    obj.name = name
    return finish(obj, parent, mat, loc, angle, soft=True)


def slab(parent, name, outline, y0, y1, mat, loc=(0, 0, 0), angle=0):
    """An outline in the local XZ plane, given thickness along local Y."""
    n = len(outline)
    verts = [(x, y0, z) for x, z in outline] + [(x, y1, z) for x, z in outline]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh(parent, name, verts, faces, mat, loc, angle)


def arched(width, z0, z1, rise, steps=10):
    return [(-width / 2, z0), (width / 2, z0)] + [(width / 2 - i / steps * width, z1 + rise * math.sin(i / steps * math.pi)) for i in range(steps + 1)]


def bed(parent, x, y, angle, fabric):
    """A low child's bed for the 3.6 m traveler: wooden frame and headboard, soft mattress, draped duvet, pillow."""
    at = dict(loc=(x, y, 0), angle=angle)
    soft_box(parent, "Bed frame", (0, 0, .17), (3.9, 2.15, .3), WOOD, .06, **at)  # 2 cm off the floor: only the headboard sinks
    slab(parent, "Bed headboard", arched(2.35, SINK, 1.0, .3), -.08, .08, WOOD, loc=(x + math.cos(angle) * -1.95, y + math.sin(angle) * -1.95, 0), angle=angle + math.pi / 2)
    soft_box(parent, "Mattress", (0, 0, .45), (3.7, 1.95, .38), CREAM if fabric is not CREAM else SKY, .16, **at)
    blob(parent, "Pillow", (-1.2, 0, .74), (.42, .7, .15), CREAM, **at)
    rows = []
    for i in range(12):
        u = -.6 + i * .21
        wave = .05 * math.sin(u * 6.3 + x)
        profile = ((-1.1 - wave, .3 + .06 * math.sin(u * 5 + x)), (-1.06, .55), (-.98, .68), (-.6, .72), (0, .74), (.6, .72), (.98, .68), (1.06, .55), (1.1 + wave, .3 + .06 * math.cos(u * 4.4 + x)))
        rows.append([(u, py, pz + (.025 * math.sin(u * 3 + py * 4) if pz > .6 else 0)) for py, pz in profile])
    columns = len(rows[0])
    verts = [p for row in rows for p in row]
    faces = [(i * columns + j, i * columns + j + 1, (i + 1) * columns + j + 1, (i + 1) * columns + j) for i in range(len(rows) - 1) for j in range(columns - 1)]
    duvet = mesh(parent, "Draped duvet", verts, faces, fabric, soft=True, **at)
    mod = duvet.modifiers.new("Cloth thickness", "SOLIDIFY")
    mod.thickness, mod.offset = .06, 0
    bpy.context.view_layer.objects.active = duvet
    bpy.ops.object.modifier_apply(modifier=mod.name)


# NapRoomSet: two beds turned slightly towards each other and a folding-mat pile on the left; on the right a curved
# soft screen half hides the last bed, set apart and turned away, so it reads as something to find.
nap = node("NapRoomSet")
bed(nap, -7.4, -1.6, .12, SKY)
bed(nap, -4.0, 1.3, -.2, CORAL)
for i, (dx, dy, turn) in enumerate(((0, 0, .03), (.12, -.08, -.04), (.05, .1, .06))):
    for p in range(3):
        px = -9.0 + (p - 1) * 1.25 + dx
        if i == 2 and p == 2:
            soft_box(nap, "Folded mat panel", (px - .25, 2.6 + dy, .25 + i * .24 + .45), (1.2, 1.5, .22), [BLUE, CORAL, CREAM][i], .09, tilt=(0, math.radians(-55)))
            continue
        soft_box(nap, "Folding mat panel", (px, 2.6 + dy, .1 + i * .24), (1.2, 1.5, .22), [BLUE, CORAL, CREAM][i], .09)
screen = []
for i in range(25):
    a, top = math.radians(150 + i * 2.7), 1.45 + .12 * math.sin(i * .9)
    screen.append([(9.0 + (3.6 + u) * math.cos(a), -.2 + (3.6 + u) * math.sin(a), z) for u, z in ((-.13, SINK), (.13, SINK), (.13, top), (0, top + .17), (-.13, top))])
n = len(screen[0])
verts = [p for ring in screen for p in ring]
faces = [(i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j) for i in range(len(screen) - 1) for j in range(n)]
faces += [tuple(range(n)), tuple(range((len(screen) - 1) * n, len(screen) * n))]
mesh(nap, "Curved soft screen", verts, faces, BLUE)
bed(nap, 8.9, .6, 1.75, CREAM)                                      # the last bed, apart behind the screen and turned

# BirthdayRoomSet: a rounded table under a scalloped cloth with a tiered cake, six chairs each turned to face the cake,
# a party arch over the aisle, and a heap of soft gift cushions on the other side.
party = node("BirthdayRoomSet")
CX, CY = -6.2, -.4
cloth = [(CX + (2.6 if math.cos(a) > 0 else -2.6) + 1.15 * math.cos(a), CY + 1.15 * math.sin(a)) for a in (k / 40 * math.tau for k in range(40))]
verts = [(x, y, z) for z in (1.12, 1.24) for x, y in cloth]
faces = [tuple(range(39, -1, -1)), tuple(range(40, 80))] + [(k, (k + 1) % 40, 40 + (k + 1) % 40, 40 + k) for k in range(40)]
mesh(party, "Cloth table top", verts, faces, CREAM)
rows = [[(CX + (2.6 if math.cos(a) > 0 else -2.6) + r * math.cos(a), CY + r * math.sin(a), z(k)) for k, a in enumerate(k / 40 * math.tau for k in range(40))]
        for r, z in ((1.18, lambda k: 1.2), (1.25, lambda k: .72 + .1 * abs(math.sin(k * math.pi / 4))))]
verts = [p for row in rows for p in row]
faces = [(k, (k + 1) % 40, 40 + (k + 1) % 40, 40 + k) for k in range(40)]
skirt = mesh(party, "Scalloped skirt", verts, faces, CORAL, soft=True)
mod = skirt.modifiers.new("Cloth thickness", "SOLIDIFY")
mod.thickness, mod.offset = .04, 0
bpy.context.view_layer.objects.active = skirt
bpy.ops.object.modifier_apply(modifier=mod.name)
for lx in (-2.2, 2.2):
    for ly in (-.6, .6):
        rod(party, "Table leg", (CX + lx, CY + ly, SINK), (CX + lx, CY + ly, 1.13), .08, WOOD)
for name, radius, depth, z, mat in (("Cake base", .55, .42, 1.46, CREAM), ("Cake top", .38, .3, 1.81, CORAL)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=depth, location=(CX, CY, z))
    bpy.ops.object.transform_apply(location=True)
    bevel(finish(bpy.context.object, party, mat), .04, 2).name = name
for k in range(5):
    a = k / 5 * math.tau
    rod(party, "Candle", (CX + .2 * math.cos(a), CY + .2 * math.sin(a), 1.95), (CX + .2 * math.cos(a), CY + .2 * math.sin(a), 2.22), .035, CREAM)
for x, y, colour in ((-8.0, -2.35, GREEN), (-5.6, -2.45, CORAL), (-4.4, 1.55, GREEN), (-7.1, 1.6, BLUE), (-9.7, -.2, CORAL), (-2.6, -.6, BLUE)):
    turn = math.atan2(CY - y, CX - x)                               # local +X faces the cake
    at = dict(loc=(x, y, 0), angle=turn)
    soft_box(party, "Chair seat", (0, 0, .7), (.95, .95, .16), colour, .07, **at)
    slab(party, "Chair back", arched(.95, .74, 1.38, .16), -.07, .07, colour, loc=(x - .46 * math.cos(turn), y - .46 * math.sin(turn), 0), angle=turn + math.pi / 2)
    for dx in (-.36, .36):
        for dy in (-.36, .36):
            rod(party, "Chair leg", (dx, dy, SINK), (dx, dy, .64), .045, WOOD, **at)
inner, outer = 4.4, 4.95
arch = [(outer * math.cos(t), outer * math.sin(t)) for t in (i / 24 * math.pi for i in range(25))] + [(inner * math.cos(t), inner * math.sin(t)) for t in (math.pi - i / 24 * math.pi for i in range(25))]
arch[0], arch[24], arch[25], arch[49] = (outer, SINK), (-outer, SINK), (-inner, SINK), (inner, SINK)
bevel(slab(party, "Party arch", arch, -.28, .28, CORAL, loc=(0, -2.2, 0)), .1)
for i in range(1, 10):
    t = i / 10 * math.pi
    c, s = math.cos(t), math.sin(t)
    flag = [(inner * c - .2 * s, inner * s + .2 * c), (inner * c + .2 * s, inner * s - .2 * c), ((inner - .35) * c, (inner - .35) * s)]
    slab(party, "Bunting flag", flag, -.03, .03, [CREAM, SKY, GREEN][i % 3], loc=(0, -2.2, 0))
for x, y, z, size, mat, turn in ((6.4, -1.2, .45, (1.5, 1.4, .9), SKY, .2), (7.9, -.6, .4, (1.2, 1.2, .8), CORAL, -.3), (6.9, -.9, 1.32, (1.0, .9, .7), CREAM, .5),
                                 (8.6, 1.6, .35, (1.0, 1.0, .7), BLUE, .1), (5.8, 1.4, .3, (.8, .8, .6), CORAL, -.6)):
    soft_box(party, "Gift cushion", (0, 0, z), size, mat, .14, loc=(x, y, 0), angle=turn)
    rod(party, "Gift ribbon", (-size[0] / 2 - .02, 0, z + size[2] / 2 - .02), (size[0] / 2 + .02, 0, z + size[2] / 2 - .02), .05, CREAM, loc=(x, y, 0), angle=turn)

MODULES = (nap, party)


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
            edge.smooth = obj.get("soft") or (len(edge.link_faces) == 2 and edge.calc_face_angle(0) <= math.radians(40))
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
assert triangles <= 14_600 and len(bpy.data.materials) <= 6, (triangles, len(bpy.data.materials))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_materials="EXPORT")
print(f"ASSET_CHECK: {GLB.name}: {triangles} triangles, {len(bpy.data.materials)} materials")
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

# Preview: each set from a three-quarter view and from a traveler's eye height, with a 3.6 m figure for scale.
scene = bpy.context.scene
floor = bpy.data.objects.new("Preview floor", bpy.data.meshes.new("Preview floor"))
floor.data.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
floor.data.materials.append(material("Preview floor", (.06, .26, .31), .98))
scene.collection.objects.link(floor)
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=.45, depth=3.6, location=(-.8, -3.4, 1.8))
figure = bpy.context.object
figure.data.materials.append(material("Preview figure", (.5, .2, .15), .8))
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
shots = [(nap, (3, -14, 9), (0, .5, .6)), (nap, (1.5, -7.5, 4.2), (3, 1, .8)), (party, (-3, -14, 9), (0, 0, .8)), (party, (2.5, -8, 4.6), (-5, 0, 1.2))]
tiles = []
for parent, eye, target in shots:
    for other in MODULES:
        for obj in meshes(other):
            obj.hide_render = other is not parent
    camera.location = eye
    camera.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEW.parent / f".quiet-tile-{len(tiles)}.png")
    bpy.ops.render.render(write_still=True)
    tiles.append(scene.render.filepath)
sheet = np.zeros((1100, 1400, 4), dtype=np.float32)
for index, path in enumerate(tiles):
    image = bpy.data.images.load(path)
    row = 1 - index // 2
    sheet[row * 550:(row + 1) * 550, (index % 2) * 700:(index % 2 + 1) * 700] = np.array(image.pixels[:], dtype=np.float32).reshape(550, 700, 4)
    bpy.data.images.remove(image)
    Path(path).unlink()
overview = bpy.data.images.new("Playroom quiet split overview", 1400, 1100, alpha=True)
overview.pixels = sheet.ravel()
overview.filepath_raw, overview.file_format = str(PREVIEW), "PNG"
overview.save()

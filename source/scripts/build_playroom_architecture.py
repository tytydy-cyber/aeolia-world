"""Build the playroom architecture kit: arch passage, cloud niche, wave soffit with light cove, padded column.

Run: Blender --background --python source/scripts/build_playroom_architecture.py
Each module is a root node at the origin of the GLB, fetched with getObjectByName: ArchPassage, CloudNiche,
WaveSoffit, PaddedColumn (no spaces, since GLTFLoader rewrites spaces in node names). Blender -Y is the front,
which is +Z in three.js. Floor modules stand on y=0; the soffit hangs down from y=0 with its top 5 cm above it.
"""
from pathlib import Path
from mathutils import Vector
import bmesh
import bpy
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GLB = ROOT / "outputs/assets/playroom/playroom-architecture.glb"
BLEND = ROOT / "source/blender/playroom-architecture.blend"
PREVIEW = ROOT / "source/previews/playroom-architecture-preview.png"
bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, color, rough, metal=0, emit=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emit
    return mat


# Names carry the surface class the game groups by (soft / fabric / wall, plastic, steel).
FABRIC = material("Soft padded fabric", (.70, .29, .23), .95)
PAINT = material("Painted wall plaster", (.84, .80, .70), .82)
RECESS = material("Shadowed wall recess", (.10, .18, .24), .9)
PLASTIC = material("Glossy plastic trim", (.83, .60, .16), .42)
STEEL = material("Brushed steel channel", (.62, .64, .63), .34, .85)
LIGHT = material("Warm light diffuser", (1.0, .86, .62), .5, emit=3)


def module(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    return obj


def mesh(parent, name, verts, faces, mat, recalc=True):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(data)
        bm.free()
    return obj


def face_outward(obj, face, axis, sign):
    """Open shells cannot be recalculated reliably; flip the whole shell if a known face points the wrong way."""
    data = obj.data
    if data.polygons[face].normal[axis] * sign < 0:
        bm = bmesh.new()
        bm.from_mesh(data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(data)
        bm.free()


def bevel(obj, width, segments=3):
    mod = obj.modifiers.new("Rounded edge", "BEVEL")
    mod.width, mod.segments, mod.limit_method = width, segments, "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def loft(parent, name, rings, mat, caps=True):
    """Rings of equal length joined into a closed tube; caps close the two ends."""
    count = len(rings[0])
    verts = [p for ring in rings for p in ring]
    faces = [(i * count + j, i * count + (j + 1) % count, (i + 1) * count + (j + 1) % count, (i + 1) * count + j)
             for i in range(len(rings) - 1) for j in range(count)]
    if caps:
        faces += [tuple(range(count)), tuple(range((len(rings) - 1) * count, len(rings) * count))]
    return mesh(parent, name, verts, faces, mat)


def extrude_xz(parent, name, outline, y0, y1, mat):
    count = len(outline)
    verts = [(x, y0, z) for x, z in outline] + [(x, y1, z) for x, z in outline]
    faces = [tuple(range(count)), tuple(range(count, count * 2))]
    faces += [(i, (i + 1) % count, count + (i + 1) % count, count + i) for i in range(count)]
    return mesh(parent, name, verts, faces, mat)


def pipe(parent, name, points, radius, mat, cyclic=False):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth, curve.bevel_resolution, curve.use_fill_caps = radius, 2, True
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return obj


def soft_box(parent, name, loc, size, mat, radius=.12):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.name, obj.parent = name, parent
    obj.data.materials.append(mat)
    return bevel(obj, radius, 3)


# 1. Arch passage: a 1.4 m thick wall with an 8 m wide, 6 m high basket arch, padded jamb feet and rolled trim.
arch = module("ArchPassage")
outline = [(4.0, 0), (5.6, 0)]
for i in range(9):
    a = i / 8 * math.pi / 2
    outline.append((4.0 + 1.6 * math.cos(a), 5.8 + 1.6 * math.sin(a)))
for i in range(9):
    a = math.pi / 2 + i / 8 * math.pi / 2
    outline.append((-4.0 + 1.6 * math.cos(a), 5.8 + 1.6 * math.sin(a)))
outline += [(-5.6, 0), (-4.0, 0)]
opening = [(-4.0, 1.2 * i) for i in range(3)]
opening += [(4.0 * math.cos(math.pi - i / 24 * math.pi), 3.6 + 2.4 * math.sin(math.pi - i / 24 * math.pi)) for i in range(25)]
opening += [(4.0, 3.6 - 1.2 * i) for i in range(1, 4)]
bevel(extrude_xz(arch, "Arch wall", outline + opening[1:-1], -.7, .7, PAINT), .16)
for y in (-.72, .72):
    pipe(arch, "Rolled arch trim", [(x, y, z) for x, z in opening], .17, PLASTIC)
    for x in (-4.85, 4.85):
        soft_box(arch, "Padded jamb foot", (x, math.copysign(.83, y), .74), (1.3, .36, 1.44), FABRIC)

# 2. Cloud niche: a 1 m deep wall block with a scalloped cloud recess that narrows towards a dark back.
niche = module("CloudNiche")
N, cx, cz = 72, 0, 2.55
outer_f, inner_f, inner_b, outer_b = [], [], [], []
for k in range(N):
    t = k / N * math.tau
    c, s = math.cos(t), math.sin(t)
    sx, sz = math.copysign(abs(c) ** (1 / 3), c), math.copysign(abs(s) ** (1 / 3), s)
    lobes = 1 + (.115 + .055 * s) * abs(math.sin(3.5 * t))  # big lobes on top, small ones below, no step at the sides
    for loop, y in ((outer_f, -1.0), (outer_b, 0)):
        loop.append((3.6 * sx, y, 2.5 + 2.5 * sz))
    inner_f.append((cx + 2.45 * lobes * c, -1.0, cz + 1.5 * lobes * s))
    inner_b.append((cx + 2.0 * lobes * c, -.28, cz + .12 + 1.22 * lobes * s))
frame_faces = [(k, (k + 1) % N, N + (k + 1) % N, N + k) for k in range(N)]          # front ring: outer to inner
frame_faces += [(k, 2 * N + k, 2 * N + (k + 1) % N, (k + 1) % N) for k in range(N)]  # outer sides to the back
frame_faces.append(tuple(range(3 * N - 1, 2 * N - 1, -1)))                          # flat back on the wall
frame = mesh(niche, "Niche wall block", outer_f + inner_f + outer_b, frame_faces, PAINT, recalc=False)
face_outward(frame, 0, 1, -1)
recess_faces = [(k, N + k, N + (k + 1) % N, (k + 1) % N) for k in range(N)]
recess_faces.append(tuple(range(2 * N - 1, N - 1, -1)))
recess = mesh(niche, "Niche recess", inner_f + inner_b, recess_faces, RECESS, recalc=False)
face_outward(recess, N, 1, -1)
pipe(niche, "Cloud rim", [(x, y - .02, z) for x, y, z in inner_f], .13, PLASTIC, cyclic=True)
soft_box(niche, "Niche seat cushion", (0, -.62, 1.2), (2.6, .9, .5), FABRIC, .14)

# 3. Wave soffit: a 12 m ceiling drop whose depth and underside both undulate, with a lipped indirect light cove.
soffit = module("WaveSoffit")
paint_rings, steel_rings, light_rings = [], [], []
for i in range(61):
    x = -6 + i * .2
    d = 2.4 + .45 * math.sin(math.tau * x / 5.5)
    drop = 1.3 + .25 * math.sin(math.tau * x / 4 + 1)
    profile = [(0, .05), (0, -drop), (-d + .4, -drop), (-d + .1, -drop + .1), (-d, -drop + .4), (-d, -.45),
               (-d + .16, -.45), (-d + .16, -.62), (-d + .75, -.62), (-d + .75, .05)]
    channel = [(-d + .19, -.4), (-d + .22, -.4), (-d + .22, -.56), (-d + .69, -.56), (-d + .69, -.4), (-d + .72, -.4),
               (-d + .72, -.59), (-d + .19, -.59)]
    # The glowing strip lines the back of the cove so it shows through the slot above the lip from below.
    strip = [(-d + .70, -.36), (-d + .74, -.36), (-d + .74, -.12), (-d + .70, -.12)]
    for rings, points in ((paint_rings, profile), (steel_rings, channel), (light_rings, strip)):
        rings.append([(x, y, z) for y, z in points])
loft(soffit, "Soffit body", paint_rings, PAINT)
loft(soffit, "Cove channel", steel_rings, STEEL)
loft(soffit, "Cove light strip", light_rings, LIGHT)

# 4. Padded column: an off-centre, twisting cushion stack between a plastic boot and collar on a steel foot plate.
column = module("PaddedColumn")
SEG = 28


def section(z, scale, pads=True):
    t = (z - .45) / 1.02
    pad = 1 + .08 * math.sin(math.pi * (t % 1)) ** .6 if pads and 0 < t < 5 else 1
    lean = .09 * math.sin(z * .9)
    ring = []
    for j in range(SEG):
        a = j / SEG * math.tau
        r = scale * pad * (1 + .16 * math.cos(a - .5 * z) + .07 * math.cos(2 * a + 1.3))
        ring.append((lean + r * math.cos(a), r * .86 * math.sin(a), z))
    return ring


loft(column, "Column cushions", [section(.45 + i * 5.1 / 40, .6) for i in range(41)], FABRIC)
loft(column, "Column boot", [section(z, s, False) for z, s in ((.03, .74), (.3, .72), (.55, .66))], PLASTIC)
loft(column, "Column collar", [section(z, s, False) for z, s in ((5.45, .66), (5.75, .72), (6.0, .78))], PLASTIC)
loft(column, "Foot plate", [[(x * 1.12, y * 1.12, z) for x, y, _ in section(0, .76, False)] for z in (0, .06)], STEEL)

MODULES = (arch, niche, soffit, column)


def meshes(parent):
    return [obj for obj in parent.children_recursive if obj.type == "MESH"]


def smooth(obj, angle=math.radians(38)):
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
assert triangles <= 30_000 and len(bpy.data.materials) <= 6, (triangles, len(bpy.data.materials))
GLB.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_materials="EXPORT")
print(f"ASSET_CHECK: {GLB.name}: {triangles} triangles, {len(bpy.data.materials)} materials")


# 2×2 overview: each module alone, framed to its bounds, from a 10–25 m game-like three-quarter view.
def bounds(parent):
    points = [obj.matrix_world @ Vector(c) for obj in meshes(parent) for c in obj.bound_box]
    return Vector([min(p[i] for p in points) for i in range(3)]), Vector([max(p[i] for p in points) for i in range(3)])


scene = bpy.context.scene
floor = bpy.data.objects.new("Preview floor", bpy.data.meshes.new("Preview floor"))
floor.data.from_pydata([(-60, -60, -.01), (60, -60, -.01), (60, 60, -.01), (-60, 60, -.01)], [], [(0, 1, 2, 3)])
floor.data.materials.append(material("Preview carpet", (.06, .26, .31), .98))
scene.collection.objects.link(floor)
ceiling = bpy.data.objects.new("Preview ceiling", bpy.data.meshes.new("Preview ceiling"))
ceiling.data.from_pydata([(-8, -5, .04), (-8, 2, .04), (8, 2, .04), (8, -5, .04)], [], [(0, 1, 2, 3)])
ceiling.data.materials.append(material("Preview ceiling", (.55, .6, .62), .95))
scene.collection.objects.link(ceiling)
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
views = {arch: (.5, -1, .45), niche: (.45, -1, .3), soffit: (.5, -1, -.3), column: (.6, -1, .35)}
tiles = []
for parent in MODULES:
    for other in MODULES:
        for obj in meshes(other):
            obj.hide_render = other is not parent
    floor.hide_render, ceiling.hide_render = parent is soffit, parent is not soffit
    # The soffit is seen from below, so its tile is lit from below the ceiling.
    sun.rotation_euler = (math.radians(128 if parent is soffit else 50), 0, math.radians(-30))
    low, high = bounds(parent)
    centre, radius = (low + high) / 2, (high - low).length / 2
    direction = Vector(views[parent]).normalized()
    camera.location = centre + direction * radius * 2.6
    camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEW.parent / f".arch-tile-{len(tiles)}.png")
    bpy.ops.render.render(write_still=True)
    tiles.append(scene.render.filepath)
sheet = np.zeros((1100, 1400, 4), dtype=np.float32)
for index, path in enumerate(tiles):
    image = bpy.data.images.load(path)
    row = 1 - index // 2
    sheet[row * 550:(row + 1) * 550, (index % 2) * 700:(index % 2 + 1) * 700] = np.array(image.pixels[:], dtype=np.float32).reshape(550, 700, 4)
    bpy.data.images.remove(image)
    Path(path).unlink()
overview = bpy.data.images.new("Playroom architecture overview", 1400, 1100, alpha=True)
overview.pixels = sheet.ravel()
overview.filepath_raw, overview.file_format = str(PREVIEW), "PNG"
overview.save()
for obj in bpy.data.objects:
    obj.hide_render = False
bpy.data.objects.remove(floor)
bpy.data.objects.remove(ceiling)
bpy.data.objects.remove(camera)
bpy.data.objects.remove(sun)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

"""Build the deep-room kit: a cloud-edged ceiling cove, a soft wall alcove and a hanging cloud cluster.

Run: Blender --background --python source/scripts/build_playroom_deep_room_kit.py
Root nodes (getObjectByName): CloudCeilingCove, SoftWallAlcove, HangingCloudCluster. Metres; front is +Z in three.js.
- CloudCeilingCove and HangingCloudCluster hang from their origin, which goes on the ceiling: their tops are at
  y=+0.05, so they sink 5 cm into it. The cove drops at most 1.3 m and the cluster at most 6.4 m, so under the 16–20 m
  ceilings nothing reaches the 3.6 m walkway zone.
- SoftWallAlcove stands on the floor with its back on a wall: bottom at y=-0.01, back at z=-0.01.
"""
from pathlib import Path
from mathutils import Vector
import bmesh
import bpy
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GLB = ROOT / "outputs/assets/playroom/playroom-deep-room-kit.glb"
BLEND = ROOT / "source/blender/playroom-deep-room-kit.blend"
PREVIEW = ROOT / "source/previews/playroom-deep-room-kit-preview.png"
bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb(r, g, b):
    return tuple((c / 255) ** 2.2 for c in (r, g, b))


def material(name, color, rough, emit=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emit
    return mat


# Faded sky, cream, dull blue and faded coral only; names carry the game's wall / soft / cloud words.
SKY = material("Faded sky wall plaster", srgb(161, 186, 202), .9)
CREAM = material("Cream soft padding", srgb(226, 212, 182), .92)
BLUE = material("Dull blue wall recess", srgb(112, 138, 160), .9)
CORAL = material("Faded coral soft cloud", srgb(196, 128, 112), .93)
LIGHT = material("Cream light diffuser", srgb(226, 212, 182), .5, emit=2.5)


def module(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    return obj


def mesh(parent, name, verts, faces, materials, indices=None, soft=False, recalc=True):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    for mat in materials:
        data.materials.append(mat)
    if indices:
        data.polygons.foreach_set("material_index", indices)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        face.smooth = True
    for edge in bm.edges:
        edge.smooth = soft or (len(edge.link_faces) == 2 and edge.calc_face_angle(0) <= math.radians(40))
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    return obj


def loft(parent, name, rings, materials, index_for=lambda j: 0):
    count = len(rings[0])
    verts = [p for ring in rings for p in ring]
    faces, indices = [], []
    for i in range(len(rings) - 1):
        for j in range(count):
            faces.append((i * count + j, i * count + (j + 1) % count, (i + 1) * count + (j + 1) % count, (i + 1) * count + j))
            indices.append(index_for(j))
    faces += [tuple(range(count)), tuple(range((len(rings) - 1) * count, len(rings) * count))]
    indices += [index_for(0)] * 2
    return mesh(parent, name, verts, faces, materials, indices)


def blob(parent, name, loc, radii, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=10, radius=1, location=loc)
    obj = bpy.context.object
    obj.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.name, obj.parent = name, parent
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def rod(parent, name, top, bottom, radius, mat):
    """A round rod between two points (cords, anchors)."""
    direction = Vector(top) - Vector(bottom)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=radius, depth=direction.length, location=(Vector(top) + Vector(bottom)) / 2)
    obj = bpy.context.object
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    obj.name, obj.parent = name, parent
    obj.data.materials.append(mat)
    return obj


# 1. CloudCeilingCove: a 16 m ceiling edge whose front swells into cloud lobes in plan and whose underside puffs
# down under each lobe. A lip hides a cream light strip in a trough against the ceiling. The back sits 1 cm into the wall.
cove = module("CloudCeilingCove")
rings, light = [], []
for i in range(161):
    x = -8 + i * .1
    lobe = abs(math.sin(math.pi * (x + 8) / 2.3 + .3 * math.sin(x * .7))) ** .6
    d = 1.35 + .55 * lobe + .12 * math.sin(x * .45)
    drop = .95 + .2 * lobe
    profile = [(.01, .05), (.01, -drop + .1), (-.35 * d, -drop - .04), (-.72 * d, -drop - .06), (-d + .14, -drop + .06),
               (-d, -drop + .32), (-d, -.42), (-d + .14, -.42), (-d + .14, -.64), (-d + .62, -.64), (-d + .62, .05)]
    rings.append([(x, y, z) for y, z in profile])
    light.append([(x, y, z) for y, z in ((-d + .57, -.4), (-d + .61, -.4), (-d + .61, -.14), (-d + .57, -.14))])
loft(cove, "Cloud cove body", rings, [SKY, CREAM], lambda j: 1 if 1 <= j <= 4 else 0)  # cream puffy underside
loft(cove, "Cove light strip", light, [LIGHT])

# 2. SoftWallAlcove: a 7.5 m wide, 1.6 m deep wall block with a closed, asymmetric soft-arched recess 1.25 m deep
# whose top rises to the right. The recess narrows towards its back and is lined in dull blue; a cream roll frames it.
alcove = module("SoftWallAlcove")
N, CZ = 80, 2.6
outer_f, inner_f, inner_b, outer_b = [], [], [], []
for k in range(N):
    t = k / N * math.tau
    c, s = math.cos(t), math.sin(t)
    sx, sz = math.copysign(abs(c) ** (1 / 3), c), math.copysign(abs(s) ** (1 / 3), s)
    wave = .18 * math.sin(3 * t + .8) * max(s, 0)                        # soft, uneven top edge
    for loop, y in ((outer_f, -1.6), (outer_b, .01)):
        loop.append((3.75 * sx - .2 * max(s, 0) * c, y, CZ + (2.61 + wave) * sz if s > 0 else CZ + 2.61 * sz))
    ix, iz = (c, s) if s > 0 else (math.copysign(abs(c) ** .5, c), -abs(s) ** (1 / 3))  # round arched top, square-ish sill
    top = 1.0 + .7 * (c + 1) / 2                                         # recess top higher on the right
    for loop, y, shrink in ((inner_f, -1.6, 1.0), (inner_b, -.35, .86)):
        loop.append((-.3 + 2.4 * shrink * ix, y, CZ - .1 + (top * shrink * iz if s > 0 else 2.38 * iz * (1 if shrink == 1 else .97))))
frame_faces = [(k, (k + 1) % N, N + (k + 1) % N, N + k) for k in range(N)]
frame_faces += [(k, 2 * N + k, 2 * N + (k + 1) % N, (k + 1) % N) for k in range(N)]
frame_faces.append(tuple(range(3 * N - 1, 2 * N - 1, -1)))
recess_faces = [(k, N + k, N + (k + 1) % N, (k + 1) % N) for k in range(N)]
recess_faces.append(tuple(range(2 * N - 1, N - 1, -1)))
frame = mesh(alcove, "Alcove wall block", outer_f + inner_f + outer_b, frame_faces, [SKY], recalc=False)
recess = mesh(alcove, "Alcove recess", inner_f + inner_b, recess_faces, [BLUE], recalc=False)
for obj, face in ((frame, 0), (recess, N)):                              # front ring and recess back face the viewer
    if obj.data.polygons[face].normal.y > 0:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(obj.data)
        bm.free()
curve = bpy.data.curves.new("Alcove roll", "CURVE")
curve.dimensions, curve.bevel_depth, curve.bevel_resolution = "3D", .11, 2
spline = curve.splines.new("POLY")
spline.points.add(N - 1)
for point, (x, y, z) in zip(spline.points, inner_f):
    point.co = (x, y - .02, max(z, .12), 1)
spline.use_cyclic_u = True
roll = bpy.data.objects.new("Alcove roll", curve)
bpy.context.collection.objects.link(roll)
roll.parent = alcove
roll.data.materials.append(CREAM)
bpy.context.view_layer.objects.active = roll
bpy.ops.object.select_all(action="DESELECT")
roll.select_set(True)
bpy.ops.object.convert(target="MESH")

# 3. HangingCloudCluster: four solid clouds at different heights, each a cluster of overlapping puffs so it reads
# thick from every side, hung on cream cords from small ceiling roses.
cluster = module("HangingCloudCluster")
CLOUDS = (((-1.6, .6, -2.6), 1.0, CREAM), ((1.4, -.4, -3.7), 1.25, SKY), ((-.2, -1.2, -4.6), .9, CORAL), ((.9, 1.3, -5.4), .8, CREAM))
PUFFS = ((0, 0, 0, 1.0, .62, .6), (-.85, .1, -.08, .7, .5, .48), (.9, -.08, -.1, .75, .52, .5),
         (.3, .25, .32, .6, .45, .45), (-.35, -.2, .28, .5, .4, .4), (.05, .1, -.3, .85, .55, .35))
for index, ((cx, cy, cz), size, mat) in enumerate(CLOUDS, 1):
    parts = [blob(cluster, f"Cloud {index}", (cx + dx * size, cy + dy * size * (1 if index % 2 else -1), cz + dz * size),
                  (rx * size, ry * size, rz * size), mat) for dx, dy, dz, rx, ry, rz in PUFFS]
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    parts[0].name = parts[0].data.name = f"Cloud {index}"
    top = cz + (.32 + .45) * size
    rod(cluster, "Hanging cord", (cx, cy, -.08), (cx, cy, top - .15), .025, CREAM)
    rod(cluster, "Ceiling rose", (cx, cy, .05), (cx, cy, -.1), .22, CREAM)

MODULES = (cove, alcove, cluster)


def meshes(parent):
    return [obj for obj in parent.children_recursive if obj.type == "MESH"]


for parent in MODULES:
    for obj in meshes(parent):
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        if not obj.name.startswith("Cloud"):
            obj.name = obj.data.name = f"{parent.name} — {obj.name}"
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


# Preview: each module in its setting (cove under a ceiling against a wall, alcove on a wall, cluster from below).
def bounds(objects):
    points = [obj.matrix_world @ Vector(c) for obj in objects for c in obj.bound_box]
    return Vector([min(p[i] for p in points) for i in range(3)]), Vector([max(p[i] for p in points) for i in range(3)])


scene = bpy.context.scene
props = []
for name, verts, mat in (("Preview floor", [(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)], (.06, .26, .31)),
                         ("Preview wall", [(-40, .02, -20), (40, .02, -20), (40, .02, 20), (-40, .02, 20)], (.36, .45, .5)),
                         ("Preview ceiling", [(-40, -40, .01), (40, -40, .01), (40, 40, .01), (-40, 40, .01)], (.6, .62, .62))):
    obj = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    obj.data.from_pydata(verts, [], [(0, 1, 2, 3)])
    obj.data.materials.append(material(name, mat, .95))
    scene.collection.objects.link(obj)
    props.append(obj)
floor, wall, ceiling = props
camera = bpy.data.objects.new("Preview camera", bpy.data.cameras.new("Preview camera"))
scene.collection.objects.link(camera)
camera.data.lens = 32
sun = bpy.data.objects.new("Preview key", bpy.data.lights.new("Preview key", "SUN"))
scene.collection.objects.link(sun)
sun.data.energy = 3.0
scene.world = bpy.data.worlds.new("Preview world")
scene.world.color = (.42, .46, .47)
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 700, 550
scene.render.image_settings.file_format = "PNG"
scene.view_settings.look = "AgX - Medium High Contrast"
shots = [(cove, (.45, -1, -.45), 1.5, (wall, ceiling), 125), (alcove, (.35, -1, .3), 2.2, (wall, floor), 50),
         (cluster, (.5, -1, -.35), 2.4, (), 125), (cluster, (-.6, -1, .1), 2.6, (), 60)]
tiles = []
for parent, direction, distance, shown_props, sun_angle in shots:
    for obj in [o for m in MODULES for o in meshes(m)] + props:
        obj.hide_render = not (obj in meshes(parent) or obj in shown_props)
    sun.rotation_euler = (math.radians(sun_angle), 0, math.radians(-30))
    low, high = bounds(meshes(parent))
    centre, size = (low + high) / 2, (high - low).length / 2
    direction = Vector(direction).normalized()
    camera.location = centre + direction * size * distance
    camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEW.parent / f".deep-tile-{len(tiles)}.png")
    bpy.ops.render.render(write_still=True)
    tiles.append(scene.render.filepath)
sheet = np.zeros((1100, 1400, 4), dtype=np.float32)
for index, path in enumerate(tiles):
    image = bpy.data.images.load(path)
    row = 1 - index // 2
    sheet[row * 550:(row + 1) * 550, (index % 2) * 700:(index % 2 + 1) * 700] = np.array(image.pixels[:], dtype=np.float32).reshape(550, 700, 4)
    bpy.data.images.remove(image)
    Path(path).unlink()
overview = bpy.data.images.new("Playroom deep room overview", 1400, 1100, alpha=True)
overview.pixels = sheet.ravel()
overview.filepath_raw, overview.file_format = str(PREVIEW), "PNG"
overview.save()

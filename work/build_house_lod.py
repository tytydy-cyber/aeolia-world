"""Build the low-detail Aeolia house (LOD) with Blender 4.3.

Keeps the silhouette and facade rhythm of work/build_house.py: pitched slate roof,
chimney, eight arched windows with shutters, door, balcony and corner quoins.
Drops individual slates, louvers, brick courses, bevels and climbing plants.
Four material batches whose names match the game's texture lookup in aeolia.html.
Glass, door recess and ironwork share the wood batch and are darkened by vertex color.
"""
import bpy
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'assets'
MAX_TRIANGLES = 5000
MAX_BATCHES = 4


def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def import_reference():
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(OUT / 'aeolia-house.glb'))
    return [o for o in bpy.context.scene.objects if o not in before and o.type == 'MESH']


def bounds(objects):
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    return (Vector([min(p[i] for p in points) for i in range(3)]),
            Vector([max(p[i] for p in points) for i in range(3)]))


clear()
reference_min, reference_max = bounds(import_reference())
clear()


def material(name, color, rough=.8, vertex_color=False):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    # Look nodes up by type: their names are localized when Blender's UI language is not English.
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    if vertex_color:
        attribute = m.node_tree.nodes.new('ShaderNodeVertexColor')
        attribute.layer_name = 'Col'
        mix = m.node_tree.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        socket = lambda sockets, key: next(x for x in sockets if x.identifier == key)
        socket(mix.inputs, 'Factor_Float').default_value = 1
        socket(mix.inputs, 'A_Color').default_value = (*color, 1)
        m.node_tree.links.new(attribute.outputs['Color'], socket(mix.inputs, 'B_Color'))
        m.node_tree.links.new(socket(mix.outputs, 'Result_Color'), bsdf.inputs['Base Color'])
    return m


plaster = material('Warm lime plaster', (.73, .67, .53))
stone = material('Carved limestone', (.62, .56, .44))
slate = material('Slate roof', (.08, .19, .22), .72)
wood = material('Aged chestnut shutters', (.19, .10, .055), .85, vertex_color=True)
DARK = (.03, .04, .045, 1)
LIGHT = (1, 1, 1, 1)
parts = []


def finish(obj, name, mat, shade=LIGHT):
    obj.name = name
    obj.data.materials.append(mat)
    if mat is wood:
        attribute = obj.data.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
        for value in attribute.data:
            value.color = shade
        obj.data.color_attributes.active_color = attribute
    parts.append(obj)
    return obj


def box(name, loc, size, mat, rotation=None, shade=LIGHT):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rotation:
        obj.rotation_euler = rotation
    return finish(obj, name, mat, shade)


def polygon(name, verts, faces, mat, facing, shade=LIGHT):
    # Wind every face so its normal points along `facing`.
    oriented = []
    for face in faces:
        a, b, c = (Vector(verts[i]) for i in face[:3])
        oriented.append(face if (b - a).cross(c - a).dot(Vector(facing)) > 0 else tuple(reversed(face)))
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], oriented)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    return finish(obj, name, mat, shade)


# Body, plinth and horizontal bands.
box('Lime rendered walls', (0, 0, 5.5), (12, 10, 11), plaster)
box('Foundation', (0, 0, .25), (12.3, 10.3, .5), stone)
box('First floor string course', (0, 0, 5.2), (12.25, 10.25, .22), stone)
box('Deep eaves cornice', (0, 0, 10.9), (12.5, 10.5, .25), stone)
box('Stone base moulding', (0, 0, .86), (12.15, 10.15, .5), stone)
for sx in [-1, 1]:
    for sy in [-1, 1]:
        for row in range(7):
            wide = row % 2
            box('Corner quoin', (sx * 5.98, sy * 4.98, 1.775 + row * 1.3),
                (1.05 if wide else .65, .65 if wide else 1.05, 1.12), stone)

# Gables and a pitched roof made of two slabs with a few slate course ribs.
for sy in [-1, 1]:
    polygon('Gable', [(-6, sy * 5, 11), (6, sy * 5, 11), (0, sy * 5, 14.6)], [(0, 1, 2)], plaster, (0, sy, 0))
half, rise = 6.65, 3.6
slope = math.atan2(rise, half)
for side in [-1, 1]:
    box('Roof slab', (side * half / 2, 0, 12.8 + .12), (math.hypot(half, rise), 11.5, .3), slate, (0, side * slope, 0))
    for t in [.25, .5, .75]:
        box('Slate course', (side * half * t, 0, 14.6 - rise * t + .32), (.12, 11.5, .1), slate, (0, side * slope, 0))
    box('Rain gutter', (side * 6.64, 0, 10.98), (.18, 11.7, .18), wood, shade=DARK)
box('Ridge cap', (0, 0, 14.7), (.4, 11.6, .26), slate)

box('Chimney stack', (3.8, 2.4, 13.7), (1.15, 1.2, 4.5), stone)
box('Chimney cap', (3.8, 2.4, 15.95), (1.45, 1.5, .25), stone)


def window(cx, sy, z, shutters=True):
    yy = sy * 5.03
    radius = .88
    coords = [(cx - radius, yy, z), (cx + radius, yy, z), (cx + radius, yy, z + 1.55)]
    coords += [(cx + math.cos(a) * radius, yy, z + 1.55 + math.sin(a) * radius) for a in [i * math.pi / 8 for i in range(1, 9)]]
    polygon('Recessed arched glass', coords, [tuple(range(len(coords)))], wood, (0, sy, 0), DARK)
    for side in [-1, 1]:
        box('Window jamb', (cx + side * 1.01, yy + sy * .06, z + .78), (.22, .24, 1.65), stone)
    for i in range(7):
        a = (i + .5) * math.pi / 7
        box('Arch stone', (cx + math.cos(a) * 1.01, yy + sy * .06, z + 1.55 + math.sin(a) * 1.01), (.42, .25, .26), stone, (0, math.pi / 2 - a, 0))
    box('Window sill', (cx, yy + sy * .16, z - .05), (2.4, .65, .18), stone)
    box('Glass mullion', (cx, yy + sy * .04, z + .95), (.065, .10, 1.9), stone)
    box('Glass transom', (cx, yy + sy * .04, z + .95), (1.76, .10, .065), stone)
    for side in [-1, 1] if shutters else []:
        box('Shutter', (cx + side * 1.59, yy, z + .9), (.8, .15, 1.95), wood)


for sy in [-1, 1]:
    for xx in [-3.35, 3.35]:
        for zz in [2, 7]:
            window(xx, sy, zz)
# The balcony window's shutters would sit coplanar with its neighbours' and flicker.
window(0, -1, 7, shutters=False)

# Door, frame and step.
box('Doorway shadow', (0, -5.07, 1.8), (2.45, .12, 3.6), wood, shade=DARK)
box('Oak door', (0, -5.17, 1.68), (2.16, .12, 3.24), wood)
for zz in [.55, 2.5]:
    box('Door iron strap', (0, -5.25, zz), (2.1, .05, .07), wood, shade=DARK)
for sx in [-1, 1]:
    box('Door pilaster', (sx * 1.32, -5.12, 1.8), (.28, .4, 3.6), stone)
box('Carved lintel', (0, -5.15, 3.65), (2.95, .5, .35), stone)
box('Door step', (0, -5.36, .15), (2.8, .6, .3), stone)

# Balcony with corbels and a sparse railing.
box('Balcony slab', (0, -5.62, 6.75), (3.6, 1.2, .25), stone)
for xx in [-1.45, 1.45]:
    box('Balcony corbel', (xx, -5.42, 6.3), (.35, .7, .7), stone)
for i in range(8):
    box('Balcony baluster', (-1.7 + i * 3.4 / 7, -6.17, 7.38), (.07, .07, 1.15), wood, shade=DARK)
box('Balcony handrail', (0, -6.17, 7.98), (3.6, .10, .10), wood, shade=DARK)

# Every part must touch another part: nothing floats away from the house.
def part_bounds(obj):
    return bounds([obj])


boxes = [part_bounds(o) for o in parts]
for i, (lo, hi) in enumerate(boxes):
    touching = any(all(lo[k] <= other_hi[k] + .05 and other_lo[k] <= hi[k] + .05 for k in range(3))
                   for j, (other_lo, other_hi) in enumerate(boxes) if j != i)
    assert touching, f'Floating part: {parts[i].name}'

# Merge by material, matching the full-detail asset's batching.
groups = {}
for obj in parts:
    groups.setdefault(obj.data.materials[0].name, []).append(obj)
for name, objects in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    bpy.context.object.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

models = [o for o in bpy.context.scene.objects if o.type == 'MESH']
triangles = 0
for obj in models:
    obj.data.calc_loop_triangles()
    triangles += len(obj.data.loop_triangles)
    assert len(obj.data.materials) == 1, f'{obj.name} must stay a single material batch'
    assert obj.data.materials[0].diffuse_color[3] == 1, f'{obj.name} must be opaque'
assert len(models) <= MAX_BATCHES, f'Material batch budget exceeded: {len(models)}'
assert triangles <= MAX_TRIANGLES, f'Triangle budget exceeded: {triangles}'

lod_min, lod_max = bounds(models)
for k, axis in enumerate('xyz'):
    assert abs(lod_min[k] - reference_min[k]) < .35 and abs(lod_max[k] - reference_max[k]) < .35, \
        f'{axis} bounds drift: LOD {lod_min[k]:.2f}..{lod_max[k]:.2f}, full {reference_min[k]:.2f}..{reference_max[k]:.2f}'

# Every surface visible from outside must face the viewer: rays from four sides and above.
depsgraph = bpy.context.evaluated_depsgraph_get()
rays = []
for lateral in range(-55, 56, 5):
    for height in range(5, 160, 5):
        x, z = lateral / 10, height / 10
        rays += [((x, -30, z), (0, 1, 0)), ((x, 30, z), (0, -1, 0)), ((-30, x * .9, z), (1, 0, 0)), ((30, x * .9, z), (-1, 0, 0))]
for x in range(-60, 61, 5):
    for y in range(-50, 51, 5):
        rays.append(((x / 10, y / 10, 40), (0, 0, -1)))
hits = backfaces = 0
for origin, direction in rays:
    hit, _, normal, _, obj, _ = bpy.context.scene.ray_cast(depsgraph, Vector(origin), Vector(direction))
    if hit:
        hits += 1
        backfaces += normal.dot(Vector(direction)) > 0
assert hits > 1000 and backfaces == 0, f'Back-facing surfaces visible from outside: {backfaces}/{hits}'
print(f'ASSET_CHECK: {len(models)} material batches; {triangles} triangles; {hits} outside rays, 0 back faces; '
      f'bounds {tuple(round(v, 2) for v in lod_min)}..{tuple(round(v, 2) for v in lod_max)}')

bpy.ops.object.select_all(action='DESELECT')
for obj in models:
    obj.select_set(True)
export = dict(filepath=str(OUT / 'aeolia-house-lod.glb'), export_format='GLB', use_selection=True,
              export_apply=True, export_animations=False)
try:
    bpy.ops.export_scene.gltf(**export, export_vertex_color='ACTIVE')
except TypeError:
    bpy.ops.export_scene.gltf(**export, export_colors=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'aeolia-house-lod.blend'))

# Side-by-side preview: full-detail asset on the left, LOD on the right.
for obj in models:
    obj.location.x += 8
for obj in import_reference():
    obj.location.x -= 8
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.world.use_nodes = True
background = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
background.inputs[0].default_value = (.47, .6, .72, 1)
background.inputs[1].default_value = .45
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.04))
bpy.context.object.data.materials.append(material('Preview floor', (.32, .36, .33)))
bpy.ops.object.light_add(type='SUN', location=(0, 0, 30))
bpy.context.object.data.energy = 3.5
bpy.context.object.rotation_euler = (math.radians(50), 0, math.radians(-35))
bpy.ops.object.camera_add(location=(18, -40, 24))
camera = bpy.context.object
camera.rotation_euler = (Vector((0, 0, 7)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 36
scene.camera = camera
scene.render.resolution_x, scene.render.resolution_y = 1200, 640
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT / 'house-lod-preview.png')
bpy.ops.render.render(write_still=True)

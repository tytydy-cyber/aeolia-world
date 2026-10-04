"""Build the first feasible asset kit for the dreamcore playroom world.

Exports three independent GLBs plus one editable Blender source and a neutral preview render:
rainbow arch, slide tower, and a lightweight ball pit. Geometry is deliberately modest enough
for the browser game; repeated balls are joined by material and can later be instanced in Three.js.
"""
import bpy
import math
import random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'assets' / 'playroom'
SOURCE = ROOT / 'source'
OUT.mkdir(parents=True, exist_ok=True)
(SOURCE / 'blender').mkdir(parents=True, exist_ok=True)
(SOURCE / 'previews').mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def material(name, color, rough=.78):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    return m


RED = material('Faded red plastic', (.68, .09, .055), .62)
ORANGE = material('Faded orange paint', (.86, .29, .055))
YELLOW = material('Faded yellow plastic', (.92, .63, .07), .66)
GREEN = material('Faded green plastic', (.055, .43, .19), .67)
BLUE = material('Faded blue plastic', (.035, .22, .58), .64)
DARK_BLUE = material('Blue steel', (.025, .11, .3), .5)
CREAM = material('Soft wall padding', (.72, .67, .5), .92)
PIT = material('Ball pit rim', (.72, .16, .12), .76)
FLOOR = material('Ball pit floor', (.21, .43, .49), .9)
BALL_MATS = [RED, YELLOW, GREEN, BLUE]


def add_to(root, obj, mat=None):
    if mat:
        obj.data.materials.append(mat)
    obj.parent = root
    return obj


def cube(root, name, loc, size, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    add_to(root, o, mat)
    if bevel:
        mod = o.modifiers.new('Soft manufactured edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return o


def cylinder(root, name, loc, radius, depth, mat, vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    add_to(root, o, mat)
    return o


def empty(name, x):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location.x = x
    return o


def arch_mesh(name, inner, outer, depth, segments=24):
    verts = []
    for y in (-depth / 2, depth / 2):
        for r in (inner, outer):
            for i in range(segments + 1):
                a = math.pi - i / segments * math.pi
                verts.append((math.cos(a) * r, y, math.sin(a) * r))
    faces = []
    row = segments + 1
    for side in range(2):
        base = side * row * 2
        for i in range(segments):
            faces.append((base + i, base + i + 1, base + row + i + 1, base + row + i))
    for ring in range(2):
        a = ring * row
        b = row * 2 + ring * row
        for i in range(segments):
            faces.append((a + i, b + i, b + i + 1, a + i + 1))
    for i in (0, segments):
        faces.append((i, row + i, row * 3 + i, row * 2 + i))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


# Rainbow arch: five separate paint bands and padded bases. It is a gateway, not a flat decal.
rainbow = empty('Rainbow arch', -11)
for i, mat in enumerate((RED, ORANGE, YELLOW, GREEN, BLUE)):
    inner = 3.7 + i * .48
    o = bpy.data.objects.new(f'Rainbow band {i + 1}', arch_mesh(f'Rainbow band {i + 1}', inner, inner + .52, 1.0))
    bpy.context.collection.objects.link(o)
    add_to(rainbow, o, mat)
for x in (-5.95, 5.95):
    cube(rainbow, 'Padded arch base', (x, 0, .65), (1.35, 1.35, 1.3), CREAM, .14)


# Slide tower: modular boxes/cylinders and one genuinely curved, modestly tessellated slide.
slide = empty('Slide tower', 1.5)
for x in (-1.4, 1.4):
    for y in (-1.05, 1.05):
        cylinder(slide, 'Tower post', (x, y, 2.25), .11, 4.5, DARK_BLUE)
cube(slide, 'Platform', (0, 0, 2.6), (3.2, 2.5, .24), YELLOW, .08)
cube(slide, 'Rear panel', (0, 1.08, 3.45), (2.7, .12, 1.55), GREEN, .08)
for x in (-1.45, 1.45):
    cube(slide, 'Roof support', (x, 0, 4.25), (.16, .16, 2.0), DARK_BLUE)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.35, radius2=0, depth=1.15, location=(0, 0, 5.58), rotation=(0, 0, math.pi / 4))
roof = bpy.context.object
roof.name = 'Simple pyramid roof'
add_to(slide, roof, RED)
for z in (.55, 1.05, 1.55, 2.05):
    cube(slide, 'Ladder step', (-1.65, 1.45, z), (1.1, .16, .12), YELLOW, .03)
for x in (-2.15, -1.15):
    cylinder(slide, 'Ladder rail', (x, 1.45, 1.35), .07, 2.7, DARK_BLUE, 10)


def slide_mesh():
    segments, width, thick = 18, 1.55, .10
    verts = []
    centres = []
    for i in range(segments + 1):
        t = i / segments
        # Starts nearly level at the deck, becomes steeper, then flattens onto the floor.
        x = 1.35 + t * 4.6
        z = .22 + 2.5 * (1 - t) ** 2
        centres.append(Vector((x, -1.15, z)))
    for i, c in enumerate(centres):
        tangent = (centres[min(i + 1, segments)] - centres[max(i - 1, 0)]).normalized()
        normal = Vector((-tangent.z, 0, tangent.x)).normalized()
        for y in (-width / 2, width / 2):
            for d in (0, -thick):
                p = c + normal * d + Vector((0, y, 0))
                verts.append(tuple(p))
    faces = []
    for i in range(segments):
        a, b = i * 4, (i + 1) * 4
        faces.extend(((a, b, b + 2, a + 2), (a + 1, a + 3, b + 3, b + 1),
                      (a, a + 1, b + 1, b), (a + 2, b + 2, b + 3, a + 3)))
    faces.extend(((0, 2, 3, 1), (segments * 4, segments * 4 + 1, segments * 4 + 3, segments * 4 + 2)))
    mesh = bpy.data.meshes.new('Curved slide')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


slide_surface = bpy.data.objects.new('Curved slide', slide_mesh())
bpy.context.collection.objects.link(slide_surface)
add_to(slide, slide_surface, RED)


def slide_lip_mesh(name, y):
    segments, half_width, height = 18, .06, .18
    verts = []
    for i in range(segments + 1):
        t = i / segments
        x = 1.35 + t * 4.6
        z = .22 + 2.5 * (1 - t) ** 2
        verts.extend(((x, y - half_width, z), (x, y + half_width, z),
                      (x, y - half_width, z + height), (x, y + half_width, z + height)))
    faces = []
    for i in range(segments):
        a, b = i * 4, (i + 1) * 4
        faces.extend(((a, b, b + 2, a + 2), (a + 1, a + 3, b + 3, b + 1),
                      (a + 2, b + 2, b + 3, a + 3)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


for y in (-1.15 - .775, -1.15 + .775):
    lip = bpy.data.objects.new('Curved slide edge', slide_lip_mesh('Curved slide edge', y))
    bpy.context.collection.objects.link(lip)
    add_to(slide, lip, RED)


# Ball pit: solid low rim, flat coloured base, and a sparse top layer joined into four material batches.
pit = empty('Ball pit', 12.5)
cube(pit, 'Pit floor', (0, 0, .08), (7.2, 5.2, .16), FLOOR, .10)
for loc, size in [((0, -2.55, .48), (7.6, .45, .95)), ((0, 2.55, .48), (7.6, .45, .95)),
                  ((-3.55, 0, .48), (.45, 4.7, .95)), ((3.55, 0, .48), (.45, 4.7, .95))]:
    cube(pit, 'Padded pit rim', loc, size, PIT, .16)
random.seed(8)
balls = [[] for _ in BALL_MATS]
for i in range(56):
    x, y = random.uniform(-3.15, 3.15), random.uniform(-2.1, 2.1)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=.22, location=(x, y, .27 + random.uniform(0, .13)))
    o = bpy.context.object
    o.name = f'Ball {i:02d}'
    for polygon in o.data.polygons:
        polygon.use_smooth = True
    o.data.materials.append(BALL_MATS[i % 4])
    balls[i % 4].append(o)
for index, group in enumerate(balls):
    bpy.ops.object.select_all(action='DESELECT')
    for o in group:
        o.select_set(True)
    bpy.context.view_layer.objects.active = group[0]
    bpy.ops.object.join()
    group[0].name = f'Ball batch {index + 1}'
    group[0].parent = pit


def descendants(root):
    return [root, *root.children_recursive]


def export(root, filename):
    preview_location = root.location.copy()
    root.location = (0, 0, 0)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in descendants(root):
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.gltf(filepath=str(OUT / filename), export_format='GLB', use_selection=True,
                              export_apply=True, export_yup=True, export_materials='EXPORT')
    root.location = preview_location
    bpy.context.view_layer.update()


export(rainbow, 'playroom-rainbow.glb')
export(slide, 'playroom-slide.glb')
export(pit, 'playroom-ball-pit.glb')

# Neutral studio preview. The floor is preview-only and not exported.
bpy.ops.mesh.primitive_plane_add(size=38, location=(1, 0, -.02))
preview_floor = bpy.context.object
preview_floor.name = 'Preview floor'
preview_floor.data.materials.append(material('Preview floor material', (.18, .21, .2), .94))
bpy.ops.object.light_add(type='AREA', location=(1, -5, 12))
bpy.context.object.data.energy = 1700
bpy.context.object.data.shape = 'DISK'
bpy.context.object.data.size = 10
bpy.ops.object.light_add(type='AREA', location=(-8, 7, 7))
bpy.context.object.data.energy = 900
bpy.context.object.data.size = 8
bpy.ops.object.camera_add(location=(1, -36, 11.5))
camera = bpy.context.object
bpy.context.scene.camera = camera
camera.data.lens = 46


def point_camera(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()


point_camera(camera, (1.5, 0, 2.1))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(SOURCE / 'previews' / 'playroom-assets-preview.png')
scene.render.film_transparent = False
scene.world.color = (.035, .045, .055)
scene.view_settings.look = 'AgX - Medium High Contrast'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / 'blender' / 'playroom-assets.blend'))
bpy.ops.render.render(write_still=True)

for root in (rainbow, slide, pit):
    tris = sum(len(o.data.loop_triangles) for o in descendants(root) if o.type == 'MESH' for _ in [o.data.calc_loop_triangles()])
    mats = {m.name for o in descendants(root) if o.type == 'MESH' for m in o.data.materials}
    print(f'ASSET_CHECK: {root.name}: {tris} triangles, {len(mats)} materials')

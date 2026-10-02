"""Build the five floating-island district modules with Blender 4.3.

One GLB with five objects, each with its origin at the centre of its footprint on the ground:
market stall set, bell-tower equipment, windmill workshop, water-garden basin edge, cloud-stop platform.
Materials are shared and named for the game's texture lookup (limestone, chestnut, ironwork) plus
'Island life atlas', whose UVs address cells of outputs/assets/textures/island-life-atlas.png.
Images are not embedded; the game assigns textures by material name, as it does for the houses.
"""
import bpy
import bmesh
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'assets'
TEX = OUT / 'textures'
MAX_TRIANGLES = 45000
MAX_BATCHES = 12
INSET = 4 / 1024

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def material(name, color, image=None, rough=.85, metal=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    # Nodes are looked up by type: their names are localized when Blender's UI is not English.
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if image:
        node = m.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(TEX / image))
        m.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
    return m


ATLAS = material('Island life atlas', (1, 1, 1), 'island-life-atlas.png')
STONE = material('Carved limestone', (.62, .56, .44), 'stone-color.jpg')
WOOD = material('Aged chestnut', (.3, .2, .12), 'wood-color.jpg')
IRON = material('Bronze ironwork', (.15, .12, .07), rough=.42, metal=.65)

# Atlas cells (see textures/GENERATED-ASSETS.md): row-major 4x4 from the top-left.
CELL = dict(awning=0, check=1, linen=2, canvas=3, lavender=4, blossom=5, crate=8, crate_brace=9,
            tools=10, boards=11, clock=12, clock_green=13, timetable=14, timetable_light=15)

MODULES = {}  # name -> {'offset': Vector, 'parts': [(obj, mat)], 'size': expected (x, y, z) maxima}


def module(name, offset, size):
    MODULES[name] = {'offset': Vector(offset), 'parts': [], 'size': size}
    return name


def add(mod, obj, mat, cell=None):
    obj.data.materials.append(mat)
    if cell is not None:
        atlas_uv(obj, CELL[cell])
    MODULES[mod]['parts'].append(obj)
    return obj


def place(mod, loc):
    return MODULES[mod]['offset'] + Vector(loc)


def box(mod, loc, size, mat, cell=None, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=place(mod, loc))
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rot:
        obj.rotation_euler = rot
    return add(mod, obj, mat, cell)


def cyl(mod, loc, radius, depth, mat, cell=None, verts=10, rot=None, radius2=None):
    if radius2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=place(mod, loc))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=radius, radius2=radius2, depth=depth, location=place(mod, loc))
    obj = bpy.context.object
    if rot:
        obj.rotation_euler = rot
    return add(mod, obj, mat, cell)


def lathe(mod, loc, profile, mat, steps=16):
    """Closed solid of revolution from an (radius, height) profile running from the top axis point to the bottom one."""
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0, z)) for r, z in profile]
    for a, b in zip(verts, verts[1:]):
        bm.edges.new((a, b))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], axis=(0, 0, 1), cent=(0, 0, 0), steps=steps, angle=math.tau)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    data = bpy.data.meshes.new('Lathe')
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new('Lathe', data)
    obj.location = place(mod, loc)
    bpy.context.collection.objects.link(obj)
    return add(mod, obj, mat)


def atlas_uv(obj, cell):
    """Project each face onto the plane facing its normal and fit it into one inset atlas cell."""
    col, row = cell % 4, cell // 4
    u0, u1 = col / 4 + INSET, (col + 1) / 4 - INSET
    v0, v1 = 1 - (row + 1) / 4 + INSET, 1 - row / 4 - INSET
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name='UVMap')
    uv = mesh.uv_layers.active.data
    co = [v.co for v in mesh.vertices]
    lo = Vector([min(c[k] for c in co) for k in range(3)])
    span = Vector([max(max(c[k] for c in co) - lo[k], 1e-6) for k in range(3)])
    for poly in mesh.polygons:
        n = poly.normal
        axis = max(range(3), key=lambda k: abs(n[k]))
        a, b = [k for k in range(3) if k != axis]
        if axis == 0:
            a, b = 1, 2
        elif axis == 1:
            a, b = 0, 2
        for li in poly.loop_indices:
            c = co[mesh.loops[li].vertex_index]
            uv[li].uv = (u0 + (c[a] - lo[a]) / span[a] * (u1 - u0), v0 + (c[b] - lo[b]) / span[b] * (v1 - v0))


# ---- Market: flower stall, tiered flower stand, harvest crates --------------------------------
m = module('Market module', (0, 0, 0), (7.2, 4.6, 3.6))
for x in (-1.7, 1.7):
    for y in (-.7, .7):
        cyl(m, (x, y, 1.45), .07, 2.9, WOOD, verts=8)
box(m, (0, 0, .95), (3.8, 1.6, .12), WOOD)
box(m, (0, -.8, .5), (3.7, .08, .9), ATLAS, 'crate')
box(m, (0, 0, 3.0), (4.3, 2.2, .1), ATLAS, 'awning', rot=(.16, 0, 0))
for i, x in enumerate((-1.2, 0, 1.2)):
    box(m, (x, .1, 1.17), (.9, .6, .32), ATLAS, 'lavender' if i % 2 else 'blossom')
# Tiered stand: three wooden steps, each with a flower tray.
for k in range(3):
    box(m, (-2.95, -.2 + k * .5, .3 + k * .45), (1.1, .5, .6 + k * .9), WOOD)
    box(m, (-2.95, -.2 + k * .5, .66 + k * .9), (.95, .4, .12), ATLAS, 'blossom' if k % 2 else 'lavender')
# Stacked harvest crates.
box(m, (2.9, -.6, .35), (.8, .7, .7), ATLAS, 'crate')
box(m, (2.9, .25, .35), (.8, .7, .7), ATLAS, 'crate_brace')
box(m, (2.95, -.2, 1.05), (.75, .65, .7), ATLAS, 'crate')

# ---- Bell tower equipment: clock face, bell frame with rope, inspection scaffold ----------------
t = module('Bell tower module', (12, 0, 0), (3.4, 3.4, 7.4))
# Inspection scaffold: four posts, two decks and a cross rail; the bell hangs above the top deck.
for x in (-1.1, 1.1):
    for y in (-1.1, 1.1):
        box(t, (x, y, 2.5), (.14, .14, 5.0), WOOD)
for z in (2.3, 4.94):
    box(t, (0, 0, z), (2.5, 2.5, .12), WOOD)
box(t, (0, -1.1, 1.2), (2.3, .08, .08), WOOD)
# Clock face mounted on a backing board across the front posts.
box(t, (0, -1.2, 3.6), (2.3, .06, 2.3), WOOD)
cyl(t, (0, -1.3, 3.6), 1.05, .14, ATLAS, 'clock', verts=24, rot=(math.pi / 2, 0, 0))
cyl(t, (0, -1.27, 3.6), 1.12, .06, IRON, verts=24, rot=(math.pi / 2, 0, 0))
# Bell frame on the top deck, bell and its rope down to the lower deck.
for x in (-.75, .75):
    box(t, (x, 0, 5.6), (.16, .16, 1.24), WOOD)
box(t, (0, 0, 6.25), (1.8, .24, .2), WOOD)
lathe(t, (0, 0, 5.14), [(0, .95), (.24, .93), (.32, .8), (.36, .55), (.44, .25), (.62, .05), (.6, 0), (0, 0)], IRON)
cyl(t, (0, 0, 6.12), .1, .1, IRON, verts=8)
cyl(t, (.45, .45, 3.65), .03, 2.6, WOOD, verts=6)

# ---- Windmill workshop: tool bench, drying-cloth frame, repair timber ----------------------------
w = module('Windmill module', (24, 0, 0), (6.6, 3.6, 3.2))
box(w, (-2, 0, .85), (2.2, 1.0, .1), WOOD)
for x in (-2.95, -1.05):
    for y in (-.4, .4):
        box(w, (x, y, .4), (.1, .1, .8), WOOD)
box(w, (-2, .55, 1.6), (2.2, .08, 1.4), ATLAS, 'tools')
box(w, (-2.3, -.1, 1.02), (.6, .4, .24), ATLAS, 'crate')
for x in (.4, 3.0):
    box(w, (x, 0, 1.4), (.12, .12, 2.8), WOOD)
box(w, (1.7, 0, 2.7), (2.7, .06, .06), WOOD)
for i, (x, cell) in enumerate(((.95, 'check'), (1.7, 'linen'), (2.45, 'canvas'))):
    box(w, (x, 0, 2.68 - (1.2 - i * .2) / 2), (.62, .03, 1.2 - i * .2), ATLAS, cell)
for k in range(4):
    box(w, (1.7, 1.25, .1 + k * .18), (2.6 - k * .3, .3, .16), WOOD)
box(w, (3.0, 1.3, .35), (.5, .5, .7), ATLAS, 'boards')

# ---- Water garden: segmented basin rim, stone benches, drain grate -------------------------------
g = module('Water garden module', (38, 0, 0), (11.4, 11.4, .9))
for i in range(16):
    a = i / 16 * math.tau
    box(g, (math.cos(a) * 5.2, math.sin(a) * 5.2, .25), (2.2, .6, .5), STONE, rot=(0, 0, a + math.pi / 2))
for a in (math.pi * .25, math.pi * 1.25):
    cx, cy = math.cos(a) * 3.4, math.sin(a) * 3.4
    box(g, (cx, cy, .45), (1.6, .5, .1), STONE, rot=(0, 0, a + math.pi / 2))
    for s in (-.55, .55):
        box(g, (cx + math.cos(a + math.pi / 2) * s, cy + math.sin(a + math.pi / 2) * s, .2), (.16, .4, .4), STONE, rot=(0, 0, a + math.pi / 2))
box(g, (0, -5.2, .52), (.8, .6, .04), IRON)
for k in range(5):
    box(g, (-.3 + k * .15, -5.2, .56), (.05, .5, .04), IRON)

# ---- Cloud stop: platform, roof, bench, single lamp, timetable -----------------------------------
s = module('Cloud stop module', (54, 0, 0), (12.4, 3.4, 3.9))
box(s, (0, 0, .4), (12, 3, .8), STONE)
box(s, (0, -1.42, .82), (12, .16, .04), STONE)
for x in (-2.4, 2.4):
    box(s, (x, .9, 2.0), (.16, .16, 2.4), WOOD)
box(s, (0, .55, 3.3), (6.2, 2.0, .14), WOOD, rot=(-.12, 0, 0))
box(s, (0, 1.05, 1.25), (2.2, .45, .08), WOOD)
for x in (-.95, .95):
    box(s, (x, 1.05, 1.0), (.1, .4, .4), WOOD)
box(s, (0, 1.25, 1.55), (2.2, .06, .5), WOOD)
box(s, (5.2, .6, 2.1), (.12, .12, 2.6), WOOD)
box(s, (5.2, .6, 3.55), (.42, .42, .3), ATLAS, 'clock')
box(s, (5.2, .6, 3.75), (.55, .55, .1), WOOD)
for x in (-4.6, -3.4):
    box(s, (x, .9, 1.4), (.1, .1, 1.2), WOOD)
box(s, (-4.0, .9, 2.25), (1.4, .06, 1.0), ATLAS, 'timetable')

# ---- Checks before merging ---------------------------------------------------------------------
def world_bounds(objects):
    pts = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    return Vector([min(p[k] for p in pts) for k in range(3)]), Vector([max(p[k] for p in pts) for k in range(3)])


bpy.context.view_layer.update()
for name, spec in MODULES.items():
    parts = spec['parts']
    boxes = [world_bounds([p]) for p in parts]
    # Every part must connect to the ground through touching parts: nothing floats.
    reached = {i for i, (lo, _) in enumerate(boxes) if lo.z < .05}
    changed = True
    while changed:
        changed = False
        for i, (lo, hi) in enumerate(boxes):
            if i in reached:
                continue
            if any(all(lo[k] <= boxes[j][1][k] + .03 and boxes[j][0][k] <= hi[k] + .03 for k in range(3)) for j in reached):
                reached.add(i)
                changed = True
    floating = [parts[i].name for i in range(len(parts)) if i not in reached]
    assert not floating, f'{name}: floating parts {floating}'

# Merge each module into one object (one primitive per material) with its origin on the ground centre.
modules = []
for name, spec in MODULES.items():
    bpy.ops.object.select_all(action='DESELECT')
    for p in spec['parts']:
        p.select_set(True)
    bpy.context.view_layer.objects.active = spec['parts'][0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.scene.cursor.location = spec['offset']
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    modules.append(obj)
bpy.context.scene.cursor.location = (0, 0, 0)
bpy.context.view_layer.update()

triangles = batches = 0
depsgraph = bpy.context.evaluated_depsgraph_get()
for obj, (name, spec) in zip(modules, MODULES.items()):
    mesh = obj.data
    mesh.calc_loop_triangles()
    tris = len(mesh.loop_triangles)
    used = {p.material_index for p in mesh.polygons}
    triangles += tris
    batches += len(used)
    # Origin sits at the footprint centre on the ground; size stays inside the module's budget.
    lo, hi = world_bounds([obj])
    local_lo, local_hi = lo - obj.location, hi - obj.location
    assert (obj.location - spec['offset']).length < 1e-4, f'{name}: origin moved'
    assert abs(local_lo.z) < .02, f'{name}: lowest point {local_lo.z:.3f} is not on the ground'
    assert abs(local_lo.x + local_hi.x) < 1.2 and abs(local_lo.y + local_hi.y) < 1.2, f'{name}: origin is off the footprint centre'
    size = local_hi - local_lo
    assert all(size[k] <= spec['size'][k] for k in range(3)) and min(size) > .3, f'{name}: size {tuple(round(v, 2) for v in size)} outside {spec["size"]}'
    # No duplicated faces (same vertex positions twice in one mesh).
    keys = [tuple(sorted(tuple(round(c, 4) for c in mesh.vertices[v].co) for v in p.vertices)) for p in mesh.polygons]
    assert len(keys) == len(set(keys)), f'{name}: duplicated faces'
    # Faces seen from outside must face the viewer: rays from four sides and above.
    rays = []
    for i in range(-20, 21):
        for j in range(1, 30):
            h = local_lo.z + (local_hi.z - local_lo.z) * (j - .5) / 29
            # Sample cell centres so no ray runs exactly along an outer face plane.
            x = obj.location.x + local_lo.x + (local_hi.x - local_lo.x) * (i + 20.5) / 41
            y = obj.location.y + local_lo.y + (local_hi.y - local_lo.y) * (i + 20.5) / 41
            rays += [((x, -40, h), (0, 1, 0)), ((x, 40, h), (0, -1, 0)), ((obj.location.x - 40, y, h), (1, 0, 0)), ((obj.location.x + 40, y, h), (-1, 0, 0))]
            rays.append(((x, y, 30), (0, 0, -1)))
    hits = back = 0
    for origin, direction in rays:
        hit, _, normal, _, target, _ = bpy.context.scene.ray_cast(depsgraph, Vector(origin), Vector(direction))
        if hit and target == obj:
            hits += 1
            back += normal.dot(Vector(direction)) > .05  # ignore rays grazing along a face
    assert hits > 100 and back == 0, f'{name}: {back}/{hits} outside rays hit back faces'
    print(f'MODULE_CHECK: {name}: {tris} triangles, {len(used)} batches, size {tuple(round(v, 2) for v in size)}, {hits} rays ok')
assert triangles <= MAX_TRIANGLES, f'Triangle budget exceeded: {triangles}'
assert batches <= MAX_BATCHES, f'Batch budget exceeded: {batches}'
print(f'ASSET_CHECK: {len(modules)} modules; {triangles} triangles; {batches} material batches')

bpy.ops.object.select_all(action='DESELECT')
for obj in modules:
    obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT / 'aeolia-island-modules.glb'), export_format='GLB', use_selection=True,
                          export_apply=True, export_animations=False, export_image_format='NONE')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'aeolia-island-modules.blend'))

# Preview from about 15 m, the middle of the 10-30 m recognition range.
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.world.use_nodes = True
background = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
background.inputs[0].default_value = (.47, .6, .72, 1)
background.inputs[1].default_value = .5
bpy.ops.mesh.primitive_plane_add(size=300, location=(27, 0, -.01))
bpy.context.object.data.materials.append(material('Preview ground', (.3, .36, .28)))
bpy.ops.object.light_add(type='SUN', location=(0, 0, 30))
bpy.context.object.data.energy = 3.5
bpy.context.object.rotation_euler = (math.radians(50), 0, math.radians(-30))
bpy.ops.object.camera_add(location=(27, -34, 16))
camera = bpy.context.object
camera.rotation_euler = (Vector((27, 0, 1.6)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 66
scene.camera = camera
scene.render.resolution_x, scene.render.resolution_y = 1600, 520
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT / 'island-modules-preview.png')
bpy.ops.render.render(write_still=True)

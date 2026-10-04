"""Build reusable low-poly modules for the remaining playroom districts."""
from pathlib import Path
from mathutils import Vector
import bpy
import math

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/assets/playroom"
SOURCE = ROOT / "source"
OUT.mkdir(parents=True, exist_ok=True)
(SOURCE / "blender").mkdir(parents=True, exist_ok=True)
(SOURCE / "previews").mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def material(name, color, rough=.76, metal=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return mat


RED = material("Sun-faded red plastic", (.62, .12, .09), .72)
YELLOW = material("Worn warm yellow plastic", (.83, .56, .08), .75)
GREEN = material("Soft green plastic", (.08, .38, .22), .76)
BLUE = material("Faded blue plastic", (.05, .25, .53), .73)
CREAM = material("Clean aged cream vinyl", (.76, .70, .57), .9)
SKY = material("Sky wallpaper face", (.35, .66, .77), .91)
CARPET = material("Matte teal carpet", (.06, .26, .31), .98)
WOOD = material("Pale sealed wood", (.58, .39, .20), .8)
STEEL = material("Painted maintenance steel", (.18, .25, .29), .58, .18)
DARK = material("Deep opening", (.025, .035, .04), .9)
WHITE = material("Warm white fabric", (.82, .80, .72), .95)
PINK = material("Faded coral fabric", (.72, .34, .34), .9)


def root(name, x):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.location.x = x
    return obj


def finish(parent, obj, name, mat, bevel=0):
    obj.name = name
    obj.data.materials.append(mat)
    obj.parent = parent
    if bevel:
        mod = obj.modifiers.new("Rounded manufactured edge", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def box(parent, name, loc, size, mat, bevel=.08, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(parent, obj, name, mat, min(bevel, min(size) * .3))


def cylinder(parent, name, loc, radius, depth, mat, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    return finish(parent, bpy.context.object, name, mat, min(.035, radius * .3, depth * .15))


def curve_pipe(parent, name, points, radius, mat, resolution=2):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_resolution = 1
    curve.bevel_depth = radius
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, point in zip(spline.bezier_points, points):
        bp.co = point
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj.select_set(False)
    return obj


def hollow_tube(parent, name, loc, length, outer, mat, segments=16):
    inner = outer - .14
    verts, faces = [], []
    for x in (-length / 2, length / 2):
        for radius in (outer, inner):
            for i in range(segments):
                angle = i * math.tau / segments
                verts.append((x + loc[0], loc[1] + math.cos(angle) * radius, loc[2] + math.sin(angle) * radius))
    for side in range(2):
        base = side * segments
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((base + i, base + j, base + segments * 2 + j, base + segments * 2 + i))
    for end in range(2):
        outer_base = end * segments * 2
        inner_base = outer_base + segments
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((outer_base + i, inner_base + i, inner_base + j, outer_base + j))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(parent, obj, name, mat)


def extruded_outline(parent, name, outline, depth, mat):
    count = len(outline)
    verts = [(x, -depth / 2, z) for x, z in outline] + [(x, depth / 2, z) for x, z in outline]
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, count + j, count + i))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(parent, obj, name, mat, .045)


def arch(parent, name, loc, inner, outer, depth, mat, segments=18):
    outline = []
    for radius, reverse in ((outer, False), (inner, True)):
        values = range(segments + 1)
        if reverse:
            values = reversed(list(values))
        for i in values:
            angle = math.pi - i / segments * math.pi
            outline.append((loc[0] + math.cos(angle) * radius, loc[2] + math.sin(angle) * radius))
    return extruded_outline(parent, name, outline, depth, mat)


# Playground: a readable, asymmetric silhouette with rounded supports, soft stairs and a traversable tube.
playground = root("Playground pack", -31)
for x, y, lean in ((-5.0, -2.2, -.18), (-4.2, 2.0, .12), (4.1, -2.0, .14), (5.2, 1.7, -.2)):
    curve_pipe(playground, "Bent padded support", [(x, y, 0), (x + lean, y, 3.2), (x + lean * .3, y, 6.4)], .18, BLUE)
box(playground, "Rounded upper deck", (-1.2, 0, 5.25), (7.7, 4.8, .4), YELLOW, .18, (0, 0, -.04))
box(playground, "Offset lower deck", (3.8, -.3, 2.8), (4.0, 3.5, .38), GREEN, .17, (0, 0, .08))
for i in range(7):
    box(playground, "Soft stair", (-6.4 + i * .72, 1.5, .35 + i * .55), (1.1, 2.35, .55), [RED, YELLOW, GREEN, BLUE][i % 4], .16, (0, 0, -.03 * i))
hollow_tube(playground, "Traversable tube", (3.4, -.2, 5.0), 8.4, 1.3, RED)
for y in (-2.35, 2.35):
    for x in [i * .72 - 3.2 for i in range(10)]:
        curve_pipe(playground, "Safety net vertical", [(x, y, 3.1), (x + .12 * math.sin(x), y, 6.25)], .018, CREAM, 1)
    for z in [3.2 + i * .52 for i in range(7)]:
        curve_pipe(playground, "Safety net horizontal", [(-3.4, y, z), (0, y, z + .08), (3.4, y, z)], .018, CREAM, 1)
arch(playground, "Cloud entry arch", (-1.0, 0, 0), 1.55, 2.05, .45, CREAM)


# Child town: three distinct low facades and lamps derived from generic late-1990s indoor play streets.
town = root("Child town pack", -8)
shops = ((-7.2, 4.8, 4.4, CREAM, RED, 1.15, 3.15),
         (-1.0, 5.8, 5.2, SKY, YELLOW, 1.5, 3.85),
         (6.0, 5.2, 4.0, WHITE, GREEN, 1.0, 2.85))
for index, (x, width, height, wall, roof, opening_z, awning_z) in enumerate(shops):
    box(town, "Low facade", (x, 0, height / 2), (width, .7, height), wall, .12)
    arch(town, "Rounded shop opening", (x, -.42, opening_z - 1.15), 1.15, 1.48, .22, roof, 14)
    box(town, "Deep shop opening", (x, -.39, opening_z), (2.1, .12, 2.3), DARK, .05)
    box(town, "Sun faded awning", (x, -.82, awning_z), (width * (.64 + index * .05), 1.0, .22), roof, .06, (math.radians(8), 0, (index - 1) * .025))
    for offset in (-width * .33, width * .33):
        box(town, "Inset display window", (x + offset, -.4, 2.0 + index * .18), (width * .18, .12, .85 + index * .12), BLUE, .035)
# Three rooflines keep the miniature street from reading as a row of boxes.
extruded_outline(town, "Gabled shop crown", [(-9.6, 4.3), (-7.2, 5.9), (-4.8, 4.3)], .76, RED)
arch(town, "Rounded shop crown", (-1.0, 0, 5.0), 2.0, 2.45, .76, YELLOW, 18)
box(town, "Stepped shop crown", (6.0, 0, 4.35), (3.2, .76, .7), GREEN, .08)
box(town, "Offset crown step", (6.65, 0, 4.92), (1.9, .76, .5), GREEN, .07)
for x, y, turn in ((-9, -3.0, .5), (2.0, -3.4, -.35), (9.3, -2.8, .65)):
    curve_pipe(town, "Curved street lamp", [(x, y, 0), (x, y, 2.8), (x + turn, y, 3.8), (x + turn * 2.2, y, 3.7)], .09, STEEL)
    cylinder(town, "Rounded lamp shade", (x + turn * 2.25, y, 3.62), .32, .28, YELLOW, 16)
box(town, "Uneven curb", (0, -2.0, .12), (20, 1.25, .24), CREAM, .1, (0, 0, -.015))


# Quiet rooms: nap and birthday modules share a pack and muted, clean but worn finishes.
quiet = root("Nap and birthday pack", 16)
for stack, (x, y) in enumerate(((-8, 2.3), (-5.5, 2.1), (-7, -1.5))):
    for i in range(3 + stack % 2):
        box(quiet, "Offset stacked mat", (x + i * .12, y - i * .08, .16 + i * .25), (3.5, 2.0, .24), [CREAM, PINK, SKY][i % 3], .12, (0, 0, (i - 1) * .035))
for index, (x, y, angle) in enumerate(((-2.5, 2.2, .02), (1.2, 2.0, -.04), (-1.0, -1.4, .05))):
    box(quiet, "Low bed mattress", (x, y, .3), (3.1, 1.75, .38), [CREAM, SKY, PINK][index], .18, (0, 0, angle))
    box(quiet, "Small pillow", (x - .92, y, .58), (.72, 1.05, .18), WHITE, .12, (0, 0, angle))
box(quiet, "Rounded long table", (7.0, .4, 1.25), (7.8, 2.15, .25), WOOD, .18)
for x in (3.9, 5.9, 8.0, 10.0):
    for y in (-1.55, 2.25):
        box(quiet, "Child chair seat", (x, y, .72), (1.0, .95, .2), [RED, YELLOW, GREEN, BLUE][int(x + y) % 4], .13)
        curve_pipe(quiet, "Child chair frame", [(x - .34, y, .05), (x - .34, y, .75), (x + .34, y, .75), (x + .34, y, .05)], .055, STEEL, 1)
arch(quiet, "Birthday decoration arch", (7.0, 0, .05), 2.6, 3.0, .32, PINK, 20)
for i in range(9):
    angle = math.pi - i * math.pi / 8
    cylinder(quiet, "Arch light", (7 + math.cos(angle) * 2.8, -.2, .05 + math.sin(angle) * 2.8), .075, .18, YELLOW, 10, (math.pi / 2, 0, 0))


# Cloud corridor: solid cloud panels, wallpaper with a visible back and exposed service structure.
corridor = root("Cloud corridor pack", 40)
cloud = [(-4.4, .4), (-4.2, 1.6), (-3.4, 2.4), (-2.2, 2.45), (-1.5, 3.35), (-.2, 3.7), (1.1, 3.3), (1.8, 2.55), (3.1, 2.35), (4.1, 1.55), (4.25, .45)]
extruded_outline(corridor, "Cloud wall panel", cloud + [(4.2, 0), (-4.3, 0)], .42, WHITE)
wall = box(corridor, "Wallpaper panel with exposed back", (7.0, .2, 3.1), (5.6, .24, 6.2), SKY, .04, (0, 0, .08))
box(corridor, "Unpainted wallpaper back", (7.0, .36, 3.1), (5.2, .08, 5.8), WOOD, .02, (0, 0, .08))
box(corridor, "Peeled wallpaper corner", (9.32, -.06, 5.5), (1.2, .06, 1.5), CREAM, .02, (0, .18, .22))
for x in (-5.0, 0, 5.0, 10.0):
    curve_pipe(corridor, "Maintenance beam", [(x, -2.2, 0), (x, -2.2, 6.8), (x + .45, 1.8, 8.0)], .14, STEEL, 1)
for z in (5.4, 7.6):
    box(corridor, "Service cross beam", (2.5, -.2, z), (16.0, .34, .34), STEEL, .04, (0, 0, .025 if z < 6 else -.02))
box(corridor, "Narrow service ledge", (2.7, 1.3, 4.3), (15.5, 1.1, .24), CREAM, .08)


PACKS = {
    playground: "playroom-playground-pack.glb",
    town: "playroom-child-town-pack.glb",
    quiet: "playroom-quiet-rooms-pack.glb",
    corridor: "playroom-cloud-corridor-pack.glb",
}


def meshes(parent):
    return [obj for obj in parent.children_recursive if obj.type == "MESH"]


def merge_by_material(parent):
    groups = {}
    for obj in meshes(parent):
        groups.setdefault(obj.data.materials[0].name, []).append(obj)
    for name, objects in groups.items():
        if len(objects) == 1:
            objects[0].name = name
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        objects[0].name = name
        objects[0].parent = parent


def export(parent, filename):
    merge_by_material(parent)
    preview_location = parent.location.copy()
    parent.location = (0, 0, 0)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    parent.select_set(True)
    for obj in meshes(parent):
        obj.select_set(True)
        obj.data.calc_loop_triangles()
    bpy.context.view_layer.objects.active = parent
    triangles = sum(len(obj.data.loop_triangles) for obj in meshes(parent))
    materials = {mat.name for obj in meshes(parent) for mat in obj.data.materials}
    assert triangles < 150_000 and len(materials) <= 10
    bpy.ops.export_scene.gltf(filepath=str(OUT / filename), export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_materials="EXPORT")
    parent.location = preview_location
    bpy.context.view_layer.update()
    print(f"ASSET_CHECK: {filename}: {triangles} triangles, {len(materials)} materials")


for pack, filename in PACKS.items():
    export(pack, filename)

# One overview render for proportion and surface checks. Preview-only floor/lights are added after export.
for pack, position in zip(PACKS, ((-13, 8, 0), (13, 8, 0), (-13, -8, 0), (13, -8, 0))):
    pack.location = position
playground.rotation_euler.z = math.radians(12)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -.08))
preview_floor = bpy.context.object
preview_floor.data.materials.append(CARPET)
bpy.ops.object.light_add(type="AREA", location=(-10, -18, 26))
bpy.context.object.data.energy = 2400
bpy.context.object.data.shape = "RECTANGLE"
bpy.context.object.data.size = 22
bpy.ops.object.light_add(type="AREA", location=(20, 12, 20))
bpy.context.object.data.energy = 1200
bpy.context.object.data.size = 12
bpy.ops.object.camera_add(location=(0, -48, 42))
camera = bpy.context.object
camera.rotation_euler = (Vector((0, 0, 3.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = 46
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1400
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(SOURCE / "previews/playroom-zone-assets-preview.png")
scene.world.color = (.055, .07, .075)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / "blender/playroom-zone-assets.blend"))
bpy.ops.render.render(write_still=True)

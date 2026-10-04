"""Build reusable low-poly modules for the remaining playroom districts."""
from pathlib import Path
from mathutils import Vector
import bmesh
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


def material(name, color, rough=.76, metal=0, coat=0, sheen=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    # Surface classes read apart without textures: plastic carries a clear coat, fabric a soft sheen.
    # Only set them where used: any non-default coat input makes the exporter emit the extension on every material.
    if coat:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = .28
    if sheen:
        bsdf.inputs["Sheen Weight"].default_value = sheen
        bsdf.inputs["Sheen Roughness"].default_value = .6
    return mat


RED = material("Sun-faded red plastic", (.62, .12, .09), .46, coat=.3)
YELLOW = material("Worn warm yellow plastic", (.83, .56, .08), .48, coat=.3)
GREEN = material("Soft green plastic", (.08, .38, .22), .48, coat=.3)
BLUE = material("Faded blue plastic", (.05, .25, .53), .46, coat=.3)
CREAM = material("Clean aged cream vinyl", (.76, .70, .57), .62, coat=.12)
SKY = material("Sky wallpaper face", (.35, .66, .77), .9)
CARPET = material("Matte teal carpet", (.06, .26, .31), .98)
WOOD = material("Pale sealed wood", (.58, .39, .20), .7)
STEEL = material("Painted maintenance steel", (.18, .25, .29), .5, .2)
DARK = material("Deep opening", (.025, .035, .04), .95)
WHITE = material("Warm white fabric", (.82, .80, .72), 1, sheen=.5)
PINK = material("Faded coral fabric", (.72, .34, .34), 1, sheen=.5)
DENIM = material("Faded blue fabric", (.22, .38, .55), 1, sheen=.5)
FOAM = material("Painted cloud foam", (.93, .92, .87), .88)


def root(name, x):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.location.x = x
    return obj


def fix_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def finish(parent, obj, name, mat, bevel=0, segments=2):
    obj.name = name
    obj.data.materials.append(mat)
    obj.parent = parent
    if bevel:
        mod = obj.modifiers.new("Rounded manufactured edge", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def mesh_object(parent, name, verts, faces, mat, bevel=0, loc=(0, 0, 0), rot=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    fix_normals(obj)
    finish(parent, obj, name, mat, bevel)
    obj.location, obj.rotation_euler = loc, rot
    return obj


def box(parent, name, loc, size, mat, bevel=.08, rotation=(0, 0, 0), segments=2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(parent, obj, name, mat, min(bevel, min(size) * .3), segments)


def cylinder(parent, name, loc, radius, depth, mat, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    bevel = min(.035, radius * .3, depth * .15)
    # A bevel under a centimetre is invisible from 10 m and only adds triangles to small lights and thin discs.
    return finish(parent, bpy.context.object, name, mat, bevel if bevel >= .01 else 0)


def lobe(parent, name, loc, radii, mat, segments=14, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=loc)
    obj = bpy.context.object
    obj.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj["soft"] = True
    return finish(parent, obj, name, mat)


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
    return mesh_object(parent, name, verts, faces, mat)


def extruded_outline(parent, name, outline, depth, mat, y=0, bevel=.045, loc=None, rot=(0, 0, 0)):
    """Outline in the XZ plane, extruded along Y."""
    count = len(outline)
    verts = [(x, y - depth / 2, z) for x, z in outline] + [(x, y + depth / 2, z) for x, z in outline]
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, count + j, count + i))
    return mesh_object(parent, name, verts, faces, mat, bevel, loc or (0, 0, 0), rot)


def prism(parent, name, outline, z0, z1, mat):
    """Outline in the XY plane, extruded along Z."""
    count = len(outline)
    verts = [(x, y, z0) for x, y in outline] + [(x, y, z1) for x, y in outline]
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, count + j, count + i))
    return mesh_object(parent, name, verts, faces, mat)


def arch(parent, name, loc, inner, outer, depth, mat, segments=18):
    outline = []
    for radius, reverse in ((outer, False), (inner, True)):
        values = range(segments + 1)
        if reverse:
            values = reversed(list(values))
        for i in values:
            angle = math.pi - i / segments * math.pi
            outline.append((loc[0] + math.cos(angle) * radius, loc[2] + math.sin(angle) * radius))
    return extruded_outline(parent, name, outline, depth, mat, loc[1])


def rounded_top(cx, width, z0, z1, rise, steps=10):
    """A slab outline with a softly arched top, used for doors, headboards and chair backs."""
    points = [(cx - width / 2, z0), (cx + width / 2, z0)]
    for i in range(steps + 1):
        t = i / steps
        points.append((cx + width / 2 - t * width, z1 + math.sin(t * math.pi) * rise))
    return points


def shell(parent, name, loc, length, radius, thick, a0, a1, mat, segments=12, rot=(0, 0, 0)):
    """A curved sheet bent around the X axis: canopies and peeled paper."""
    verts, faces = [], []
    for x in (-length / 2, length / 2):
        for k in range(segments + 1):
            angle = a0 + (a1 - a0) * k / segments
            for r in (radius, radius - thick):
                verts.append((x, -r * math.sin(angle), r * math.cos(angle)))
    idx = lambda e, k, s: e * (segments + 1) * 2 + k * 2 + s
    for k in range(segments):
        faces.append((idx(0, k, 0), idx(0, k + 1, 0), idx(1, k + 1, 0), idx(1, k, 0)))
        faces.append((idx(0, k, 1), idx(1, k, 1), idx(1, k + 1, 1), idx(0, k + 1, 1)))
        for e in range(2):
            faces.append((idx(e, k, 0), idx(e, k, 1), idx(e, k + 1, 1), idx(e, k + 1, 0)))
    for k in (0, segments):
        faces.append((idx(0, k, 0), idx(1, k, 0), idx(1, k, 1), idx(0, k, 1)))
    return mesh_object(parent, name, verts, faces, mat, loc=loc, rot=rot)


def sheet(parent, name, rows, mat, thickness=.05, cyclic=False, loc=(0, 0, 0), rot=(0, 0, 0)):
    """A draped cloth from a grid of points, given real thickness so no face is single-sided."""
    columns = len(rows[0])
    verts = [p for row in rows for p in row]
    faces = []
    for i in range(len(rows) - 1):
        for j in range(columns if cyclic else columns - 1):
            k = (j + 1) % columns
            faces.append((i * columns + j, i * columns + k, (i + 1) * columns + k, (i + 1) * columns + j))
    obj = mesh_object(parent, name, verts, faces, mat, loc=loc, rot=rot)
    mod = obj.modifiers.new("Cloth thickness", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    fix_normals(obj)
    obj["soft"] = True
    return obj


def stadium(cx, cy, half, radius, steps=12):
    points = []
    for end, sign in ((half, 1), (-half, -1)):
        for i in range(steps + 1):
            angle = -math.pi / 2 + i * math.pi / steps
            points.append((cx + end + sign * math.cos(angle) * radius, cy + sign * math.sin(angle) * radius))
    return points


def turn(x, y, cx, cy, angle):
    c, s = math.cos(angle), math.sin(angle)
    return cx + x * c - y * s, cy + x * s + y * c


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


# Child town: three shops told apart by roofline, opening and awning, not by colour alone.
# Buildings keep the collision widths 4.8 / 5.8 / 5.2 m; their front faces -Y and their bodies extend behind the storefronts.
town = root("Child town pack", -8)


def facade(x, width, height, wall):
    box(town, "Enclosed shop body", (x, 1.25, height / 2), (width, 3.2, height), wall, .12)
    box(town, "Shop foundation", (x, 1.25, .19), (width + .24, 3.5, .42), STEEL, .08)


# Bakery: steep gable with deep eaves and a chimney, arched door, striped scalloped awning.
x, w, h = -7.2, 4.8, 4.4
facade(x, w, h, CREAM)
extruded_outline(town, "Gable end wall", [(x - w / 2, h - .02), (x + w / 2, h - .02), (x, 5.75)], 3.2, CREAM, 1.25, bevel=0)
span, ridge = w / 2 + .38, 5.95
for side in (-1, 1):
    eave = (x + side * span, h - .25)
    mid = ((eave[0] + x) / 2, (eave[1] + ridge) / 2)
    run = math.hypot(span, ridge - eave[1])
    box(town, "Deep eave roof", (mid[0], 1.25, mid[1]), (run + .12, 3.8, .22), RED, .06, (0, side * math.atan2(ridge - eave[1], span), 0))
box(town, "Brick chimney", (x + 1.05, 1.65, 5.55), (.52, .52, 1.2), RED, .06)
box(town, "Chimney cap", (x + 1.05, 1.65, 6.17), (.7, .7, .1), STEEL, .03)
extruded_outline(town, "Arched door opening", rounded_top(x, 1.3, .42, 1.95, .62), .12, DARK, -.37, bevel=0)
arch(town, "Door arch trim", (x, -.43, 1.95), .66, .86, .14, RED, 12)
for side in (-1, 1):
    box(town, "Door post trim", (x + side * .76, -.43, 1.18), (.2, .14, 1.54), RED, .04)
    cylinder(town, "Round window frame", (x + side * 1.6, -.37, 2.55), .46, .08, RED, 16, (math.pi / 2, 0, 0))
    cylinder(town, "Round window glass", (x + side * 1.6, -.42, 2.55), .36, .06, BLUE, 16, (math.pi / 2, 0, 0))
for i in range(6):
    sx = x - 1.25 + i * .5
    stripe = RED if i % 2 == 0 else CREAM
    box(town, "Striped awning", (sx, -.8, 2.95), (.48, 1.0, .07), stripe, .02, (math.radians(22), 0, 0))
    cylinder(town, "Awning scallop", (sx, -1.27, 2.72), .22, .06, stripe, 12, (math.pi / 2, 0, 0))

# Toy shop: a solid half-sun crown with a ringed rim, a columned wide shopfront and a barrel canopy.
x, w, h = -1.0, 5.8, 5.2
facade(x, w, h, SKY)
crown = [(x + math.cos(math.pi - i * math.pi / 18) * 2.3, h - .02 + math.sin(math.pi - i * math.pi / 18) * 2.3) for i in range(19)]
extruded_outline(town, "Half sun crown", crown, 3.2, YELLOW, 1.25, bevel=0)
arch(town, "Ringed crown rim", (x, 1.25, h - .02), 2.3, 2.58, 3.25, RED, 18)
box(town, "Shop sign band", (x, -.42, h - .62), (w * .78, .16, .56), BLUE, .05)
box(town, "Wide shopfront", (x, -.37, 1.7), (3.4, .12, 2.6), DARK, .03)
box(town, "Shopfront lintel", (x, -.47, 3.12), (4.2, .34, .3), CREAM, .06)
for side in (-1, 1):
    cylinder(town, "Shopfront column", (x + side * 1.92, -.5, 1.6), .17, 2.9, CREAM, 12)
shell(town, "Barrel canopy", (x, -.36, 2.72), 4.5, .92, .08, 0, math.pi / 2, YELLOW, 10)

# Kiosk: wooden body, a lookout tower on one side, crenellated parapet, off-centre door and a serving hatch.
x, w, h = 6.0, 5.2, 4.0
facade(x, w, h, WOOD)
box(town, "Lookout tower", (x - 1.7, 1.25, h + .84), (1.7, 3.0, 1.72), WOOD, .08)
box(town, "Tower cap", (x - 1.7, 1.25, h + 1.79), (2.0, 3.25, .22), GREEN, .06)
cylinder(town, "Tower round window", (x - 1.7, -.42, h + .9), .34, .06, BLUE, 16, (math.pi / 2, 0, 0))
for i in range(4):
    box(town, "Parapet merlon", (x - .35 + i * .82, 1.25, h + .2), (.52, 3.0, .44), GREEN, .05)
box(town, "Narrow side door", (x - 1.65, -.37, 1.42), (.95, .12, 2.4), DARK, .03)
box(town, "Serving hatch", (x + 1.0, -.37, 1.95), (2.2, .12, 1.15), DARK, .03)
box(town, "Hatch counter", (x + 1.0, -.62, 1.32), (2.5, .58, .12), GREEN, .04)
box(town, "Flat hatch awning", (x + 1.0, -.95, 2.88), (2.8, 1.25, .14), GREEN, .05, (math.radians(-8), 0, 0))
for side in (-1, 1):
    curve_pipe(town, "Awning brace", [(x + 1.0 + side * 1.15, -.36, 2.25), (x + 1.0 + side * 1.15, -1.35, 2.86)], .04, STEEL, 1)

for x, y, bend in ((-9, -3.0, .5), (2.0, -3.4, -.35), (9.3, -2.8, .65)):
    curve_pipe(town, "Curved street lamp", [(x, y, 0), (x, y, 2.8), (x + bend, y, 3.8), (x + bend * 2.2, y, 3.7)], .09, STEEL)
    cylinder(town, "Rounded lamp shade", (x + bend * 2.25, y, 3.62), .32, .28, YELLOW, 16)
box(town, "Uneven curb", (0, -2.0, .12), (20, 1.25, .24), CREAM, .1, (0, 0, -.015))


# Quiet rooms: nap and birthday modules. Bedding is soft and draped; vinyl mats fold; the table wears a cloth.
quiet = root("Nap and birthday pack", 16)
for stack, (x, y) in enumerate(((-8, 2.3), (-5.5, 2.1), (-7, -1.5))):
    layers = 3 + stack % 2
    for i in range(layers):
        z, colour = .15 + i * .28, [BLUE, RED, CREAM][(i + stack) % 3]
        for p in range(3):
            px, py = turn(-1.17 + p * 1.17, 0, x + i * .12, y - i * .08, (i - 1) * .035)
            if stack == 0 and i == layers - 1 and p == 2:
                # The top mat of one stack is half folded up, breaking the flat pile silhouette.
                box(quiet, "Folded mat panel", (px - .2, py, z + .42), (1.12, 2.0, .26), colour, .1, (0, math.radians(-58), (i - 1) * .035))
                continue
            box(quiet, "Folding mat panel", (px, py, z), (1.12, 2.0, .26), colour, .1, (0, 0, (i - 1) * .035))
for index, (x, y, angle) in enumerate(((-2.5, 2.2, .02), (1.2, 2.0, -.04), (-1.0, -1.4, .05))):
    fabric = [WHITE, DENIM, PINK][index]
    box(quiet, "Low bed frame", (x, y, .07), (3.35, 1.95, .14), WOOD, .05, (0, 0, angle))
    hx, hy = turn(-1.64, 0, x, y, angle)
    extruded_outline(quiet, "Bed headboard", rounded_top(0, 1.95, 0, .78, .26), .12, WOOD, loc=(hx, hy, 0), rot=(0, 0, angle + math.pi / 2))
    box(quiet, "Puffy mattress", (x, y, .3), (3.1, 1.75, .36), WHITE if fabric is not WHITE else CREAM, .15, (0, 0, angle), 4)
    px, py = turn(-.98, 0, x, y, angle)
    pillow = lobe(quiet, "Soft pillow", (px, py, .6), (.34, .56, .13), WHITE, 12, 6)
    pillow.rotation_euler.z = angle
    rows = []
    for i in range(13):
        u = -.5 + i * .175
        side = .045 * math.sin(u * 7.3 + index)
        profile = ((-.98 - side, .16 + .05 * math.sin(u * 6 + index)), (-.94, .4), (-.87, .52), (-.6, .56), (-.3, .58), (0, .59), (.3, .58), (.6, .56), (.87, .52), (.94, .4), (.98 + side, .16 + .05 * math.cos(u * 5.6 + index)))
        rows.append([(u, py_, pz + (.022 * math.sin(u * 3.1 + py_ * 4) if .3 < pz else 0)) for py_, pz in profile])
    sheet(quiet, "Draped duvet", rows, fabric, .05, loc=(x, y, 0), rot=(0, 0, angle))
    rx, ry = turn(-.52, 0, x, y, angle)
    cylinder(quiet, "Folded duvet edge", (rx, ry, .6), .085, 1.96, fabric, 10, (math.pi / 2, 0, angle))

# Birthday seat: a rounded table under a scalloped cloth, a tiered cake, chairs with backs and a bunting arch.
cloth = stadium(7.0, .4, 2.85, 1.12)
prism(quiet, "Cloth covered table top", cloth, 1.12, 1.38, WHITE)
skirt_top, skirt_hem = stadium(7.0, .4, 2.85, 1.16, 18), stadium(7.0, .4, 2.85, 1.22, 18)
sheet(quiet, "Scalloped table skirt", [[(px, py, 1.3) for px, py in skirt_top],
                                        [(px, py, .74 + .1 * abs(math.sin(j * math.pi / 3))) for j, (px, py) in enumerate(skirt_hem)]], PINK, .04, True)
for lx in (4.6, 9.4):
    for ly in (-.25, 1.05):
        cylinder(quiet, "Table leg", (lx, ly, .56), .08, 1.12, WOOD, 10)
cylinder(quiet, "Cake base tier", (7.0, .4, 1.55), .44, .34, WHITE, 18)
cylinder(quiet, "Cake top tier", (7.0, .4, 1.82), .29, .22, PINK, 16)
for i in range(3):
    angle = i * math.tau / 3
    cylinder(quiet, "Cake candle", (7.0 + math.cos(angle) * .14, .4 + math.sin(angle) * .14, 2.02), .03, .2, YELLOW, 6)
for x in (3.9, 5.9, 8.0, 10.0):
    for y in (-1.55, 2.25):
        seat = [RED, YELLOW, GREEN, BLUE][int(x + y) % 4]
        box(quiet, "Child chair seat", (x, y, .72), (1.0, .95, .2), seat, .13)
        curve_pipe(quiet, "Child chair frame", [(x - .34, y, .05), (x - .34, y, .75), (x + .34, y, .75), (x + .34, y, .05)], .055, STEEL, 1)
        extruded_outline(quiet, "Child chair back", rounded_top(x, .86, .78, 1.3, .16, 8), .12, seat, y + (.42 if y > 0 else -.42), bevel=0)
arch(quiet, "Birthday decoration arch", (7.0, 0, .05), 2.6, 3.0, .32, PINK, 20)
for i in range(9):
    angle = math.pi - i * math.pi / 8
    cylinder(quiet, "Arch light", (7 + math.cos(angle) * 2.8, -.2, .05 + math.sin(angle) * 2.8), .075, .18, YELLOW, 10, (math.pi / 2, 0, 0))
for i in range(1, 11):
    angle = math.pi * i / 11
    c, s = math.cos(angle), math.sin(angle)
    flag = [(7 + c * 2.62 - s * .17, .05 + s * 2.62 + c * .17), (7 + c * 2.62 + s * .17, .05 + s * 2.62 - c * .17), (7 + c * 2.2, .05 + s * 2.2)]
    extruded_outline(quiet, "Bunting flag", flag, .03, [PINK, YELLOW, BLUE][i % 3], bevel=0)


# Cloud corridor: a puffy cloud wall, torn wallpaper on visible battens with a curling corner, service structure.
corridor = root("Cloud corridor pack", 40)
# Large overlapping lobes keep one continuous puffy surface instead of a pile of pebbles.
for cx, cz, rx, rz, ry in ((-3.3, .95, 1.25, .95, .34), (-1.4, 1.0, 1.4, 1.0, .4), (.7, 1.0, 1.4, 1.0, .4), (2.8, .9, 1.3, .9, .36),
                           (-2.5, 2.0, 1.1, .9, .34), (-.6, 2.45, 1.3, 1.1, .4), (1.4, 2.2, 1.2, .95, .38), (3.1, 1.8, .95, .75, .32),
                           (-1.5, 3.0, .85, .7, .32), (.4, 3.2, .95, .7, .34), (2.0, 2.9, .7, .55, .3)):
    lobe(corridor, "Puffy cloud lobe", (cx, 0, cz), (rx, ry, rz), FOAM, 18, 10)
wx, wy, wa = 7.0, .2, .08
torn = [(-2.8, 0), (2.8, 0), (2.8, 4.9), (2.0, 5.9), (1.6, 6.05), (1.1, 6.2), (.5, 6.04), (-.1, 6.2), (-.8, 6.1), (-1.5, 6.2), (-2.1, 6.08), (-2.8, 6.2)]
extruded_outline(corridor, "Torn wallpaper panel", torn, .24, SKY, bevel=0, loc=(wx, wy, 0), rot=(0, 0, wa))
for bx, bz in ((-1.6, 2.2), (.4, 4.0), (1.7, 1.4)):
    for dx, dz, r in ((0, 0, .5), (.55, .12, .4), (-.5, .08, .36)):
        px, py = turn(bx + dx, -.15, wx, wy, wa)
        cylinder(corridor, "Painted wallpaper cloud", (px, py, bz + dz), r, .03, FOAM, 14, (math.pi / 2, 0, wa))
for bx in (-2.4, 0, 2.4):
    px, py = turn(bx, .28, wx, wy, wa)
    box(corridor, "Backing batten", (px, py, 3.0), (.16, .3, 6.0), WOOD, .03, (0, 0, wa))
for bz in (.8, 5.2):
    px, py = turn(0, .48, wx, wy, wa)
    box(corridor, "Backing rail", (px, py, bz), (5.4, .14, .2), WOOD, .03, (0, 0, wa))
cx, cy = turn(2.35, -.32, wx, wy, wa)
shell(corridor, "Curling wallpaper corner", (cx, cy, 5.45), 1.3, .3, .03, -.2, math.radians(250), CREAM, 12, (0, math.radians(-128), wa))
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


def smooth(obj, angle):
    """Smooth shading with sharp edges past the angle, so bevels read rounded and flat faces stay flat."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for face in bm.faces:
        face.smooth = True
    for edge in bm.edges:
        edge.smooth = not (len(edge.link_faces) != 2 or edge.calc_face_angle(0) > angle)
    bm.to_mesh(obj.data)
    bm.free()


def merge_by_material(parent):
    bpy.context.view_layer.update()
    groups = {}
    for obj in meshes(parent):
        smooth(obj, math.pi if obj.get("soft") else math.radians(35))
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
    # Bake rotation into vertices so each merged batch exports with an axis-aligned node and tight bounds.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes(parent):
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes(parent)[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


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


# 2×2 overview: each pack is rendered alone, framed to its own bounds, so all four get the same screen share.
import numpy as np


def bounds(parent):
    points = [obj.matrix_world @ Vector(corner) for obj in meshes(parent) for corner in obj.bound_box]
    return Vector([min(p[i] for p in points) for i in range(3)]), Vector([max(p[i] for p in points) for i in range(3)])


bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -.02))
bpy.context.object.data.materials.append(CARPET)
camera = bpy.data.objects.new("Preview camera", bpy.data.cameras.new("Preview camera"))
bpy.context.collection.objects.link(camera)
camera.data.type = "ORTHO"
sun = bpy.data.objects.new("Preview key", bpy.data.lights.new("Preview key", "SUN"))
bpy.context.collection.objects.link(sun)
sun.data.energy = 3.2
sun.rotation_euler = (math.radians(48), 0, math.radians(-28))
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 700, 550
scene.render.image_settings.file_format = "PNG"
scene.world.color = (.42, .46, .47)
scene.view_settings.look = "AgX - Medium High Contrast"
tiles = []
for pack in PACKS:
    for other in PACKS:
        for obj in meshes(other):
            obj.hide_render = other is not pack
    low, high = bounds(pack)
    centre = (low + high) / 2
    # Low, spread-out layouts (the nap and birthday room) are viewed more from above to fill the tile.
    direction = Vector((.42, -1, .72 if high.z - low.z > .2 * (high.x - low.x) else 1.5)).normalized()
    camera.location = centre + direction * 60
    camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    view = camera.matrix_world.inverted()
    corners = [view @ Vector((x, y, z)) for x in (low.x, high.x) for y in (low.y, high.y) for z in (low.z, high.z)]
    width = max(c.x for c in corners) - min(c.x for c in corners)
    height = max(c.y for c in corners) - min(c.y for c in corners)
    camera.data.ortho_scale = max(width, height * 700 / 550) * 1.12
    scene.render.filepath = str(SOURCE / f"previews/.tile-{len(tiles)}.png")
    bpy.ops.render.render(write_still=True)
    tiles.append(scene.render.filepath)
for obj in bpy.data.objects:
    obj.hide_render = False
sheet_pixels = np.zeros((1100, 1400, 4), dtype=np.float32)
for index, path in enumerate(tiles):
    image = bpy.data.images.load(path)
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(550, 700, 4)
    row = 1 - index // 2
    sheet_pixels[row * 550:(row + 1) * 550, (index % 2) * 700:(index % 2 + 1) * 700] = pixels
    bpy.data.images.remove(image)
    Path(path).unlink()
overview = bpy.data.images.new("Playroom zone overview", 1400, 1100, alpha=True)
overview.pixels = sheet_pixels.ravel()
overview.filepath_raw = str(SOURCE / "previews/playroom-zone-assets-preview.png")
overview.file_format = "PNG"
overview.save()
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / "blender/playroom-zone-assets.blend"))

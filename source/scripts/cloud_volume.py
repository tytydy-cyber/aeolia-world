"""Shared cloud builder for the playroom kits: fused metaball volumes with cauliflower lobes, a cut flat base or
back, and a baked top-to-underside shade in COLOR_0 (a multiplier on the material's palette colour).

Separate spheres read as balls or balloons; a fused surface with smaller lobes on top, a flat underside and a cool
shadowed belly reads as cloud. Import with sys.path pointing at this folder.
"""
import bmesh
import bpy
import math
import random
from mathutils import Vector

UNDERSIDE, TOP = (.64, .71, .84), (1.0, 1.0, .98)   # shade multipliers: cool shadowed belly, warm lit top


def cloud(parent, name, lobes, mat, resolution=.3, faces=1500, cut=None, seed=1, detail=2):
    """lobes: [(centre, radius or (rx, ry, rz))] main puffs. cut: (axis, value, keep_above) slices a flat closed base
    or back off the volume."""
    rng = random.Random(seed)
    ball = bpy.data.metaballs.new(f"{name}Volume")
    ball.resolution = ball.render_resolution = resolution
    ball.threshold = .6
    for centre, radius in lobes:
        radii = radius if isinstance(radius, tuple) else (radius,) * 3
        radius = max(radii)
        element = ball.elements.new(type="ELLIPSOID")
        element.co, element.radius, element.stiffness = centre, radius * 1.35, 2.0
        element.size_x, element.size_y, element.size_z = (r / radius for r in radii)
        radius = min(radii)
        # Smaller lobes bubbling out of the upper half give the cauliflower edge of a cumulus.
        for _ in range(detail):
            a, up = rng.uniform(0, math.tau), rng.uniform(.25, .9)
            direction = Vector((math.cos(a) * math.sqrt(1 - up * up), math.sin(a) * math.sqrt(1 - up * up), up))
            small = rng.uniform(.5, .68) * radius
            bud = ball.elements.new(type="BALL")
            bud.co, bud.radius, bud.stiffness = Vector(centre) + direction * radius * .7, small * 1.35, 2.0
    obj = bpy.data.objects.new(f"{name}Volume", ball)                # unique base names keep metaball families apart
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.name = obj.data.name = name
    if len(obj.data.polygons) > faces:
        mod = obj.modifiers.new("Budget", "DECIMATE")
        mod.ratio = faces / len(obj.data.polygons)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    if cut:
        axis, value, keep_above = cut
        normal = Vector([1 if i == axis else 0 for i in range(3)])
        point = Vector([value if i == axis else 0 for i in range(3)])
        result = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=point, plane_no=normal,
                                        clear_inner=keep_above, clear_outer=not keep_above)
        boundary = [e for e in bm.edges if e.is_boundary]
        bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        face.smooth = True
    flat = math.radians(60)
    for edge in bm.edges:
        edge.smooth = len(edge.link_faces) == 2 and edge.calc_face_angle(0) <= flat   # the cut face keeps a crisp rim
    bm.to_mesh(obj.data)
    bm.free()
    shade(obj)
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj


def shade(obj):
    """Bake the lit-top / shadowed-underside gradient into the active colour attribute."""
    data = obj.data
    low = min(v.co.z for v in data.vertices)
    high = max(v.co.z for v in data.vertices)
    data.calc_normals_split() if hasattr(data, "calc_normals_split") else None
    attribute = data.color_attributes.new("Shade", "FLOAT_COLOR", "POINT")
    for vertex in data.vertices:
        facing = max(0, min(1, (vertex.normal.z + .55) / 1.35))
        height = (vertex.co.z - low) / max(high - low, 1e-6)
        t = .7 * facing + .3 * height
        attribute.data[vertex.index].color = (*[UNDERSIDE[i] + (TOP[i] - UNDERSIDE[i]) * t for i in range(3)], 1)
    data.color_attributes.active_color = attribute
    data.color_attributes.render_color_index = data.color_attributes.active_color_index


def preview_tint(mat):
    """Preview renders only: multiply the material colour by the baked shade, as the game does. Call after export.
    Meshes sharing the material without a baked shade get a white one, so they keep their plain colour."""
    for obj in bpy.data.objects:
        if obj.type == "MESH" and mat.name in obj.data.materials and "Shade" not in obj.data.color_attributes:
            white = obj.data.color_attributes.new("Shade", "FLOAT_COLOR", "POINT")
            for item in white.data:
                item.color = (1, 1, 1, 1)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    shade_node = nodes.new("ShaderNodeVertexColor")
    shade_node.layer_name = "Shade"
    mix = nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.inputs["Factor"].default_value = 1
    mix.inputs[6].default_value = bsdf.inputs["Base Color"].default_value
    links.new(shade_node.outputs["Color"], mix.inputs[7])
    links.new(mix.outputs[2], bsdf.inputs["Base Color"])

"""Build, render and export the reusable Aeolia house with Blender 4.3."""
import bpy
import math
import random
from pathlib import Path
from mathutils import Vector

random.seed(37)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'assets'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color, rough=.8, metal=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    return m

plaster=material('Warm lime plaster',(.73,.67,.53))
stone=material('Carved limestone',(.56,.50,.38))
ivory=material('Pale window mouldings',(.83,.78,.64))
wood=material('Aged chestnut',(.19,.10,.055))
teal=material('Painted shutters',(.07,.21,.20))
dark=material('Window recess',(.018,.04,.048),.4)
iron=material('Bronze ironwork',(.15,.12,.07),.42,.65)
leaf=material('Climbing leaves',(.18,.28,.10))
flower=material('Wisteria flowers',(.43,.29,.47))
tiles=[material('Slate '+str(i),(.045+i*.013,.14+i*.018,.17+i*.019),.72) for i in range(4)]
parts=[]

def finish(obj,name,mat,bevel=0):
    obj.name=name
    obj.data.materials.append(mat)
    if bevel:
        mod=obj.modifiers.new('Soft worn edges','BEVEL')
        mod.width=bevel
        mod.segments=2 if bevel>=.06 else 1
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod=obj.modifiers.new('Weighted face normals','WEIGHTED_NORMAL')
        mod.keep_sharp=True
        bpy.ops.object.modifier_apply(modifier=mod.name)
    parts.append(obj)
    return obj

def box(name,loc,size,mat,bevel=.04,rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=bpy.context.object
    obj.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rotation: obj.rotation_euler=rotation
    return finish(obj,name,mat,bevel)

def cylinder(name,loc,radius,depth,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=depth,location=loc)
    return finish(bpy.context.object,name,mat,.025)

def polygon(name,verts,faces,mat):
    data=bpy.data.meshes.new(name)
    data.from_pydata(verts,[],faces)
    data.update()
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    return finish(obj,name,mat)

box('Lime rendered walls',(0,0,5.5),(12,10,11),plaster,.12)
box('Foundation',(0,0,.25),(12.3,10.3,.5),stone,.09)
box('First floor string course',(0,0,5.2),(12.25,10.25,.22),ivory)
box('Deep eaves cornice',(0,0,10.9),(12.5,10.5,.25),ivory)
for z in [.62,1.1]: box('Stone base moulding',(0,0,z),(12.15,10.15,.16),ivory)
for sx in [-1,1]:
    for sy in [-1,1]:
        for row in range(14):
            box('Alternating corner quoin',(sx*5.98,sy*4.98,1.45+row*.65),(1.05 if row%2 else .65,.65 if row%2 else 1.05,.56),stone,.035)

# Gables on both ends close the pitched roof instead of a floating roof pyramid.
for sy in [-1,1]:
    polygon('Gable',[(-6,sy*5,11),(6,sy*5,11),(0,sy*5,14.6)],[(0,1,2) if sy<0 else (2,1,0)],plaster)

half=6.65
rise=3.6
slope=math.atan2(rise,half)
for side in [-1,1]:
    box('Roof underlay',(side*half/2,0,12.8),(math.hypot(half,rise),11.5,.18),wood,.03,(0,side*slope,0))
    for row in range(10):
        t=(row+.5)/10
        for col in range(15):
            yy=-5.35+col*.76+(row%2)*.15
            xx=side*half*t
            zz=14.6-rise*t+.15
            box('Overlapping slate',(xx,yy,zz),(.87,.745,.105),random.choice(tiles),.024,(0,side*slope,0))
    box('Copper rain gutter',(side*6.64,0,10.98),(.18,11.7,.18),iron)
for i in range(19):
    box('Ridge cap',(0,-5.5+i*.61,14.7),(.4,.6,.26),tiles[2],.08)

box('Chimney stack',(3.8,2.4,13.7),(1.15,1.2,4.5),stone,.065)
box('Chimney cap',(3.8,2.4,15.95),(1.45,1.5,.25),ivory)
for z in [12.1,12.7,13.3,13.9,14.5,15.1]:box('Chimney brick course',(3.8,2.4,z),(1.18,1.23,.07),plaster,.01)

def window(cx,sy,z):
    yy=sy*5.03
    radius=.88
    # A dark arched silhouette, behind the separate carved voussoirs.
    coords=[(cx-radius,yy,z),(cx+radius,yy,z),(cx+radius,yy,z+1.55)]
    coords += [(cx+math.cos(a)*radius,yy,z+1.55+math.sin(a)*radius) for a in [i*math.pi/16 for i in range(1,17)]]
    polygon('Recessed arched glass',coords,[tuple(range(len(coords)))],dark)
    for side in [-1,1]:box('Window jamb',(cx+side*1.01,yy+sy*.06,z+.78),(.22,.24,1.65),ivory,.025)
    for i in range(13):
        a=(i+.5)*math.pi/13
        box('Carved arch stone',(cx+math.cos(a)*1.01,yy+sy*.06,z+1.55+math.sin(a)*1.01),(.25,.25,.25),ivory,.02,(0,math.pi/2-a,0))
    box('Window sill',(cx,yy+sy*.16,z-.05),(2.4,.65,.18),ivory)
    box('Glass mullion',(cx,yy+sy*.04,z+.95),(.065,.10,1.9),ivory,.01)
    box('Glass transom',(cx,yy+sy*.04,z+.95),(1.76,.10,.065),ivory,.01)
    for side in [-1,1]:
        xx=cx+side*1.59
        box('Shutter',(xx,yy,z+.9),(.8,.15,1.95),teal,.025)
        for j in range(9):box('Shutter louvers',(xx,yy+sy*.1,z+.14+j*.19),(.7,.09,.075),teal,.01)
        for j in [.3,1.5]:box('Shutter strap',(xx,yy+sy*.15,z+j),(.68,.06,.06),iron,.012)

for sy in [-1,1]:
    for xx in [-3.35,3.35]:
        for zz in [2,7]:window(xx,sy,zz)

# Door is framed and recessed, with individually modeled wooden planks.
box('Doorway shadow',(0,-5.07,1.8),(2.45,.12,3.6),dark)
for i in range(8):box('Oak door plank',(-.95+i*.27,-5.17,1.68),(.24,.12,3.24),wood,.018)
for sx in [-1,1]:box('Door pilaster',(sx*1.32,-5.12,1.8),(.28,.4,3.6),ivory)
box('Carved lintel',(0,-5.15,3.65),(2.95,.5,.35),ivory,.065)
for zz in [.55,2.5]:box('Door iron strap',(0,-5.25,zz),(2.1,.05,.07),iron,.01)
cylinder('Door handle',(.62,-5.31,1.6),.095,.2,iron).rotation_euler.x=math.pi/2
box('Door step',(0,-5.36,.15),(2.8,.6,.3),stone)

# Upper central balcony with narrow railings and bracket supports.
window(0,-1,7)
box('Balcony slab',(0,-5.62,6.75),(3.6,1.2,.25),ivory,.07)
for xx in [-1.45,1.45]:
    box('Balcony corbel',(xx,-5.42,6.3),(.35,.7,.7),stone,.08)
for i in range(15):cylinder('Balcony baluster',(-1.7+i*.243,-6.17,7.38),.032,1.15,iron)
box('Balcony handrail',(0,-6.17,7.98),(3.6,.10,.10),iron)

# Climbing vine follows one corner, with sparse hanging lavender flowers.
for i in range(95):
    z=.8+random.random()*9.1
    xx=-5.65+math.sin(z*.9)*.32+(random.random()-.5)*.6
    yy=-5.16-random.random()*.15
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.15+random.random()*.1,location=(xx,yy,z))
    obj=finish(bpy.context.object,'Ivy leaf',leaf)
    obj.scale=(1,.3,.7)
    if i%7==0:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.14,location=(xx+.12,yy-.08,z-.2))
        obj=finish(bpy.context.object,'Wisteria cluster',flower)
        obj.scale=(.7,.7,2.1)

# Merge by material: reuse the mesh across houses without hundreds of draw calls.
groups={}
for obj in parts:groups.setdefault(obj.data.materials[0].name,[]).append(obj)
for name,objects in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join()
    bpy.context.object.name=name
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

models=[o for o in bpy.context.scene.objects if o.type=='MESH']
triangles=0
for obj in models:
    obj.data.calc_loop_triangles()
    triangles+=len(obj.data.loop_triangles)
assert triangles<70000, f'Triangle budget exceeded: {triangles}'
print(f'ASSET_CHECK: {len(models)} material batches; {triangles} triangles')
bpy.ops.object.select_all(action='DESELECT')
for obj in models:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'aeolia-house.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)

# Save a directly editable source, then render a preview with real light/shadows.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'aeolia-house.blend'))
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.world.color=(.3,.3,.3)
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.47,.6,.72,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.04))
bpy.context.object.data.materials.append(material('Preview floor',(.32,.36,.33)))
bpy.ops.object.light_add(type='AREA',location=(-12,-14,22))
bpy.context.object.data.energy=2600
bpy.context.object.data.shape='DISK'
bpy.context.object.data.size=8
bpy.context.object.rotation_euler=(Vector((0,0,6))-bpy.context.object.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(22,-28,22))
camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,7))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=23
scene.camera=camera
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/'house-preview.png')
bpy.ops.render.render(write_still=True)

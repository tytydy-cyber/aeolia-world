import bpy, math, os
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, color, rough=.8, metal=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough; bs.inputs['Metallic'].default_value=metal
    return m

cloth=mat('Coat',(0.34,.055,.045),.92); darkcloth=mat('Mantle',(.12,.018,.025),.96)
skin=mat('Skin',(.78,.43,.23),.82); hair=mat('Hair',(.035,.025,.022),1)
leather=mat('Leather',(.19,.085,.035),.9); bootmat=mat('Boots',(.018,.055,.07),.82); gold=mat('Brass',(.72,.42,.1),.42,.25); scarfmat=mat('Scarf',(.8,.43,.08),.88)

def smooth(obj, bevel=.04):
    if obj.type=='MESH':
        for p in obj.data.polygons:p.use_smooth=True
        if bevel:
            mod=obj.modifiers.new('Soft edges','BEVEL');mod.width=bevel;mod.segments=3
    return obj

def uv_sphere(name,loc,scale,material,segments=32,rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material);return smooth(o,0)

def cube(name,loc,scale,material,bevel=.06):
    bpy.ops.mesh.primitive_cube_add(location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material);return smooth(o,bevel)

def cyl(name,loc,radius,depth,material,vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(material);return smooth(o,.025)

def torus(name,loc,major,minor,material,rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=36,minor_segments=10,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.data.materials.append(material);return smooth(o,0)

# Armature and named bones.
bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0)); rig=bpy.context.object;rig.name='TravelerRig'; arm=rig.data;arm.name='TravelerRig'
root=arm.edit_bones[0];root.name='root';root.head=(0,0,0);root.tail=(0,0,.9)
def bone(name,head,tail,parent=root):
    b=arm.edit_bones.new(name);b.head=head;b.tail=tail;b.parent=parent;return b
spine=bone('spine',(0,0,.9),(0,0,2.55));headb=bone('head',(0,0,2.55),(0,0,3.5),spine)
arm_l=bone('arm.L',(.38,0,2.45),(.72,0,1.7),spine);arm_r=bone('arm.R',(-.38,0,2.45),(-.72,0,1.7),spine)
leg_l=bone('leg.L',(.25,0,1.1),(.25,0,.15),root);leg_r=bone('leg.R',(-.25,0,1.1),(-.25,0,.15),root)
scarf1=bone('scarf.1',(.16,-.22,2.68),(.16,-.8,2.58),spine);scarf2=bone('scarf.2',(.16,-.8,2.58),(.16,-1.55,2.48),scarf1)
bpy.ops.object.mode_set(mode='OBJECT')

def bind(obj,bone_name):
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    world=obj.matrix_world.copy();obj.parent=rig;obj.parent_type='OBJECT';obj.matrix_world=world
    group=obj.vertex_groups.new(name=bone_name);group.add(range(len(obj.data.vertices)),1,'REPLACE')
    modifier=obj.modifiers.new('Traveler rig','ARMATURE');modifier.object=rig

# Rounded coat, layered mantle and tailored front.
coat=uv_sphere('Sculpted coat',(0,0,1.65),(.67,.5,1.02),cloth);bind(coat,'spine')
waist=cyl('Belt',(0,0,1.86),.52,.09,leather);bind(waist,'spine')
mantle=uv_sphere('Shoulder mantle',(0,-.015,2.4),(.61,.48,.36),darkcloth);bind(mantle,'spine')
for z in (1.48,1.76,2.04,2.3):
    b=uv_sphere('Brass button',(0,-.505,z),(.045,.035,.045),gold,16,10);bind(b,'spine')

# Face with separated hair volume and readable features.
face=uv_sphere('Face',(0,-.015,3.0),(.39,.35,.44),skin);bind(face,'head')
haircap=uv_sphere('Hair',(0,.12,3.14),(.41,.3,.36),hair);bind(haircap,'head')
for x in (-.14,.14):
    eye=uv_sphere('Eye',(x,-.34,3.05),(.034,.025,.045),hair,16,10);bind(eye,'head')
nose=uv_sphere('Nose',(0,-.365,2.96),(.045,.06,.06),skin,16,10);bind(nose,'head')

# Hat has a curved brim, crown and contrasting band.
brim=cyl('Hat brim',(0,0,3.39),.7,.09,leather,48);bind(brim,'head')
crown=cyl('Hat crown',(0,0,3.58),.42,.34,leather,40);crown.scale=(1,.86,1);bind(crown,'head')
band=cyl('Hat band',(0,0,3.49),.43,.075,gold,40);band.scale=(1,.86,1);bind(band,'head')

for side,bn,x in ((1,'arm.L',.52),(-1,'arm.R',-.52)):
    sleeve=uv_sphere('Sleeve',(x,0,2.08),(.2,.19,.5),cloth);bind(sleeve,bn)
    cuff=cyl('Cuff',(x,0,1.67),.19,.12,darkcloth);bind(cuff,bn)
    hand=uv_sphere('Hand',(x,0,1.53),(.14,.13,.16),skin,20,12);bind(hand,bn)
for side,bn,x in ((1,'leg.L',.25),(-1,'leg.R',-.25)):
    leg=cyl('Leg',(x,0,.7),.145,.72,bootmat,24);bind(leg,bn)
    toe=uv_sphere('Boot toe',(x,-.09,.26),(.18,.27,.14),bootmat,24,14);bind(toe,bn)

bag=cube('Satchel',(-.57,.18,1.55),(.27,.13,.3),leather,.075);bind(bag,'spine')
strap=torus('Satchel strap',(0,.04,2.15),.54,.032,gold,(math.pi/2,.35,-.68));bind(strap,'spine')
knot=torus('Scarf knot',(.16,-.05,2.67),.29,.055,scarfmat,(math.pi/2,0,0));bind(knot,'spine')
tail1=cube('Scarf upper',(.16,-.56,2.58),(.15,.38,.035),scarfmat,.035);bind(tail1,'scarf.1')
tail2=cube('Scarf lower',(.16,-1.18,2.49),(.14,.4,.03),scarfmat,.035);bind(tail2,'scarf.2')

# Animation actions. Four poses per loop give a soft stylized gait.
def action(name,frames):
    a=bpy.data.actions.new(name);rig.animation_data_create();rig.animation_data.action=a
    for frame,poses in frames:
        for bn,rot in poses.items():
            p=rig.pose.bones[bn];p.rotation_mode='XYZ';p.rotation_euler=rot;p.keyframe_insert('rotation_euler',frame=frame,group=bn)
    for fc in a.fcurves:
        for kp in fc.keyframe_points:kp.interpolation='BEZIER'
    a.frame_range=(frames[0][0],frames[-1][0]);a.use_fake_user=True
    return a

idle=action('Idle',[(1,{'spine':(0,0,-.012),'scarf.1':(.04,0,.02)}),(30,{'spine':(0,0,.012),'scarf.1':(-.025,0,-.025)}),(60,{'spine':(0,0,-.012),'scarf.1':(.04,0,.02)})])
walk=action('Walk',[(1,{'arm.L':(.55,0,0),'arm.R':(-.55,0,0),'leg.L':(-.62,0,0),'leg.R':(.62,0,0),'scarf.1':(.11,0,.08),'scarf.2':(-.1,0,.08)}),(16,{'arm.L':(-.55,0,0),'arm.R':(.55,0,0),'leg.L':(.62,0,0),'leg.R':(-.62,0,0),'scarf.1':(-.06,0,-.08),'scarf.2':(.1,0,-.1)}),(31,{'arm.L':(.55,0,0),'arm.R':(-.55,0,0),'leg.L':(-.62,0,0),'leg.R':(.62,0,0),'scarf.1':(.11,0,.08),'scarf.2':(-.1,0,.08)})])
fly=action('Fly',[(1,{'spine':(.2,0,0),'arm.L':(-.15,0,-.75),'arm.R':(-.15,0,.75),'leg.L':(.18,0,0),'leg.R':(.18,0,0),'scarf.1':(.52,0,.05),'scarf.2':(.35,0,-.04)}),(24,{'spine':(.16,0,0),'arm.L':(-.2,0,-.68),'arm.R':(-.2,0,.68),'leg.L':(.24,0,0),'leg.R':(.14,0,0),'scarf.1':(.36,0,-.05),'scarf.2':(.5,0,.08)}),(48,{'spine':(.2,0,0),'arm.L':(-.15,0,-.75),'arm.R':(-.15,0,.75),'leg.L':(.18,0,0),'leg.R':(.18,0,0),'scarf.1':(.52,0,.05),'scarf.2':(.35,0,-.04)})])

# Preserve all actions in the GLB as animation tracks.
rig.animation_data.action=None
for a in (idle,walk,fly):
    track=rig.animation_data.nla_tracks.new();track.name=a.name;strip=track.strips.new(a.name,int(a.frame_range[0]),a);strip.action_frame_start=a.frame_range[0];strip.action_frame_end=a.frame_range[1];track.mute=True

for o in bpy.context.scene.objects:o.select_set(False)
rig.select_set(True)
for o in bpy.context.scene.objects:
    if o.type=='MESH':o.select_set(True)
bpy.context.view_layer.objects.active=rig

out=os.path.abspath(os.path.join(os.path.dirname(__file__),'../outputs/assets/aeolia-traveler.glb'))
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_animations=True,export_nla_strips=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(os.path.dirname(__file__),'../outputs/assets/aeolia-traveler.blend')))
print(out)

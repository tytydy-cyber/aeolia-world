import bpy
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parents[1]/'outputs'/'assets'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'aeolia-house.blend'))
for material in bpy.data.materials:
    name=material.name
    kind='plaster' if 'plaster' in name else 'stone' if 'limestone' in name or 'mouldings' in name else 'slate' if name.startswith('Slate') else 'wood' if 'chestnut' in name or 'shutters' in name else None
    if not kind or not material.use_nodes:continue
    nodes=material.node_tree.nodes;links=material.node_tree.links;bsdf=nodes.get('Principled BSDF')
    coords=nodes.new('ShaderNodeTexCoord');scale=nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=1/(1.6 if kind=='slate' else 2 if kind=='wood' else 3)
    links.new(coords.outputs['Object'],scale.inputs[0])
    color=nodes.new('ShaderNodeTexImage');color.image=bpy.data.images.load(str(OUT/'textures'/f'{kind}-color.jpg'));color.projection='BOX';color.projection_blend=.08
    bumptex=nodes.new('ShaderNodeTexImage');bumptex.image=bpy.data.images.load(str(OUT/'textures'/f'{kind}-height.png'));bumptex.image.colorspace_settings.name='Non-Color';bumptex.projection='BOX';bumptex.projection_blend=.08
    links.new(scale.outputs[0],color.inputs[0]);links.new(scale.outputs[0],bumptex.inputs[0])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.3;bump.inputs['Distance'].default_value=.12
    links.new(bumptex.outputs['Color'],bump.inputs['Height']);links.new(bump.outputs[0],bsdf.inputs['Normal']);links.new(color.outputs['Color'],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=.8
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'aeolia-house-textured.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.47,.6,.72,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.04))
bpy.ops.object.light_add(type='AREA',location=(-12,-14,22));bpy.context.object.data.energy=2600;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=8
bpy.context.object.rotation_euler=(Vector((0,0,6))-bpy.context.object.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(22,-28,22));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,7))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=23;scene.camera=camera
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.filepath=str(OUT/'house-textured-preview.png');bpy.ops.render.render(write_still=True)

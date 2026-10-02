"""Render frames of each traveler emote from a front three-quarter view, for checking poses by eye.

Run after build_traveler.py:
  Blender --background source/blender/aeolia-traveler.blend --python work/render_traveler_emotes.py
Frames go to the folder in EMOTE_FRAMES (default /tmp/aeolia-emotes); combine them with
  python3 work/render_traveler_emotes.py --sheet
"""
import os
import sys

FRAMES = {'Wave': (1, 8, 13, 19, 37, 48), 'Bow': (1, 8, 14, 28, 40, 48), 'Spin': (1, 6, 12, 18, 24, 30)}
OUT = os.environ.get('EMOTE_FRAMES', '/tmp/aeolia-emotes')

if '--sheet' in sys.argv:
    from PIL import Image, ImageDraw
    names = list(FRAMES)
    first = Image.open(os.path.join(OUT, f'{names[0]}-{FRAMES[names[0]][0]:02d}.png'))
    w, h = first.size
    sheet = Image.new('RGB', (w * 6, (h + 24) * len(names)), '#20323a')
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(names):
        for col, frame in enumerate(FRAMES[name]):
            sheet.paste(Image.open(os.path.join(OUT, f'{name}-{frame:02d}.png')).convert('RGB'), (col * w, row * (h + 24) + 24))
            draw.text((col * w + 6, row * (h + 24) + 6), f'{name} {frame}', fill='#f0e2b8')
    target = sys.argv[sys.argv.index('--sheet') + 1] if len(sys.argv) > sys.argv.index('--sheet') + 1 else os.path.join(OUT, 'sheet.png')
    sheet.save(target)
    print('SHEET', target)
    sys.exit()

import bpy
from mathutils import Vector

os.makedirs(OUT, exist_ok=True)
scene = bpy.context.scene
rig = bpy.data.objects['TravelerRig']
for track in rig.animation_data.nla_tracks:
    track.mute = True
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 12
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 300, 380
scene.render.film_transparent = False
if not scene.world:
    scene.world = bpy.data.worlds.new('Preview world')
scene.world.use_nodes = True
background = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
background.inputs[0].default_value = (.55, .66, .72, 1)
background.inputs[1].default_value = .8
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
bpy.context.object.data.energy = 3
bpy.context.object.rotation_euler = (0.8, 0, -0.6)
# The traveler faces -Y in Blender (+Z in three.js); look from the front three-quarter side.
bpy.ops.object.camera_add(location=(4.2, -6.5, 3.2))
camera = bpy.context.object
camera.rotation_euler = (Vector((0, 0, 2.1)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 5.6
scene.camera = camera
for name, frames in FRAMES.items():
    rig.animation_data.action = bpy.data.actions[name]
    for frame in frames:
        scene.frame_set(frame)
        scene.render.filepath = os.path.join(OUT, f'{name}-{frame:02d}.png')
        bpy.ops.render.render(write_still=True)
print('FRAMES', OUT)

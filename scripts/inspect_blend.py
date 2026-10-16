"""Validate saved animation data and render one selected frame for visual QA."""
import argparse
import json
from pathlib import Path
import bpy

p=argparse.ArgumentParser()
p.add_argument('blend',type=Path);p.add_argument('--out',type=Path,required=True)
p.add_argument('--frame',type=int,default=127)
args=p.parse_args();args.out=args.out.resolve();args.out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
scene=bpy.context.scene
root=bpy.data.objects.get('pip-capybara-v1')
assert root and root['asset_version']=='pip-capybara-v1'
assert scene.frame_end==240 and scene.render.fps==12
assert root.animation_data.action.fcurves
assert scene.cycles.device=='CPU'
scene.frame_set(args.frame)
scene.render.resolution_x=540;scene.render.resolution_y=960
scene.cycles.samples=4;scene.render.threads=4
scene.render.filepath=str(args.out)
bpy.ops.render.render(write_still=True)
report={'blender':bpy.app.version_string,'objects':len(scene.objects),'frame':args.frame,
        'root_position':list(root.location),'root_rotation':list(root.rotation_euler),
        'keyframes_per_root_channel':[len(fc.keyframe_points) for fc in root.animation_data.action.fcurves],
        'cpu':scene.cycles.device,'animation_frames':scene.frame_end,'animation_fps':scene.render.fps}
args.out.with_suffix('.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

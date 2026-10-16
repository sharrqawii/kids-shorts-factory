"""Isolated Blender process: a timeout or native crash cannot block fallback."""
import argparse
import json
import time
from pathlib import Path
import bpy
from .scene import build_scene,apply_pose


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True);p.add_argument('--width',type=int,default=540)
    p.add_argument('--height',type=int,default=960);p.add_argument('--samples',type=int,default=12)
    p.add_argument('--threads',type=int,default=4);p.add_argument('--frames',type=int,default=240)
    p.add_argument('--still',type=float);p.add_argument('--save-blend',action='store_true')
    a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    spec=json.loads((Path(__file__).resolve().parents[1]/'assets/pip.json').read_text())
    start=time.monotonic();rig=build_scene(spec,a.width,a.height,a.samples,a.threads)
    timings=[]
    for i in range(1 if a.still is not None else a.frames):
        t=a.still if a.still is not None else i/12
        rig['scene'].frame_set(i+1);apply_pose(rig,t)
        if a.save_blend and i==0:
            # Store all animation poses so the .blend is an editable animated source.
            animated=[rig['pip']['root'],rig['pip']['head'],*rig['pip']['feet'],*rig['pip']['eyes'],rig['berry'],rig['heart']]
            for frame in range(240):
                apply_pose(rig,frame/12)
                for obj in animated:
                    for prop in ('location','rotation_euler','scale'):obj.keyframe_insert(prop,frame=frame+1)
            for obj in animated:
                for fcurve in obj.animation_data.action.fcurves:
                    for key in fcurve.keyframe_points:key.interpolation='LINEAR'
            rig['scene'].frame_set(i+1);apply_pose(rig,t)
            bpy.ops.wm.save_as_mainfile(filepath=str(out.parent/'pip-strawberry.blend'))
        rig['scene'].render.filepath=str(out/f'{i:04d}.png')
        tic=time.monotonic();bpy.ops.render.render(write_still=True)
        timings.append(time.monotonic()-tic)
        report={'engine':'Blender Cycles CPU','blender':bpy.app.version_string,'width':a.width,'height':a.height,'samples':a.samples,'threads':a.threads,'denoising_prefilter':rig['scene'].cycles.denoising_prefilter,'denoising_quality':rig['scene'].cycles.denoising_quality,'denoising_gpu':rig['scene'].cycles.denoising_use_gpu,'frames_done':len(timings),'frame_seconds':timings,'elapsed_seconds':time.monotonic()-start}
        (out/'metrics.json').write_text(json.dumps(report,indent=2))
        print(f'FRAME {i+1}/{a.frames}: {timings[-1]:.2f}s',flush=True)


if __name__=='__main__':main()

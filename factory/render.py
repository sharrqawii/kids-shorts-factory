"""One command from source to a verified MP4, with bounded CPU rendering."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image
from .audio import write_audio
from .graphics import title, fallback_frame
from .story import validate_episode
from .verify import verify

ROOT=Path(__file__).resolve().parents[1]


def blender(out, frames, width, height, samples, threads, timeout, save=False):
    cmd=[sys.executable,'-m','factory.blender_worker','--out',str(out),'--frames',str(frames),
         '--width',str(width),'--height',str(height),'--samples',str(samples),'--threads',str(threads)]
    if save:cmd+=['--save-blend']
    with (out.parent/(out.name+'.log')).open('w',encoding='utf-8') as log:
        subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=timeout)
    return json.loads((out/'metrics.json').read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['auto','blender','economy','fallback'],default='auto')
    p.add_argument('--out',type=Path,default=Path('build/episode'))
    p.add_argument('--threads',type=int,default=4)
    p.add_argument('--budget-seconds',type=int,default=4500)
    p.add_argument('--smoke',action='store_true',help='2-second integration clip; never presented as a full episode')
    a=p.parse_args()
    if not 1<=a.threads<=32 or a.budget_seconds<30:p.error('threads must be 1..32; budget at least 30 seconds')
    for tool in ['ffmpeg','ffprobe']:
        if not shutil.which(tool):p.error(f'{tool} is missing; see README setup')
    config=json.loads((ROOT/'episodes/strawberry.json').read_text());validate_episode(config)
    duration=2 if a.smoke else config['duration'];frames=round(duration*config['animation_fps'])
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    # A fresh run directory prevents stale PNGs from becoming part of a new video.
    run=out/f'run-{time.time_ns()}';run.mkdir()
    start=time.monotonic();report={'requested_mode':a.mode,'smoke':a.smoke,'duration':duration,'animation_fps':12,'delivery_fps':24,'output_resolution':[1080,1920],'fallback_reasons':[]}
    selected=a.mode
    if a.mode=='auto':
        try:
            probe=blender(run/'benchmark',3,540,960,4,a.threads,min(180,a.budget_seconds/3))
            report['benchmark']=probe
            estimate=max(probe['frame_seconds'])*frames*1.5+60
            report['economy_estimated_seconds']=estimate
            # Measure actual CPU speed; upscale the same geometry for the low-cost tier.
            selected='economy' if estimate<a.budget_seconds*.80 else 'fallback'
            if selected=='fallback':report['fallback_reasons'].append('Measured Blender render exceeds configured CPU time budget')
        except (subprocess.SubprocessError,OSError,ValueError) as error:
            selected='fallback';report['fallback_reasons'].append(f'Blender benchmark failed: {error}')
    raw=run/'frames';raw.mkdir()
    width,height,samples=(1080,1920,12) if selected=='blender' else (540,960,4)
    if selected in ('blender','economy'):
        try:
            remaining=max(1,a.budget_seconds-(time.monotonic()-start))
            report['render']=blender(raw,frames,width,height,samples,a.threads,remaining,save=True)
        except (subprocess.SubprocessError,OSError,ValueError) as error:
            if a.mode!='auto':raise
            report['fallback_reasons'].append(f'Blender run failed or timed out: {error}')
            selected='fallback'
    delivery=run/'delivery';delivery.mkdir()
    for i in range(frames):
        if selected=='fallback':
            image=fallback_frame(i/12,1080,1920)
        else:
            with Image.open(raw/f'{i:04d}.png') as rendered:
                image=rendered.convert('RGB').resize((1080,1920),Image.Resampling.LANCZOS)
            title(image,i/12)
        image.save(delivery/f'{i:04d}.png',compress_level=1)
        if i in (0,min(72,frames-1),min(132,frames-1),min(216,frames-1)):
            image.save(out/f'story-{i:04d}.jpg',quality=93)
    audio=out/'original-audio.wav';report['audio']=write_audio(audio,duration)
    name='smoke-test.mp4' if a.smoke else 'pip-and-the-giant-strawberry.mp4'
    video=out/name
    subprocess.run(['ffmpeg','-y','-v','warning','-framerate','12','-start_number','0','-i',str(delivery/'%04d.png'),
                    '-i',str(audio),'-map','0:v:0','-map','1:a:0','-vf','fps=24','-c:v','libx264',
                    '-preset','fast','-crf','19','-pix_fmt','yuv420p','-threads',str(a.threads),
                    '-c:a','aac','-b:a','192k','-ar','48000','-t',str(duration),'-movflags','+faststart',str(video)],check=True,timeout=300)
    report['verification']=verify(video,duration)['checks']
    report['actual_mode']=selected
    report['render_resolution']=[width,height] if selected!='fallback' else [1080,1920]
    report['note']='12 distinct animation poses per second, each held for two delivery frames.'
    if selected=='economy':report['note']+=' Blender renders at 540x960, Lanczos-upscaled to 1080x1920. Titles are native 1080p.'
    if selected=='fallback':report['note']+=' The fallback is a shaded 2.5D illustration, not full 3D geometry.'
    report['elapsed_seconds']=time.monotonic()-start
    report['video_bytes']=video.stat().st_size
    report['sha256']=hashlib.sha256(video.read_bytes()).hexdigest()
    report['environment']={'python':sys.version,'platform':sys.platform,'threads':a.threads}
    report['inputs']={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [ROOT/'assets/pip.json',ROOT/'episodes/strawberry.json']}
    (out/'render-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    blend=run/'pip-strawberry.blend'
    if blend.exists():shutil.copy2(blend,out/'pip-strawberry.blend')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()

"""Probe and fully decode an MP4; reject silently wrong deliverables."""
import argparse
import json
import subprocess
from pathlib import Path


def verify(path, duration=20):
    result=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,check=True)
    info=json.loads(result.stdout)
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    audio=next(s for s in info['streams'] if s['codec_type']=='audio')
    checks={
        'resolution':(video['width'],video['height'])==(1080,1920),
        'h264':video['codec_name']=='h264',
        'yuv420p':video['pix_fmt']=='yuv420p',
        'duration':abs(float(info['format']['duration'])-duration)<.10,
        'fps':video['avg_frame_rate']=='24/1',
        'frame_count':int(video.get('nb_frames',0))==round(duration*24),
        'aac':audio['codec_name']=='aac',
        'stereo_48khz':audio['channels']==2 and audio['sample_rate']=='48000',
        'audio_duration':abs(float(audio['duration'])-duration)<.10,
    }
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'],check=True,capture_output=True)
    checks['full_decode']=True
    report={'pass':all(checks.values()),'checks':checks,'probe':info}
    Path(path).with_suffix('.verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not report['pass']:raise RuntimeError(f'Output verification failed: {checks}')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path');p.add_argument('--duration',type=float,default=20)
    args=p.parse_args();print(json.dumps(verify(args.path,args.duration)['checks'],indent=2))

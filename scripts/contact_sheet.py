"""Extract actual MP4 frames, not substitute illustrations, for review."""
import argparse
import subprocess
import tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

p=argparse.ArgumentParser();p.add_argument('video',type=Path);p.add_argument('out',type=Path)
args=p.parse_args()
times=[1,6,10.5,14,18.5]
sheet=Image.new('RGB',(270*len(times),520),'#f1f5eb')
draw=ImageDraw.Draw(sheet)
with tempfile.TemporaryDirectory() as temp:
    for i,t in enumerate(times):
        imagepath=Path(temp)/f'{i}.png'
        subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(args.video),'-frames:v','1','-vf','scale=270:480','-y',str(imagepath)],check=True)
        with Image.open(imagepath) as im:sheet.paste(im,(270*i,0))
        draw.text((270*i+14,493),f'{t:04.1f}s',fill='#234739',font=ImageFont.load_default(size=19))
args.out.parent.mkdir(parents=True,exist_ok=True)
sheet.save(args.out)

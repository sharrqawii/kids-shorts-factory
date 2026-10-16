"""Titles and a deliberately simpler, CPU-only illustrated fallback."""
import math
from PIL import Image, ImageDraw, ImageFont
from .story import pose


def title(image, t):
    w,h=image.size
    scale=w/1080
    layer=Image.new('RGBA',image.size)
    draw=ImageDraw.Draw(layer)
    def text(x,y,value,size,fill):
        draw.text((int(x*scale),int(y*scale)),value,font=ImageFont.load_default(size=int(size*scale)),fill=fill,stroke_width=0)
    text(86,126,'P I P ’ S   L I T T L E   W O R L D',24,(35,87,71,255))
    if t<5:
        opacity=int(255*min(1,(5-t)/.5))
        text(80,190,'A very',78,(35,71,57,opacity))
        text(80,273,'BIG berry!',98,(35,71,57,opacity))
        text(85,390,'A tiny garden discovery',28,(35,87,71,opacity))
    elif t>16.8:
        opacity=int(255*min(1,(t-16.8)/.5))
        text(80,215,'Little friend.',73,(35,71,57,opacity))
        text(80,298,'BIG discovery.',78,(35,71,57,opacity))
    image.alpha_composite(layer) if image.mode=='RGBA' else image.paste(Image.alpha_composite(image.convert('RGBA'),layer).convert('RGB'))
    return image


def fallback_frame(t,width=540,height=960):
    """2.5D shaded illustration: portability fallback, not a Blender render."""
    image=Image.new('RGB',(width,height),'#cdebd5')
    d=ImageDraw.Draw(image)
    sx=width/540;sy=height/960
    def ellipse(box,fill):d.ellipse(tuple(int(v*(sx if i%2==0 else sy)) for i,v in enumerate(box)),fill)
    def shaded(box,color):
        from PIL import ImageColor
        rgb=ImageColor.getrgb(color)
        cx=(box[0]+box[2])/2;cy=(box[1]+box[3])/2
        rx=(box[2]-box[0])/2;ry=(box[3]-box[1])/2
        for i in range(32):
            f=1-i/36
            c=tuple(min(255,int(v*(.80+.30*i/31))) for v in rgb)
            ellipse((cx-rx*f-i*.2,cy-ry*f-i*.3,cx+rx*f-i*.2,cy+ry*f-i*.3),c)
    ellipse((-180,370,430,1060),'#a6dba0');ellipse((180,395,750,1100),'#95d1aa')
    for x,y,c in [(48,405,'#d8a2d3'),(475,425,'#c1ace5')]:
        d.line((int(x*sx),int((y+180)*sy),int(x*sx),int(y*sy)),fill='#c39872',width=max(1,int(16*sx)))
        shaded((x-65,y-80,x+65,y+75),c)
    state=pose(t)
    bx=373+state['berry_wobble']*80;by=617
    ellipse((bx-99,by+76,bx+104,by+111),'#7eae87')
    shaded((bx-100,by-124,bx+98,by+85),'#ed4f67')
    for row in range(5):
        for col in range(5):
            x=bx-65+col*31+(row%2)*9
            y=by-86+row*33
            if ((x-bx)/90)**2+((y-by+15)/100)**2<.85:ellipse((x-3,y-5,x+3,y+5),'#ffe5a5')
    for i in range(5):
        a=i*math.tau/5
        ellipse((bx-14+math.cos(a)*28,by-140+math.sin(a)*12,bx+20+math.cos(a)*28,by-114+math.sin(a)*12),'#46995d')
    x=214+(state['x']+1.07)*88;y=645-state['z']*100
    ellipse((x-70,727,x+80,747),'#7eae87')
    for dx in [-43,43]:shaded((x+dx-19,y+38,x+dx+22,y+90),'#bd8753')
    shaded((x-62,y-51,x+62,y+67),'#bd8753')
    ellipse((x-52,y-20,x+52,y+2),'#48bfa7')
    for dx in [-48,48]:
        shaded((x+dx-14,y-116,x+dx+15,y-78),'#b97b48')
        ellipse((x+dx-8,y-106,x+dx+8,y-88),'#dfaa8b')
    shaded((x-69,y-106,x+69,y+3),'#b97b48')
    shaded((x-58,y-55,x+58,y-1),'#e5b77b')
    for dx in [-39,39]:
        eh=10*state['eye']
        ellipse((x+dx-7,y-62-eh,x+dx+7,y-62+eh),'#2a2427')
        if eh>3:ellipse((x+dx-3,y-67,x+dx+1,y-63),'white')
        ellipse((x+dx-9,y-42,x+dx+8,y-32),'#df9390')
    for dx in [-15,15]:ellipse((x+dx-3,y-33,x+dx+3,y-29),'#684832')
    d.arc((int((x-16)*sx),int((y-26)*sy),int((x+16)*sx),int((y-11)*sy)),0,180,fill='#684832',width=max(1,int(2*sx)))
    ellipse((x-22,y-1,x-7,y+14),'#ffdb71')
    if state['heart']>.01:
        hx=x+70;hy=420-(state['heart_z']-2.4)*90;r=15*state['heart']
        ellipse((hx-r*1.5,hy-r,hx+.2*r,hy+r),'#ee7b9a');ellipse((hx-.2*r,hy-r,hx+1.5*r,hy+r),'#ee7b9a')
        d.polygon([(int((hx-r*1.5)*sx),int(hy*sy)),(int((hx+r*1.5)*sx),int(hy*sy)),(int(hx*sx),int((hy+2*r)*sy))],fill='#ee7b9a')
    return title(image,t)

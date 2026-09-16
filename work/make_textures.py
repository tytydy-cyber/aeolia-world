"""Seamless material maps, paired color/height, generated locally without downloads."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import math

OUT=Path(__file__).resolve().parents[1]/'outputs'/'assets'/'textures'
OUT.mkdir(parents=True,exist_ok=True)
N=512
rng=random.Random(710)

def noise(size,grid):
    small=Image.new('L',(grid,grid));small.putdata([rng.randrange(256) for _ in range(grid*grid)])
    tiled=Image.new('L',(grid*3,grid*3))
    for x in range(3):
        for y in range(3):tiled.paste(small,(x*grid,y*grid))
    return tiled.resize((size*3,size*3),Image.Resampling.BICUBIC).crop((size,size,size*2,size*2))

layers=[list(noise(N,g).getdata()) for g in [4,12,32,96]]
materials={
    'plaster':(220,204,180),'stone':(180,170,148),'slate':(108,130,141),
    'grass':(108,121,77),'wood':(130,92,58),'cliff':(132,122,105),
}
sheet=Image.new('RGB',(N*3,(N+36)*2),'#243b44');draw=ImageDraw.Draw(sheet)
for mi,(kind,base) in enumerate(materials.items()):
    rgb=[];height=[]
    for i in range(N*N):
        x=i%N;y=i//N
        a,b,c,d=[layer[i]/255-.5 for layer in layers]
        grain=a*.42+b*.25+c*.12+d*.07
        relief=.52+c*.12+d*.12
        moss=0
        if kind=='plaster':
            # Broad lime patches and tiny pits, without a repetitive brick pattern.
            grain+=max(0,b-.18)*.6
            grain*=.35
            relief+=b*.12-(.15 if d<-.38 else 0)
        elif kind=='stone':
            row=y//64;offset=(row%2)*64
            joint=min((x+offset)%128,128-(x+offset)%128,y%64,64-y%64)
            edge=max(0,1-joint/5)
            grain-=edge*.22;relief-=edge*.27
            grain+=math.sin(((x+offset)//128%4)*17+row*71)*.035
        elif kind=='slate':
            ridge=math.sin(x*math.tau*20/N+b*2)*.023+math.sin(y*math.tau*9/N+a*3)*.04
            grain+=ridge;relief+=ridge*2
        elif kind=='wood':
            ring=math.sin(x*math.tau*20/N+math.sin(y*math.tau*2/N)*1.2+b*7)
            grain+=ring*.07+math.sin(x*math.tau*68/N+c*5)*.04
            relief+=ring*.08
            joint=min(x%128,128-x%128)
            if joint<3:grain-=.28;relief-=.3
        elif kind=='grass':
            grain=a*.5+b*.28+c*.18+d*.11
            moss=max(0,b)*.45;relief+=b*.2
            if d>.3:grain+=.07
        else:
            strata=math.sin(y*math.tau*4/N+a*7)*.09+math.sin(y*math.tau*19/N+b*3)*.035
            grain+=strata;relief+=strata*1.7+b*.15
            moss=max(0,a+b-.35)*.25
        rgb.append(tuple(max(0,min(255,int(v*(1+grain)-(20 if j!=1 else 0)*moss))) for j,v in enumerate(base)))
        height.append(max(0,min(255,int(relief*255))))
    color=Image.new('RGB',(N,N));color.putdata(rgb);color.save(OUT/f'{kind}-color.jpg',quality=90)
    bump=Image.new('L',(N,N));bump.putdata(height);bump.save(OUT/f'{kind}-height.png')
    col=mi%3;row=mi//3;sheet.paste(color,(col*N,row*(N+36)));draw.text((col*N+12,row*(N+36)+N+8),kind.upper(),fill='#ead4a9')
sheet.save(OUT/'material-preview.jpg',quality=90)

# Panoramic background: multi-scale clouds and atmospheric mountain silhouettes.
W,H=2048,1024
clouds=noise(1024,12).resize((W,H));fine=noise(1024,40).resize((W,H));co=list(clouds.getdata());fi=list(fine.getdata())
pixels=[]
for y in range(H):
    v=y/H
    if v<.5:
        t=v/.5;start=(58,99,132);end=(186,202,207)
    else:
        t=(v-.5)/.5;start=(186,202,207);end=(219,211,191)
    base=[a+(b-a)*t for a,b in zip(start,end)]
    for x in range(W):
        i=y*W+x
        cover=max(0,min(.68,((co[i]/255*.8+fi[i]/255*.2)-.55)*3))
        cover*=max(0,1-abs(v-.32)*3)
        pixels.append(tuple(int(c*(1-cover)+light*cover) for c,light in zip(base,(233,230,217))))
panorama=Image.new('RGB',(W,H));panorama.putdata(pixels);pd=ImageDraw.Draw(panorama)
for layer,(base,amp,color) in enumerate([(540,72,(157,181,188)),(565,90,(141,164,173)),(592,115,(118,145,157))]):
    terrain=[[rng.random() for _ in range(n)] for n in [9,23,61]]
    def contour(x,values):
        p=x/W*len(values);i=int(p)%len(values);f=p-int(p);f=f*f*(3-2*f)
        return values[i]*(1-f)+values[(i+1)%len(values)]*f
    points=[]
    for x in range(W+1):
        peak=sum(contour(x,values)*weight for values,weight in zip(terrain,[.65,.25,.1]))
        points.append((x,base-peak*amp))
    pd.polygon(points+[(W,H),(0,H)],fill=color)
veil=Image.new('RGBA',(W,H));vd=ImageDraw.Draw(veil)
for y in range(540,H):
    alpha=int(min(.96,max(0,(y-540)/200))*255)
    vd.line([(0,y),(W,y)],fill=(200,212,210,alpha))
panorama=Image.alpha_composite(panorama.convert('RGBA'),veil).convert('RGB')
panorama=panorama.filter(ImageFilter.GaussianBlur(.65));panorama.save(OUT/'sky-panorama.jpg',quality=90)
assert all((OUT/f'{name}-color.jpg').exists() and (OUT/f'{name}-height.png').exists() for name in materials)
print('Generated six paired 512px material maps and a 2048×1024 panorama.')

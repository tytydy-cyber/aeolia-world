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

# Floating-island atlases. Runs after the maps above so their random sequence is unchanged.
# Every cell is opaque and full-bleed (no gutters to bleed); surface cells tile seamlessly within their cell.
ar=random.Random(9031)
C=256

def soften(image,radius):
    """Gaussian blur that wraps around the cell edges, so tiling cells stay seamless."""
    w,h=image.size;tiled=Image.new(image.mode,(w*3,h*3))
    for x in range(3):
        for y in range(3):tiled.paste(image,(x*w,y*h))
    return tiled.filter(ImageFilter.GaussianBlur(radius)).crop((w,h,w*2,h*2))

def cell_noise(grid,size=C):
    small=Image.new('L',(grid,grid));small.putdata([ar.randrange(256) for _ in range(grid*grid)])
    tiled=Image.new('L',(grid*3,grid*3))
    for x in range(3):
        for y in range(3):tiled.paste(small,(x*grid,y*grid))
    return tiled.resize((size*3,size*3),Image.Resampling.BICUBIC).crop((size,size,size*2,size*2))

def tint(base,amount,grid=6,fine=24,size=C):
    """Base colour with soft tileable mottling; amount is the relative brightness swing."""
    a=cell_noise(grid,size);b=cell_noise(fine,size)
    shade=Image.blend(a,b,.3).point(lambda v:int(128+(v-128)*amount*2))
    flat=Image.new('RGB',(size,size),base)
    return Image.composite(flat.point(lambda v:min(255,int(v*1.12))),flat.point(lambda v:int(v*.86)),shade)

def wrapped(draw,shape,box,size=C,**style):
    # Draw a shape and its wrapped copies so the cell tiles without seams.
    x0,y0,x1,y1=box
    for dx in (-size,0,size):
        for dy in (-size,0,size):getattr(draw,shape)((x0+dx,y0+dy,x1+dx,y1+dy),**style)

def stripes(colors,width,angle_rows=False):
    im=tint(colors[0],.05);d=ImageDraw.Draw(im)
    for i,x in enumerate(range(0,C,width)):
        if i%2:d.rectangle((x,0,x+width-1,C) if not angle_rows else (0,x,C,x+width-1),fill=colors[1])
    return Image.blend(im,tint(colors[0],.08),.25)

def cloth_check():
    im=tint((146,96,82),.06);d=ImageDraw.Draw(im)
    for x in range(0,C,32):d.line((x,0,x,C),fill=(166,122,102),width=6);d.line((0,x,C,x),fill=(166,122,102),width=6)
    return Image.blend(im,tint((146,96,82),.1),.3)

def cloth_patch():
    im=tint((206,196,170),.07);d=ImageDraw.Draw(im)
    d.rectangle((70,80,170,170),fill=(180,170,140));d.rectangle((70,80,170,170),outline=(130,118,96),width=2)
    for x in range(74,168,8):d.line((x,78,x+4,78),fill=(110,96,78),width=2);d.line((x,172,x+4,172),fill=(110,96,78),width=2)
    return im

def cloth_folds():
    im=tint((128,142,112),.05);d=ImageDraw.Draw(im)
    for x in range(0,C,64):
        for k in range(10):d.line((x+k,0,x+k,C),fill=(116-k,130-k,102-k))
    return soften(im,2)

def blossoms(leaf,petals,count,radius):
    im=tint(leaf,.12,4,16);d=ImageDraw.Draw(im)
    for _ in range(count*2):
        x,y=ar.randrange(C),ar.randrange(C);r=ar.randrange(5,11)
        wrapped(d,'ellipse',(x-r,y-r*.6,x+r,y+r*.6),fill=tuple(int(v*(.8+ar.random()*.3)) for v in leaf))
    for _ in range(count):
        x,y=ar.randrange(C),ar.randrange(C);color=ar.choice(petals)
        for k in range(5):
            a=k*math.tau/5;px,py=x+math.cos(a)*radius,y+math.sin(a)*radius
            wrapped(d,'ellipse',(px-radius*.8,py-radius*.8,px+radius*.8,py+radius*.8),fill=color)
        wrapped(d,'ellipse',(x-2,y-2,x+2,y+2),fill=(214,180,92))
    return soften(im,.6)

def ivy():
    im=tint((86,98,70),.1,4,16);d=ImageDraw.Draw(im)
    for _ in range(140):
        x,y=ar.randrange(C),ar.randrange(C);r=ar.randrange(7,14);g=ar.randrange(-14,14)
        wrapped(d,'ellipse',(x-r,y-r*.7,x+r,y+r*.7),fill=(70+g,92+g,52+g))
    return soften(im,.7)

def petals_on_stone():
    im=tint((182,172,150),.06);d=ImageDraw.Draw(im)
    for y in range(0,C,64):
        for x in range(-128,C,128):d.rectangle((x+(64 if y//64%2 else 0),y,x+(64 if y//64%2 else 0)+127,y+63),outline=(150,140,120),width=2)
    for _ in range(60):
        x,y=ar.randrange(C),ar.randrange(C);color=ar.choice([(196,170,200),(218,206,150),(206,150,150)])
        wrapped(d,'ellipse',(x-3,y-2,x+3,y+2),fill=color)
    return im

def planks(base,horizontal=True,brace=False):
    im=tint(base,.07,4,32);d=ImageDraw.Draw(im)
    for k in range(0,C,64):
        d.line((0,k,C,k) if horizontal else (k,0,k,C),fill=tuple(int(v*.55) for v in base),width=4)
        for x in (18,C-18):
            nx,ny=(x,k+32) if horizontal else (k+32,x)
            d.ellipse((nx-3,ny-3,nx+3,ny+3),fill=(70,66,60))
    if brace:
        wrapped(d,'line',(0,0,C,C),fill=tuple(int(v*.78) for v in base),width=28);wrapped(d,'line',(0,0,C,C),fill=tuple(int(v*.55) for v in base),width=2)
    grain=cell_noise(48).point(lambda v:int(128+(v-128)*.4))
    return Image.composite(im,im.point(lambda v:int(v*.9)),grain)

def tool_board(base):
    im=planks(base,False);d=ImageDraw.Draw(im)
    for y in range(20,C,40):
        for x in range(20,C,40):d.ellipse((x-2,y-2,x+2,y+2),fill=(60,50,40))
    steel,handle=(120,124,122),(110,72,44)
    d.rectangle((40,40,52,150),fill=handle);d.rectangle((26,30,66,52),fill=steel)              # hammer
    d.rectangle((112,46,122,170),fill=steel);d.ellipse((102,26,132,58),fill=steel);d.ellipse((110,32,124,48),fill=base)  # wrench
    d.polygon([(160,40),(226,40),(226,170),(160,140)],fill=steel);d.rectangle((150,30,236,48),fill=handle)  # saw
    for x in range(162,224,6):d.line((x,140,x+3,146),fill=(90,94,92))
    d.rectangle((40,190,214,206),fill=handle);d.rectangle((200,182,232,214),fill=steel)          # chisel
    return im

def clock(rim):
    im=tint((168,156,132),.05);d=ImageDraw.Draw(im)
    d.ellipse((20,20,236,236),fill=rim);d.ellipse((34,34,222,222),fill=(232,224,204))
    for k in range(60):
        a=k*math.tau/60;r0=100 if k%5 else 88
        d.line((128+math.cos(a)*r0,128+math.sin(a)*r0,128+math.cos(a)*104,128+math.sin(a)*104),fill=(60,52,44),width=4 if k%5==0 else 1)
    d.line((128,128,128+math.cos(-1.1)*60,128+math.sin(-1.1)*60),fill=(40,36,32),width=6)
    d.line((128,128,128+math.cos(.6)*84,128+math.sin(.6)*84),fill=(40,36,32),width=3)
    d.ellipse((121,121,135,135),fill=rim)
    return im

def timetable(board,ink):
    im=tint(board,.05);d=ImageDraw.Draw(im);font=ImageFont.load_default()
    d.rectangle((14,14,242,242),outline=ink,width=3);d.line((14,48,242,48),fill=ink,width=2)
    for x in (70,128,186):d.line((x,14,x,242),fill=ink,width=1)
    for row,y in enumerate(range(58,222,16)):
        for col,x in enumerate((20,78,136,194)):
            if col==0:d.text((x,y),f'{6+row:02d}',fill=ink,font=font)
            else:
                for k in range(ar.randrange(1,4)):d.line((x+k*16,y+6,x+k*16+9,y+6),fill=ink,width=2)
    for x in range(20,240,22):d.line((x,30,x+12,30),fill=ink,width=3)
    return soften(im,.4)

life_cells=[
    stripes([(206,196,170),(72,118,122)],32),cloth_check(),cloth_patch(),cloth_folds(),
    blossoms((86,104,70),[(180,150,196),(196,170,210)],40,5),blossoms((96,112,72),[(226,214,160),(232,224,196)],60,4),ivy(),petals_on_stone(),
    planks((140,104,70)),planks((128,94,62),brace=True),tool_board((150,118,84)),planks((112,84,58),False),
    clock((96,78,50)),clock((84,108,98)),timetable((52,62,58),(214,206,180)),timetable((206,196,170),(60,58,52)),
]

def facade(base,rows=2):
    im=tint(base,.06);d=ImageDraw.Draw(im)
    for r in range(rows):
        y=24+r*128
        for x in range(17,C,64):
            d.rectangle((x,y,x+30,y+48),fill=(46,54,58));d.rectangle((x-4,y+48,x+34,y+54),fill=tuple(min(255,v+18) for v in base))
            streak=Image.new('L',(C,C),0);sd=ImageDraw.Draw(streak);sd.rectangle((x+4,y+54,x+26,y+100),fill=60)
            im=Image.composite(im.point(lambda v:int(v*.84)),im,soften(streak,6));d=ImageDraw.Draw(im)
    return im

def roof(base,lines=(0,0,0)):
    im=tint(base,.08,5,28);d=ImageDraw.Draw(im)
    for y in range(0,C,32):d.line((0,y,C,y),fill=tuple(int(v*.72) for v in base),width=3)
    for y in range(0,C,32):
        for x in range((y//32%2)*16,C,32):d.line((x,y,x,y+32),fill=tuple(int(v*.82) for v in base),width=2)
    return im

def tower_bands():
    im=tint((206,194,170),.05);d=ImageDraw.Draw(im)
    for y in range(0,C,64):d.rectangle((0,y,C,y+8),fill=(176,164,140))
    for x in range(23,C,64):d.rounded_rectangle((x,70,x+18,150),radius=9,fill=(52,58,60))
    return im

def gilded():
    im=tint((176,146,90),.1,4,20);g=soften(cell_noise(10).point(lambda v:255 if v>175 else 0),6)
    return Image.composite(Image.new('RGB',(C,C),(104,132,112)),im,g)

def strata():
    im=Image.new('RGB',(C,C));d=ImageDraw.Draw(im)
    for y in range(C):
        v=math.sin(y*math.tau*3/C)*.06+math.sin(y*math.tau*11/C)*.03
        d.line((0,y,C,y),fill=tuple(int(c*(1+v)) for c in (132,122,105)))
    return Image.blend(im,tint((132,122,105),.1),.4)

def grime(kind):
    im=Image.new('RGB',(C,C),(236,232,224));d=ImageDraw.Draw(im)
    if kind=='rain':
        for _ in range(40):
            x=ar.randrange(C);w=ar.randrange(3,9);h=ar.randrange(60,200);y=ar.randrange(C)
            wrapped(d,'rectangle',(x,y,x+w,y+h),fill=(204,200,192))
    elif kind=='soot':
        soot=cell_noise(5).point(lambda v:max(0,v-120)*2)
        im=Image.composite(Image.new('RGB',(C,C),(176,170,162)),im,soften(soot,3))
    elif kind=='moss':
        moss=cell_noise(9).point(lambda v:255 if v>160 else 0)
        im=Image.composite(Image.new('RGB',(C,C),(178,190,160)),im,soften(moss,5))
    else:
        for _ in range(70):
            x,y=ar.randrange(C),ar.randrange(C);r=ar.randrange(3,9)
            wrapped(d,'ellipse',(x-r,y-r,x+r,y+r),fill=(214,214,190))
    return soften(im,1.5)

distance_cells=[
    facade((214,200,174)),facade((206,176,128)),facade((210,182,170)),facade((176,184,160)),
    roof((90,118,130)),roof((150,96,74)),roof((92,132,118)),roof((70,82,90)),
    tower_bands(),gilded(),strata(),tint((150,140,122),.12,3,12),
    grime('rain'),grime('soot'),grime('moss'),grime('lichen'),
]

def atlas(cells,name):
    sheet=Image.new('RGB',(C*4,C*4))
    for i,cell in enumerate(cells):sheet.paste(cell.convert('RGB'),((i%4)*C,(i//4)*C))
    sheet.save(OUT/name,optimize=True)
    return sheet

def mask_wet():
    m=soften(cell_noise(6).point(lambda v:255 if v>150 else 0),5)
    return Image.blend(m,cell_noise(24).point(lambda v:int(v*.35)),.15)

def mask_repair():
    m=Image.new('L',(C,C),0);d=ImageDraw.Draw(m)
    for _ in range(9):
        x,y=ar.randrange(C),ar.randrange(C);w,h=ar.randrange(18,60),ar.randrange(14,44)
        wrapped(d,'rectangle',(x,y,x+w,y+h),fill=ar.randrange(150,230))
    for _ in range(6):
        x,y=ar.randrange(C),ar.randrange(C)
        for k in range(6):
            nx,ny=x+ar.randrange(-22,23),y+ar.randrange(-22,23);wrapped(d,'line',(x,y,nx,ny),fill=255,width=2);x,y=nx%C,ny%C
    return soften(m,.8)

def mask_dust():
    return soften(cell_noise(4).point(lambda v:int(max(0,v-70)*1.4)),4)

def mask_steps():
    m=Image.new('L',(C,C),0);d=ImageDraw.Draw(m)
    for k in range(8):
        y=k*32+8;x=96+(28 if k%2 else 0)
        d.ellipse((x,y,x+16,y+24),fill=210);d.ellipse((x+3,y-9,x+13,y+1),fill=160)
    return soften(m,1.2)

life=atlas(life_cells,'island-life-atlas.png')
distance=atlas(distance_cells,'island-distance-atlas.png')
mask=Image.new('L',(512,512))
for i,cell in enumerate([mask_wet(),mask_repair(),mask_dust(),mask_steps()]):mask.paste(cell,((i%2)*C,(i//2)*C))
mask.save(OUT/'island-mark-mask.png',optimize=True)

# Each cell's saturation and brightness must sit inside the range of the existing plaster, stone, slate and wood maps.
def stats(image):
    hsv=list(image.convert('RGB').convert('HSV').getdata());lum=list(image.convert('L').getdata())
    mean=sum(lum)/len(lum)
    return sum(p[1] for p in hsv)/len(hsv),mean,(sum((v-mean)**2 for v in lum)/len(lum))**.5
reference=[stats(Image.open(OUT/f'{k}-color.jpg')) for k in ('plaster','stone','slate','wood')]
max_saturation=max(r[0] for r in reference);lum_low=min(r[1] for r in reference)*.55;lum_high=max(r[1] for r in reference)*1.12
for name,image in (('life',life),('distance',distance)):
    rows=[]
    for i in range(16):
        saturation,brightness,spread=stats(image.crop(((i%4)*C,(i//4)*C,(i%4+1)*C,(i//4+1)*C)))
        assert saturation<=max_saturation,f'{name} cell {i} saturation {saturation:.0f} exceeds existing maps ({max_saturation:.0f})'
        assert lum_low<=brightness<=lum_high,f'{name} cell {i} brightness {brightness:.0f} outside existing range ({lum_low:.0f}-{lum_high:.0f})'
        rows.append(f'{saturation:.0f}/{brightness:.0f}/{spread:.0f}')
    print(f'{name} atlas cells saturation/brightness/spread:',' '.join(rows))
# Seam check: the wrap-around edge of every cell may differ no more than its sharpest interior edge.
def line_diff(image,a,b,vertical):
    px=image.load();w,h=image.size;total=0
    for k in range(h if vertical else w):
        p,q=(px[a,k],px[b,k]) if vertical else (px[k,a],px[k,b])
        total+=sum(abs(x-y) for x,y in zip(p,q)) if isinstance(p,tuple) else abs(p-q)
    return total/(h if vertical else w)
for name,image,count,size in (('life',life,16,C),('distance',distance,16,C),('mask',mask,4,C)):
    per_row=image.size[0]//size
    for i in range(count):
        cell=image.crop(((i%per_row)*size,(i//per_row)*size,(i%per_row+1)*size,(i//per_row+1)*size))
        for vertical in (True,False):
            interior=max(line_diff(cell,k,k+1,vertical) for k in range(size-1))
            seam=line_diff(cell,size-1,0,vertical)
            assert seam<=interior*1.05+.5,f'{name} cell {i} {"left/right" if vertical else "top/bottom"} seam {seam:.1f} > interior {interior:.1f}'
print('Seam check: every atlas and mask cell tiles without a visible edge.')
print(f'Existing maps saturation/brightness/spread:',' '.join(f'{a:.0f}/{b:.0f}/{c:.0f}' for a,b,c in reference))
print('Generated island life/distance atlases (1024px) and mark mask (512px).')

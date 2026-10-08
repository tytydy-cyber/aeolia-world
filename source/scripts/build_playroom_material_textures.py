from pathlib import Path
from PIL import Image, ImageDraw
import random
import math

out = Path(__file__).parents[2] / "outputs/assets/playroom/textures"
out.mkdir(parents=True, exist_ok=True)
random.seed(4)

fabric = Image.new("RGB", (128, 128), (238, 236, 230))
d = ImageDraw.Draw(fabric)
for i in range(0, 128, 4):
    c = 180 + random.randrange(25)
    d.line((i, 0, i, 127), fill=(c, c + 5, c + 8), width=1)
    d.line((0, i + 2, 127, i + 2), fill=(c + 10, c + 7, c), width=1)
fabric.save(out / "fabric-weave.png", optimize=True)

plastic = Image.new("RGB", (128, 128), (244, 244, 240))
d = ImageDraw.Draw(plastic)
for _ in range(420):
    x, y = random.randrange(128), random.randrange(128)
    v = random.randrange(218, 240)
    d.point((x, y), fill=(v, v, v + 2))
plastic.save(out / "plastic-speckle.png", optimize=True)

rug = Image.new("RGB", (128, 128), (238, 236, 228))
d = ImageDraw.Draw(rug)
for x, y, r in [(20, 28, 10), (88, 78, 13)]:
    c = (198, 204, 205)
    d.ellipse((x-r, y-r//2, x+r, y+r//2), fill=c)
    d.ellipse((x-r//2, y-r, x+r//2, y+r//2), fill=c)
for x, y, r in [(58, 22, 7), (111, 39, 6), (42, 101, 8), (103, 112, 5)]:
    pts=[]
    for i in range(10):
        a=-math.pi/2+i*math.pi/5
        rr=r if i%2==0 else r*.42
        pts.append((x+math.cos(a)*rr,y+math.sin(a)*rr))
    d.polygon(pts,fill=(190,184,176))
rug.save(out / "rug-pattern.png", optimize=True)

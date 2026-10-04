"""Generate the four small, dependency-free playroom texture assets."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math
import random

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/assets/playroom/textures"
OUT.mkdir(parents=True, exist_ok=True)
N = 1024


def periodic_noise(size, grid, seed):
    rng = random.Random(seed)
    tile = Image.new("L", (grid, grid))
    tile.putdata([rng.randrange(256) for _ in range(grid * grid)])
    tiled = Image.new("L", (grid * 3, grid * 3))
    for x in range(3):
        for y in range(3):
            tiled.paste(tile, (x * grid, y * grid))
    return tiled.resize((size * 3, size * 3), Image.Resampling.BICUBIC).crop((size, size, size * 2, size * 2))


def seamless(image):
    """Make opposite border pixels identical before JPEG compression."""
    px = image.load()
    for x in range(image.width):
        px[x, image.height - 1] = px[x, 0]
    for y in range(image.height):
        px[image.width - 1, y] = px[0, y]
    return image


def wallpaper():
    coarse = periodic_noise(N, 7, 110)
    fine = periodic_noise(N, 48, 111)
    image = Image.new("RGB", (N, N))
    cp, fp, out = coarse.load(), fine.load(), image.load()
    for y in range(N):
        # A real paper join every quarter-width; the outer edge itself remains tileable.
        for x in range(N):
            shade = (cp[x, y] - 128) * .055 + (fp[x, y] - 128) * .018
            seam = -5 * max(0, 1 - min(x % 256, 256 - x % 256) / 3)
            out[x, y] = tuple(max(0, min(255, int(v + shade + seam))) for v in (128, 194, 218))
    return seamless(image.filter(ImageFilter.GaussianBlur(.25)))


def carpet():
    fine = periodic_noise(N, 96, 210)
    image = Image.new("RGB", (N, N), (47, 103, 119))
    fp, out = fine.load(), image.load()
    for y in range(N):
        for x in range(N):
            shade = (fp[x, y] - 128) * .018
            # Barely compressed tile edges, visible nearby without reading as a wave at distance.
            pressure = -2.2 * max(0, 1 - min(x % 128, 128 - x % 128, y % 128, 128 - y % 128) / 2)
            shade += pressure
            out[x, y] = (max(0, int(47 + shade)), max(0, int(103 + shade)), max(0, int(119 + shade)))
    draw, rng = ImageDraw.Draw(image), random.Random(211)
    flecks = [(220, 178, 72), (183, 70, 70), (83, 151, 103), (190, 201, 184)]
    for _ in range(8200):
        x, y, length = rng.randrange(N), rng.randrange(N), rng.randrange(1, 4)
        color = rng.choice(flecks) if rng.random() < .065 else rng.choice([(58, 118, 131), (35, 83, 101), (72, 126, 132)])
        for dx in (-N, 0, N):
            for dy in (-N, 0, N):
                draw.line((x + dx, y + dy, x + dx + length, y + dy + rng.choice((-1, 0, 1))), fill=color)
    return seamless(image)


def worn_plastic():
    image = Image.new("RGB", (N, N))
    colors = [(188, 63, 62), (219, 176, 55), (75, 144, 102), (55, 113, 170)]
    for index, base in enumerate(colors):
        cell = Image.new("RGB", (512, 512), base)
        noise = periodic_noise(512, 20, 310 + index)
        np, cp = noise.load(), cell.load()
        for y in range(512):
            for x in range(512):
                shade = (np[x, y] - 128) * .055
                cp[x, y] = tuple(max(0, min(255, int(v + shade))) for v in base)
        draw, rng = ImageDraw.Draw(cell), random.Random(320 + index)
        for _ in range(110):
            x, y, length = rng.randrange(512), rng.randrange(512), rng.randrange(8, 54)
            tone = tuple(min(255, v + rng.randrange(14, 32)) for v in base)
            for dx in (-512, 0, 512):
                for dy in (-512, 0, 512):
                    draw.line((x + dx, y + dy, x + dx + length, y + dy + rng.randrange(-3, 4)), fill=tone, width=rng.choice((1, 1, 2)))
        seamless(cell)
        image.paste(cell, ((index % 2) * 512, (index // 2) * 512))
    return image


def cloud_atlas():
    atlas = Image.new("RGBA", (N, N))
    for index in range(12):
        cell = Image.new("RGBA", (256, 256))
        mask = Image.new("L", cell.size)
        draw, rng = ImageDraw.Draw(mask), random.Random(410 + index)
        cx, cy = 128 + rng.randrange(-12, 13), 132 + rng.randrange(-10, 11)
        for _ in range(5 + index % 4):
            rx, ry = rng.randrange(24, 55), rng.randrange(18, 39)
            x, y = cx + rng.randrange(-62, 63), cy + rng.randrange(-24, 25)
            draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=rng.randrange(205, 246))
        mask = mask.filter(ImageFilter.GaussianBlur(5 + index % 3))
        cloud = Image.new("RGBA", cell.size, (245, 241, 224, 0))
        cloud.putalpha(mask)
        cell.alpha_composite(cloud)
        atlas.alpha_composite(cell, ((index % 4) * 256, (index // 4) * 256))
    return atlas


wallpaper().save(OUT / "sky-wallpaper.jpg", quality=88, optimize=True, progressive=True)
carpet().save(OUT / "carpet.jpg", quality=86, optimize=True, progressive=True)
worn_plastic().save(OUT / "worn-plastic-atlas.png", optimize=True)
cloud_atlas().save(OUT / "clouds-12-atlas.png", optimize=True)
print("Generated playroom textures in", OUT)

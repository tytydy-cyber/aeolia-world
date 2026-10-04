"""Small acceptance check for generated playroom textures."""
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
import hashlib

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "outputs/assets/playroom/textures"
SPECS = {
    "sky-wallpaper.jpg": (1024, 1024),
    "clouds-12-atlas.png": (1024, 1024),
    "carpet.jpg": (1024, 1024),
    "worn-plastic-atlas.png": (1024, 1024),
}


def edge_error(image):
    image = image.convert("RGB")
    lr = ImageChops.difference(image.crop((0, 0, 1, image.height)), image.crop((image.width - 1, 0, image.width, image.height)))
    tb = ImageChops.difference(image.crop((0, 0, image.width, 1)), image.crop((0, image.height - 1, image.width, image.height)))
    return max(max(ImageStat.Stat(lr).mean), max(ImageStat.Stat(tb).mean))


for name, size in SPECS.items():
    image = Image.open(ASSETS / name)
    assert image.size == size, (name, image.size)

for name in ("sky-wallpaper.jpg", "carpet.jpg"):
    assert edge_error(Image.open(ASSETS / name)) < 6, (name, edge_error(Image.open(ASSETS / name)))

sky_mean = ImageStat.Stat(Image.open(ASSETS / "sky-wallpaper.jpg")).mean
carpet_mean = ImageStat.Stat(Image.open(ASSETS / "carpet.jpg")).mean
assert sky_mean[2] > sky_mean[1] > sky_mean[0], sky_mean
assert carpet_mean[2] > carpet_mean[1] > carpet_mean[0], carpet_mean
carpet = Image.open(ASSETS / "carpet.jpg").convert("L")
low_frequency = carpet.resize((16, 16), Image.Resampling.BOX)
assert ImageStat.Stat(low_frequency).stddev[0] < 2.2, ImageStat.Stat(low_frequency).stddev[0]
assert ImageStat.Stat(carpet).stddev[0] > 3, ImageStat.Stat(carpet).stddev[0]

plastic = Image.open(ASSETS / "worn-plastic-atlas.png")
means = []
for row in range(2):
    for col in range(2):
        cell = plastic.crop((col * 512, row * 512, col * 512 + 512, row * 512 + 512))
        assert edge_error(cell) < 8, (row, col, edge_error(cell))
        means.append(ImageStat.Stat(cell).mean)
assert means[0][0] > means[0][1] and means[1][0] > 180 and means[2][1] > means[2][0] and means[3][2] > means[3][0]

clouds = Image.open(ASSETS / "clouds-12-atlas.png").convert("RGBA")
hashes = set()
for index in range(12):
    x, y = index % 4 * 256, index // 4 * 256
    alpha = clouds.crop((x, y, x + 256, y + 256)).getchannel("A")
    ratio = sum(alpha.getdata()) / (255 * 256 * 256)
    assert .04 < ratio < .55, (index, ratio)
    hashes.add(hashlib.sha256(alpha.tobytes()).digest())
assert len(hashes) == 12

total = sum((ASSETS / name).stat().st_size for name in SPECS)
assert total < 1_800_000, total
print(f"PASS: 4 textures, 12 unique clouds, seamless edges, {total / 1024:.0f} KiB total")

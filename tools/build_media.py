"""Build the site's media (run once; outputs are committed under assets/media/).

- Earth renders: orthographic Earth from NASA Blue Marble: Next Generation
  (July 2004, topography + bathymetry, NASA Earth Observatory), lit from the
  upper right (the brand's one light source, the star). Credited on every
  page that shows them.
- Film loops: short silent loops cut from the frame sequences of the public
  BirunIQ teaser (take 6, 2026-11-08), the same footage as the trailer. All data in it is synthetic demonstration
  data or publicly available data (the film's own disclosure card).

Usage:  python tools/build_media.py [earth] [loops] [poster]
Sources are read from outside the repo (paths below) and never committed.
"""
import math
import pathlib
import subprocess
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "media"
NASA = pathlib.Path(r"D:/Platform/brand/biruniq-tshirt-space/source/nasa/world.topo.bathy.200407.3x21600x10800.jpg")
FILM = pathlib.Path(r"D:/Platform/film-output/teaser-v3/2026-11-08-take6")


def earth(name, lat0, lon0, px, light=(0.55, 0.62, 0.56)):
    import numpy as np
    Image.MAX_IMAGE_PIXELS = None
    ext = 1.12
    N = px * 2
    tex = np.asarray(Image.open(NASA).convert("RGB"), dtype=np.uint8)
    th, tw = tex.shape[:2]
    ax = (np.arange(N, dtype=np.float32) + 0.5) / N * 2 * ext - ext
    u, v = np.meshgrid(ax, -ax)
    r2 = u * u + v * v
    inside = r2 <= 1.0
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    la0, lo0 = math.radians(lat0), math.radians(lon0)
    lat = np.arcsin(np.clip(v * math.cos(la0) + z * math.sin(la0), -1, 1))
    lon = lo0 + np.arctan2(u, z * math.cos(la0) - v * math.sin(la0))
    tx = ((lon / (2 * math.pi) + 0.5) % 1.0 * tw).astype(np.int32) % tw
    ty = np.clip(((0.5 - lat / math.pi) * th).astype(np.int32), 0, th - 1)
    col = tex[ty, tx].astype(np.float32) / 255.0
    del tex, tx, ty, lat, lon
    col = np.power(col, 0.9)
    L = np.array(light, dtype=np.float32); L /= np.linalg.norm(L)
    ndl = u * L[0] + v * L[1] + z * L[2]
    t = np.clip((ndl + 0.10) / 0.40, 0, 1); day = t * t * (3 - 2 * t)
    shade = 0.03 + 0.97 * day * (0.6 + 0.4 * np.clip(ndl, 0, 1))
    col *= shade[..., None]
    limb = np.power(1 - z, 2.6)
    atm = np.array([0.35, 0.62, 1.0], dtype=np.float32)
    col += (atm * 0.55)[None, None, :] * (limb * (0.12 + 0.88 * day))[..., None]
    h = np.array([L[0], L[1], L[2] + 1.0]); h /= np.linalg.norm(h)
    spec = np.power(np.clip(u * h[0] + v * h[1] + z * h[2], 0, 1), 60) * 0.35
    water = np.clip((col[..., 2] - col[..., 0]) * 4, 0, 1)
    col += (spec * water)[..., None] * np.array([1.0, 0.95, 0.85], dtype=np.float32)
    r = np.sqrt(r2)
    side = np.clip((u * L[0] + v * L[1]) / np.maximum(r, 1e-6) * 0.5 + 0.55, 0.15, 1)
    glow = np.exp(-np.clip(r - 1, 0, None) / 0.022) * side * (~inside)
    rgb = np.where(inside[..., None], col, atm[None, None, :] * 1.05)
    alpha = np.where(inside, 1.0, np.clip(glow * 0.9, 0, 1))
    img = np.dstack([np.clip(rgb, 0, 1), alpha[..., None]])
    im = Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA").resize((px, px), Image.LANCZOS)
    p = OUT / f"{name}.webp"
    im.save(p, "WEBP", quality=88, method=6)
    print(p, p.stat().st_size // 1024, "KB", f"(extent {ext} radii)")


# scene -> (clip folder, start frame fraction, seconds)
LOOPS = {
    "watchfloor": ("wf-command", 0.20, 6),
    "maritimelens": ("lens", 0.30, 6),
    "sentry": ("sentry", 0.25, 6),
    "guardian": ("guardian-3d", 0.25, 6),
    "grid": ("grid-ops", 0.30, 6),
    "flux": ("flux", 0.30, 6),
    "petrocore": ("petro-monitor", 0.30, 6),
    "milepost": ("milepost", 0.25, 6),
    "tower": ("tower", 0.25, 6),
    "spilltrace": ("spill", 0.30, 6),
    "floodsurge": ("flood", 0.30, 6),
    "greenscope": ("groundwater", 0.30, 6),
    "harvest": ("harvest-fields", 0.30, 6),
    "atlas": ("smartcity", 0.25, 6),
    "terra": ("terra-flow", 0.25, 6),
    "africa": ("africa-port", 0.25, 6),
    "blueprint": ("blueprint", 0.25, 6),
    "platform": ("enterprise", 0.20, 6),
    "admin": ("admin", 0.20, 6),
    "field": ("field", 0.20, 6),
}
FPS = 30


def loops(only=None):
    (OUT / "loops").mkdir(parents=True, exist_ok=True)
    for key, (folder, frac, secs) in LOOPS.items():
        if only and key not in only:
            continue
        frames = sorted((FILM / "clips" / folder).glob("f*.jpg"))
        n = secs * FPS
        start = max(0, min(len(frames) - n, int(len(frames) * frac)))
        mp4 = OUT / "loops" / f"{key}.mp4"
        poster = OUT / "loops" / f"{key}.webp"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-start_number", str(start),
            "-i", str(FILM / "clips" / folder / "f%05d.jpg"), "-frames:v", str(min(n, len(frames))),
            "-vf", "scale=1280:-2:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "slow",
            "-crf", "29", "-an", "-movflags", "+faststart", str(mp4)], check=True)
        Image.open(frames[start]).convert("RGB").resize((1280, 720), Image.LANCZOS).save(
            poster, "WEBP", quality=78, method=6)
        print(f"{key:13s} {mp4.stat().st_size / 1e6:5.2f} MB  poster {poster.stat().st_size // 1024} KB")


def trailer_poster():
    im = Image.open(FILM / "plate" / "plate-16x9-lockup.png").convert("RGB").resize((1600, 900), Image.LANCZOS)
    p = OUT / "trailer-poster.webp"
    im.save(p, "WEBP", quality=84, method=6)
    print(p, p.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    what = set(sys.argv[1:]) or {"earth", "loops", "poster"}
    if "earth" in what:
        earth("earth-americas", 30.0, -95.0, 1800)   # US first (Steven, 2026-10-19)
        earth("earth-biruni", 32.7, 72.9, 1400)       # Nandana, where al-Biruni measured the Earth
    if "loops" in what:
        loops()
    if "poster" in what:
        trailer_poster()

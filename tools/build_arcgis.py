"""Publish the ArcGIS experience mock-up on biruniq.com.

    python tools/build_arcgis.py <path to arcgis-ux-preview.html>

The source is the single-file mock-up (published as a claude.ai artifact). This
turns it into a normal web page for the site:
  * every embedded data: URI (videos, key art, imagery, posters) becomes a file
    under assets/arcgis/, named by content hash, so the page is small and the
    media cache;
  * the Google Fonts link is removed: the site loads nothing from a third party,
    and the mock-up's font stacks fall back to system faces;
  * it is wrapped in a full HTML document as arcgis/experience.html, which
    arcgis.html embeds and links to full screen.
"""
import hashlib
import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "arcgis"
ASSET_DIR = ROOT / "assets" / "arcgis"
EXT = {"image/webp": "webp", "image/png": "png", "image/jpeg": "jpg", "video/mp4": "mp4", "image/svg+xml": "svg"}


def main(src: Path) -> None:
    s = src.read_text(encoding="utf-8")
    s = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/[^"]*">\s*', "", s)
    s = re.sub(r'<meta name="claude:[^>]*>\s*', "", s)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for old in ASSET_DIR.iterdir():
        old.unlink()
    written = {}

    def repl(m: re.Match) -> str:
        mime, b64 = m.group(1), m.group(2)
        data = base64.b64decode(b64)
        name = f"{hashlib.sha256(data).hexdigest()[:16]}.{EXT[mime]}"
        if name not in written:
            (ASSET_DIR / name).write_bytes(data)
            written[name] = len(data)
        return f"../assets/arcgis/{name}"

    s = re.sub(r"data:([a-z]+/[a-z0-9.+-]+);base64,([A-Za-z0-9+/=]+)", repl, s)
    if re.search(r"https?://(?!biruniq\.com|youtu|www\.youtube)[a-z0-9.-]+\.[a-z]{2,}/[^\"' ]*\.(?:js|css|woff2?)", s):
        raise SystemExit("the page still loads a script, stylesheet or font from another host")
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    title = m.group(1) if m else "BirunIQ for ArcGIS users"
    s = s.replace(m.group(0), "", 1) if m else s
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<title>{title} · BirunIQ</title>
<meta name="description" content="An interactive mock-up of BirunIQ for ArcGIS users: an example organisation, demo utility data on real public map data." />
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml" />
<style>html,body{{margin:0}}body{{font:14px system-ui,-apple-system,"Segoe UI",sans-serif}}[hidden]{{display:none!important}}</style>
</head>
<body>
{s}
</body>
</html>
"""
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "experience.html").write_text(doc, encoding="utf-8")
    total = sum(written.values())
    print(f"experience.html {len(doc.encode()) / 1e6:.2f} MB; {len(written)} assets {total / 1e6:.2f} MB")


if __name__ == "__main__":
    main(Path(sys.argv[1]))

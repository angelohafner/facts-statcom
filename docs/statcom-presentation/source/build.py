"""Rebuild the entire offline STATCOM slide deck using only the Python standard library.

This script reads source fragments and inlines the original, already-versioned
SVG equipment drawings from examples/gallery. It needs no network connection.
"""

from pathlib import Path
import re

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[2]
OUTPUT = SOURCE.parent / "index.html"
GALLERY = PROJECT / "examples" / "gallery"
ASSETS = ("two-level", "npc", "chb-star", "chb-delta", "mmc")


def build() -> Path:
    """Assemble a standalone HTML file and keep topology SVG source editable."""
    css = (SOURCE / "style.css").read_text(encoding="utf-8")
    slides = (SOURCE / "slides.html").read_text(encoding="utf-8")
    scripts = "\n".join((SOURCE / name).read_text(encoding="utf-8")
                        for name in ("model.js", "graphics.js", "charts.js", "ui.js"))
    page = (SOURCE / "page.html").read_text(encoding="utf-8")
    page = page.replace("__CSS__", css).replace("__SLIDES__", slides).replace("__JS__", scripts)

    for name in ASSETS:
        svg_path = GALLERY / f"{name}.svg"
        if svg_path.is_file():
            svg = svg_path.read_text(encoding="utf-8")
            svg = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", svg)
            if not svg.lstrip().startswith("<svg"):
                raise ValueError(f"Unexpected SVG format: {svg_path}")
            if re.search(r"<(?:script|foreignObject)\b|\b(?:href|src)\s*=\s*['\"]https?://", svg, re.I):
                raise ValueError(f"Unsupported script/external resource in {svg_path}")
            page = page.replace(f"<!-- GALLERY_ASSET:{name} -->", svg)
        else:
            print(f"Warning: no {svg_path}; an internal vector fallback will be used")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Built standalone presentation: {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    return OUTPUT


if __name__ == "__main__":
    build()

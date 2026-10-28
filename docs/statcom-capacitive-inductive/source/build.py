"""Build the fully standalone STATCOM lesson from reusable source assets."""

from __future__ import annotations

import base64
import re
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = HERE.parent / "index.html"
FIGURES = {
    "PHASOR_CAPACITIVE": "phasor-capacitive",
    "PHASOR_INDUCTIVE": "phasor-inductive",
    "WAVEFORMS_CAPACITIVE": "waveforms-capacitive",
    "WAVEFORMS_INDUCTIVE": "waveforms-inductive",
    "REACTIVE_POWER_VS_E": "reactive-power-vs-e",
    "REACTIVE_CURRENT_VS_E": "reactive-current-vs-e",
}


def build() -> Path:
    """Embed the source figures unchanged, and inline all required CSS and JavaScript."""
    html = (HERE / "template.html").read_text(encoding="utf-8")
    substitutions = {
        "/* INLINE_STYLES */": (HERE / "styles.css").read_text(encoding="utf-8"),
        "/* INLINE_MODEL */": (HERE / "model.js").read_text(encoding="utf-8"),
        "/* INLINE_FIGURES */": (HERE / "figures.js").read_text(encoding="utf-8"),
        "/* INLINE_APP */": (HERE / "app.js").read_text(encoding="utf-8"),
    }
    gallery = ROOT / "examples" / "operation" / "gallery"
    for placeholder, filename in FIGURES.items():
        content = (gallery / f"{filename}.svg").read_bytes()
        svg = ET.fromstring(content)
        if svg.tag != "{http://www.w3.org/2000/svg}svg":
            raise ValueError(f"Unexpected figure format for {filename}")
        if re.search(rb"<script\b|<foreignObject\b|(?:href|src)=[\"']https?://", content, re.I):
            raise ValueError(f"Figure {filename} contains an external or active resource")
        substitutions[f"__ASSET_{placeholder}__"] = (
            "data:image/svg+xml;base64," + base64.b64encode(content).decode("ascii")
        )
    for target, content in substitutions.items():
        if html.count(target) != 1:
            raise ValueError(f"Expected exactly one placeholder {target!r}")
        html = html.replace(target, content)
    if re.search(r"<(?:script|link)[^>]+(?:src|href)\s*=", html, re.I):
        raise ValueError("The presentation must not require external script or CSS")
    if "__ASSET_" in html or "INLINE_" in html:
        raise ValueError("Unresolved HTML build placeholders")
    OUTPUT.write_text(html.rstrip() + "\n", encoding="utf-8")
    return OUTPUT


if __name__ == "__main__":
    target = build()
    print(f"Built {target} ({target.stat().st_size:,} bytes)")

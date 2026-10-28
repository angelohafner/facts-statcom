"""Structural validation of the offline STATCOM teaching deck."""

from html.parser import HTMLParser
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1]
HTML = BASE / "docs" / "statcom-presentation" / "index.html"
SOURCE = BASE / "docs" / "statcom-presentation" / "source"


class Tags(HTMLParser):
    """Track inline resources, slides and screen-reader labels."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.template_depth = 0
        self.tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "template":
            self.template_depth += 1
        self.tags.append((tag, data))
        # SVG IDs inside inert HTML templates are isolated until one is cloned.
        if data.get("id") and (self.template_depth == 0 or tag == "template"):
            self.ids.append(data["id"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "template":
            self.template_depth -= 1


def test_single_html_has_all_fifteen_scenes():
    parser = Tags()
    parser.feed(HTML.read_text(encoding="utf-8"))
    assert len(parser.ids) == len(set(parser.ids)), "Duplicate HTML id"
    slides = [a["id"] for _, a in parser.tags if a.get("class", "").split().count("slide")]
    assert slides == [f"slide-{i}" for i in range(1, 16)]


def test_no_external_css_scripts_or_images():
    parser = Tags()
    parser.feed(HTML.read_text(encoding="utf-8"))
    for tag, attrs in parser.tags:
        if tag in {"script", "img", "iframe", "link", "source"}:
            assert not attrs.get("src")
            assert not (tag == "link" and attrs.get("rel") == "stylesheet")
    assert len([tag for tag, _ in parser.tags if tag == "script"]) == 1
    assert len([tag for tag, _ in parser.tags if tag == "style"]) == 1


def test_all_five_topologies_are_embedded_when_gallery_exists():
    data = HTML.read_text(encoding="utf-8")
    for name in ("two-level", "npc", "chb-star", "chb-delta", "mmc"):
        assert f'id="asset-{name}"' in data
        if (BASE / "examples" / "gallery" / f"{name}.svg").exists():
            chunk = data.split(f'<template id="asset-{name}">', 1)[1].split('</template>', 1)[0]
            assert "<svg" in chunk, name
            assert f"GALLERY_ASSET:{name}" not in chunk


def test_model_and_presentation_engines_remain_separate():
    model = (SOURCE / "model.js").read_text(encoding="utf-8")
    graphics = (SOURCE / "graphics.js").read_text(encoding="utf-8")
    ui = (SOURCE / "ui.js").read_text(encoding="utf-8")
    assert "class STATCOMModel" in model and "class VoltageController" in model
    assert "class PhasorRenderer" in graphics and "class CircuitRenderer" in graphics
    assert "class InteractiveControls" in ui and "class SlideManager" in ui
    assert "data-controls=\"lab\"" in (SOURCE / "slides.html").read_text(encoding="utf-8")
    assert not re.search(r"<script[^>]+src\s*=", HTML.read_text(encoding="utf-8"), re.I)

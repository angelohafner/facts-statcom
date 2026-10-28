"""SVG XML integrity, editable symbols, CLI and optional raster outputs."""

import json
from dataclasses import replace
from xml.etree import ElementTree as ET

import pytest

from facts_statcom.cli import main
from facts_statcom.model import presets
from facts_statcom.renderer import STATCOMRenderer, render_svg
from facts_statcom.svg import SVG_NS, SVGCanvas, Theme


def _groups(tree, device):
    return [e for e in tree.iter() if e.attrib.get("data-device") == device]


@pytest.mark.parametrize("name", list(presets()))
def test_all_diagrams_valid_editable_svg(name, tmp_path):
    cfg = presets()[name]
    output = render_svg(cfg, tmp_path / f"{name}.svg")
    assert output.is_file() and output.stat().st_size > 2500
    root = ET.parse(output).getroot()
    assert root.tag == f"{{{SVG_NS}}}svg"
    assert root.find(f"{{{SVG_NS}}}title") is not None
    ids = [e.attrib["id"] for e in root.iter() if "id" in e.attrib]
    assert len(ids) == len(set(ids)), f"Duplicate SVG IDs in {name}"
    assert any(e.tag.endswith("text") for e in root.iter()), name
    assert any(e.tag.endswith("tspan") for e in root.iter()) or name == "control"
    assert not any(e.tag.endswith("image") for e in root.iter()), name


@pytest.mark.parametrize("name,igbt,diode,capacitor", [
    ("two-level", 6, 6, 1),
    ("npc", 12, 18, 2),
    ("chb-star", 24, 24, 6),
    ("chb-delta", 24, 24, 6),
    ("mmc", 24, 24, 12),
    ("complete", 6, 6, 1),
])
def test_actual_device_counts(name, igbt, diode, capacitor, tmp_path):
    root = ET.parse(render_svg(presets()[name], tmp_path / "test.svg")).getroot()
    assert len(_groups(root, "IGBT")) == igbt
    assert len(_groups(root, "diode")) == diode
    assert len(_groups(root, "capacitor")) == capacitor
    for item in _groups(root, "diode"):
        assert item.attrib.get("data-direction") == "up"
    for item in _groups(root, "IGBT"):
        assert item.attrib["data-collector"] == "top"
        assert item.attrib["data-emitter"] == "bottom"


def test_compatibility_with_svc_svg_contract():
    assert Theme.__dataclass_fields__.keys() >= {
        "ink", "muted", "accent", "reactor", "capacitor", "paper", "canvas",
        "border", "font", "math_font"
    }
    canvas = SVGCanvas(320, 210)
    g = canvas.layer("Scientific notation", "math-layer")
    canvas.math(g, 90, 100, [("α", "variable"), (" = ", "roman"),
                             ("90", "roman"), ("°", "unit")])
    root = ET.fromstring(canvas.as_svg_bytes())
    text = next(e for e in root.iter() if e.attrib.get("data-math-notation") == "mixed")
    items = list(text)
    assert items[0].attrib["font-style"] == "italic"
    assert items[3].attrib["font-style"] == "normal"


def test_renderer_is_single_use():
    r = STATCOMRenderer(presets()["two-level"])
    r.render()
    with pytest.raises(RuntimeError):
        r.render()


@pytest.mark.parametrize("name,n,expected", [
    ("chb-star", 3, 9),
    ("chb-delta", 1, 3),
    ("mmc", 3, 18),
])
def test_configurable_module_counts(name, n, expected, tmp_path):
    cfg = presets()[name]
    cfg = (replace(cfg, submodules_per_arm=n) if name == "mmc"
           else replace(cfg, cells_per_phase=n))
    root = ET.parse(render_svg(cfg, tmp_path / "configured.svg")).getroot()
    kind = "MMC-submodule" if name == "mmc" else "H-bridge"
    assert len(_groups(root, kind)) == expected


def test_cli_all_and_manifest(tmp_path):
    assert main(["--all", "--output-dir", str(tmp_path)]) == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == 8
    assert all((tmp_path / row["files"][0]).is_file() for row in manifest)


def test_cli_custom_json(tmp_path):
    cfg = tmp_path / "user.json"
    cfg.write_text(json.dumps(replace(presets()["chb-delta"],
                            cells_per_phase=3).to_dict()), encoding="utf-8")
    output = tmp_path / "results"
    assert main(["--config", str(cfg), "--output-dir", str(output)]) == 0
    assert (output / "user.svg").exists()

"""Guard the offline STATCOM lesson and parity with the Python phasor model."""

from __future__ import annotations

import base64
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from facts_statcom.operation.physics import CouplingModel

ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "docs" / "statcom-capacitive-inductive-lesson.md"
PACKAGE = ROOT / "docs" / "statcom-capacitive-inductive"
HTML = PACKAGE / "index.html"
FIGURE_NAMES = (
    "phasor-capacitive", "phasor-inductive",
    "waveforms-capacitive", "waveforms-inductive",
    "reactive-power-vs-e", "reactive-current-vs-e",
)


def test_lesson_has_four_steps_and_reuses_six_original_figures() -> None:
    content = LESSON.read_text(encoding="utf-8")
    assert content.count("## Step ") == 4
    for name in FIGURE_NAMES:
        assert f"../examples/operation/gallery/{name}.svg" in content
    for concept in ("current reference", "rated", "PWM", "\\delta", "180°"):
        assert concept.casefold() in content.casefold()


def test_offline_html_has_five_navigation_sections_and_one_master_slider() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert html.count('class="lesson-section') == 5
    assert html.count('class="nav-step') == 5 or html.count('nav-step ') == 5
    assert html.count('id="slider-E"') == 1
    assert html.count('id="lab-circuit"') == 1
    assert html.count('id="lab-phasors"') == 1
    assert html.count('id="lab-waveforms"') == 1
    assert html.count('id="lab-q-curve"') == 1
    assert html.count('id="lab-i-curve"') == 1
    assert re.search(r"<script\b[^>]*\bsrc\s*=", html, re.I) is None
    assert re.search(r"<link\b[^>]*\bhref\s*=", html, re.I) is None
    assert "https://" not in html and "http://" not in html
    assert "__ASSET_" not in html
    assert "INLINE_" not in html


def test_all_original_svg_figures_embedded_bit_exactly() -> None:
    html = HTML.read_text(encoding="utf-8")
    encoded = re.findall(r'data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)', html)
    assert len(encoded) == len(FIGURE_NAMES)
    extracted = [base64.b64decode(x) for x in encoded]
    originals = [
        (ROOT / "examples" / "operation" / "gallery" / f"{name}.svg").read_bytes()
        for name in FIGURE_NAMES
    ]
    assert extracted == [originals[0], originals[2], originals[1], originals[3], originals[4], originals[5]]
    for image in extracted:
        assert ET.fromstring(image).tag == "{http://www.w3.org/2000/svg}svg"


def test_three_base_examples_agree_with_python_physics() -> None:
    coupling = CouplingModel(v_pcc_pu=1.0, x_coupling_pu=.2, i_limit_pu=1.0)
    for E, expected_q, expected_i in ((.9,-.5,.5),(1.0,0,0),(1.1,.5,-.5)):
        operating = coupling.operating_point(E)
        assert operating.p_injected_pu == pytest.approx(0,abs=1e-12)
        assert operating.q_injected_pu == pytest.approx(expected_q,abs=1e-12)
        assert operating.i_injected.imag == pytest.approx(expected_i,abs=1e-12)
        assert operating.current_within_rating


def test_lab_math_formatting_uses_mathml_and_roman_numbers() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert '<math display="block">' in html
    assert "math mn,.formula mtext" in html or "font-style:normal" in html
    assert "function point(parameters)" in html
    assert "function waveforms(parameters, angleDegrees)" in html
    assert "STACOMPhysics" not in html


@pytest.mark.skipif(not shutil.which("node"), reason="Node is optional for the Python package")
def test_javascript_and_python_phasors_are_numerically_equivalent() -> None:
    """Use Node to evaluate the real lesson script, not a copied reference equation."""
    from random import Random

    generator = Random(88042)
    inputs = [
        {"E":generator.uniform(.75,1.25), "V":generator.uniform(.85,1.15),
         "X":generator.uniform(.10,.40),"Imax":generator.uniform(.5,1.5),
         "theta":generator.uniform(0,360)} for _ in range(60)
    ]
    source = (PACKAGE / "source" / "model.js").read_text(encoding="utf-8")
    js = source + "\nconst cases = " + json.dumps(inputs) + ";\n"
    js += "process.stdout.write(JSON.stringify(cases.map(({theta,...p}) => ({point:STATCOMPhysics.point(p), wave:STATCOMPhysics.waveforms(p,theta)}))));"
    completed = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True)
    output = json.loads(completed.stdout)
    for p, actual in zip(inputs,output):
        model = CouplingModel(v_pcc_pu=p["V"], x_coupling_pu=p["X"], i_limit_pu=p["Imax"])
        reference = model.operating_point(p["E"])
        point = actual["point"]
        assert point["Q"] == pytest.approx(reference.q_injected_pu, rel=1e-12,abs=1e-12)
        assert point["Ireal"] == pytest.approx(reference.i_injected.real, abs=1e-12)
        assert point["Iimag"] == pytest.approx(reference.i_injected.imag, abs=1e-12)
        assert point["Iabs"] == pytest.approx(reference.current_magnitude_pu, rel=1e-12)
        assert point["withinRating"] == reference.current_within_rating
        time=p["theta"]/(360*model.frequency_hz)
        v,e,i=model.instantaneous_fundamentals([time],p["E"])
        assert actual["wave"]["v"] == pytest.approx(v[0],abs=1e-12)
        assert actual["wave"]["e"] == pytest.approx(e[0],abs=1e-12)
        if reference.current_magnitude_pu > 1e-12:
            assert actual["wave"]["i"] == pytest.approx(i[0],abs=1e-12)
        else:
            assert math.isclose(actual["wave"]["i"],0,abs_tol=1e-12)

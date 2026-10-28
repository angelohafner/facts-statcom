"""Check the offline technical visual style and mathematical typography."""

from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1] / "docs" / "statcom-capacitive-inductive"


def test_equations_are_true_vector_graphics_without_font_files():
    html = (BASE / "index.html").read_text(encoding="utf-8")
    assert html.count('class="equation-art ') == 2
    assert '<math display="block">' not in html
    assert html.count('role="img" aria-label=') >= 2
    assert not re.search(r'@font-face\\s*\\{|\\.(?:woff2?|ttf|otf)', html, re.I)


def test_equation_and_gallery_assets_are_offline():
    html = (BASE / "index.html").read_text(encoding="utf-8")
    assert html.count("data:image/svg+xml;base64,") == 6
    assert html.count("<script>") == 3
    assert not re.search(r'<(?:script|link)[^>]+(?:src|href)\\s*=', html, re.I)


def test_readable_variable_and_numeric_styles():
    css = (BASE / "source" / "styles.css").read_text(encoding="utf-8")
    assert '.math-svg-label tspan[data-math-role="var"]' in css
    assert '.math-svg-label tspan[data-math-role="roman"]' in css
    assert '.svg-numeric' in css
    assert 'font-variant-numeric:tabular-nums' in css
    assert '@media (max-width:520px)' in css


def test_electrical_model_untouched_and_slider_available():
    html = (BASE / "index.html").read_text(encoding="utf-8")
    assert "STATCOMPhysics" in html
    assert 'id="slider-E"' in html
    assert 'id="lab-circuit"' in html
    assert 'id="lab-phasors"' in html
    assert 'id="lab-waveforms"' in html

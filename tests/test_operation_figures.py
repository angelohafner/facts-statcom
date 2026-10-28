"""Plot API, Matplotlib-free numeric models, CLI and editable SVG verification."""

import json
import sys
from xml.etree import ElementTree as ET

import pytest

from facts_statcom.operation import OperationCase
from facts_statcom.operation.cli import main
from facts_statcom.operation.figures import FIGURE_NAMES, OperationFigureRenderer


@pytest.mark.parametrize("name",FIGURE_NAMES)
def test_vector_figure_contains_editable_text_without_embedded_raster(tmp_path,name):
    path=OperationFigureRenderer().save(name,tmp_path/f"{name}.svg")
    assert path.stat().st_size>8000
    root=ET.parse(path).getroot()
    assert root.tag.endswith("svg")
    assert any(e.tag.endswith("text") for e in root.iter())
    assert not any(e.tag.endswith("image") for e in root.iter())
    assert not any(e.tag.endswith("foreignObject") for e in root.iter())


def test_png_figure_export(tmp_path):
    path=OperationFigureRenderer().save("voltage-response",tmp_path/"v.png")
    assert path.read_bytes()[:8]==b"\x89PNG\r\n\x1a\n"


def test_invalid_figure_and_extension(tmp_path):
    r=OperationFigureRenderer()
    with pytest.raises(ValueError):
        r.figure("unknown")
    with pytest.raises(ValueError):
        r.save("unknown",tmp_path/"unknown.svg")
    with pytest.raises(ValueError):
        r.save("v-i-droop",tmp_path/"invalid.pdf")


def test_independent_plot_command_line_and_custom_config(tmp_path):
    default=OperationCase().to_dict()
    default["coupling"]["x_coupling_pu"]=.3
    p=tmp_path/"case.json"
    p.write_text(json.dumps(default),encoding="utf-8")
    out=tmp_path/"out"
    assert main(["--figure","power-angle","--config",str(p),
                 "--output-dir",str(out),"--format","both"])==0
    assert (out/"power-angle.svg").exists()
    assert (out/"power-angle.png").exists()
    manifest=json.loads((out/"manifest.json").read_text())
    assert manifest["config"]["coupling"]["x_coupling_pu"]==.3
    assert len(manifest["figures"])==1


def test_model_modules_do_not_load_matplotlib_or_circuit_renderer():
    # Run this check in a fresh interpreter to avoid fixture import pollution.
    import subprocess
    code=("import facts_statcom.operation.physics; "
          "import facts_statcom.operation.control; "
          "assert 'matplotlib' not in __import__('sys').modules; "
          "assert 'facts_statcom.operation.figures' not in __import__('sys').modules; "
          "assert 'facts_statcom.renderer' not in __import__('sys').modules; "
          "assert 'facts_statcom.symbols' not in __import__('sys').modules")
    import os
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    env=os.environ.copy()
    env["PYTHONPATH"]=str(root/"src")
    subprocess.run([sys.executable,"-c",code],cwd=root,env=env,check=True)


def test_export_all_gallery_and_numerical_csv(tmp_path):
    out=tmp_path/"entire-gallery"
    assert main(["--all","--output-dir",str(out),
                 "--export-control-csv"])==0
    doc=(out/"index.html").read_text(encoding="utf-8")
    assert doc.count("<article>")==len(FIGURE_NAMES)
    assert "Not EMT" in doc
    assert all((out/f"{name}.svg").exists() for name in FIGURE_NAMES)
    lines=(out/"voltage_control_trace.csv").read_text().splitlines()
    assert len(lines)>100
    assert "i_capacitive_pu" in lines[0]
    assert "e_required_pu" in lines[0]

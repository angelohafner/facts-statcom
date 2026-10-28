"""Check fixed interactive axes and full parameter-envelope visibility."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/statcom-capacitive-inductive/source'
HTML = SOURCE.parent / 'index.html'
SVG_NS = '{http://www.w3.org/2000/svg}'


def _svg(fragment: str) -> ET.Element:
    return ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{fragment}</svg>')


def _element(root: ET.Element, attribute: str, value: str) -> ET.Element:
    found = [element for element in root.iter() if element.get(attribute) == value]
    assert len(found) == 1, (attribute, value, len(found))
    return found[0]


def _path_points(path: ET.Element) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x, y in
            re.findall(r'[ML](-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', path.get('d', ''))]


def test_html_contains_the_same_renderer_as_modular_source():
    source = (SOURCE / 'figures.js').read_text(encoding='utf-8')
    generated = HTML.read_text(encoding='utf-8')
    assert source in generated
    assert generated.count('data:image/svg+xml;base64,') == 6
    assert not re.search(r'<(?:script|link)\b[^>]+(?:src|href)\s*=', generated, re.I)


def test_no_autorange_remains_in_the_live_renderer():
    source = (SOURCE / 'figures.js').read_text(encoding='utf-8')
    assert 'const AXIS_LIMITS=Object.freeze(' in source
    assert 'Math.min(185/Math.max(' not in source
    assert 'const ampl=Math.max(' not in source
    assert 'const magnitude=Math.max(' not in source
    assert 'const range=AXIS_LIMITS.trendMagnitude;' in source
    assert 'data-fixed-axis=' in source


@pytest.mark.skipif(not shutil.which('node'), reason='Node is optional')
def test_all_rendered_axes_keep_their_limits_and_extremes_are_visible():
    source = (SOURCE / 'model.js').read_text(encoding='utf-8')
    source += '\n' + (SOURCE / 'figures.js').read_text(encoding='utf-8')
    parameters = [
        {'E': 1.10, 'V': 1.00, 'X': 0.20, 'Imax': 1.0},
        {'E': 1.00, 'V': 1.00, 'X': 0.20, 'Imax': 1.0},
        {'E': 0.90, 'V': 1.00, 'X': 0.20, 'Imax': 1.0},
        {'E': 0.75, 'V': 1.15, 'X': 0.10, 'Imax': 0.5},
        {'E': 1.25, 'V': 0.85, 'X': 0.10, 'Imax': 1.5},
        {'E': 1.25, 'V': 1.15, 'X': 0.40, 'Imax': 0.5},
        {'E': 0.75, 'V': 0.85, 'X': 0.40, 'Imax': 0.5},
        {'E': 1.10, 'V': 1.00, 'X': 0.10, 'Imax': 0.5},
    ]
    source += '\nconst cases=' + json.dumps(parameters) + ';\n'
    source += '''
    process.stdout.write(JSON.stringify({
      axes:STATCOMViews.AXIS_LIMITS,
      plots:cases.map(p=>({
        p, point:STATCOMPhysics.point(p),
        phasors:STATCOMViews.phasors(p),
        waveforms:STATCOMViews.waveforms(p,90),
        Q:STATCOMViews.trend(p,'Q'),
        I:STATCOMViews.trend(p,'I')
      }))
    }));
    '''
    output = json.loads(subprocess.run(['node', '-e', source], capture_output=True,
                                       text=True, check=True).stdout)
    assert output['axes'] == {
        'phasorVoltage': 1.5, 'phasorCurrent': 4.0,
        'waveformVoltage': 2.0, 'waveformCurrent': 6.0,
        'trendEmin': .75, 'trendEmax': 1.25, 'trendMagnitude': 5.0,
    }
    for entry in output['plots']:
        phasor, waveform = _svg(entry['phasors']), _svg(entry['waveforms'])
        assert _element(phasor, 'data-fixed-axis', 'phasor-voltage').get('data-max') == '1.5'
        assert _element(phasor, 'data-fixed-axis', 'phasor-current').get('data-min') == '-4'
        assert _element(waveform, 'data-fixed-axis', 'voltage-waveform').get('data-max') == '2'
        assert _element(waveform, 'data-fixed-axis', 'current-waveform').get('data-max') == '6'
        assert -4-1e-9 <= entry['point']['Iimag'] <= 4+1e-9
        for key in ('v', 'e', 'i'):
            line = _element(waveform, 'data-signal', key)
            points = _path_points(line)
            assert len(points) == 121
            assert all(55-1e-5 <= x <= 438+1e-5 and
                       61-0.015 <= y <= 247+0.015 for x, y in points), (entry['p'], key)
        for kind in ('Q', 'I'):
            plot = _svg(entry[kind])
            metadata = _element(plot, 'data-fixed-axis',
                                'reactive-power' if kind == 'Q' else 'capacitive-current')
            assert {k: metadata.get(k) for k in ('data-min-x', 'data-max-x',
                                                  'data-min-y', 'data-max-y')} == {
                'data-min-x': '0.75', 'data-max-x': '1.25',
                'data-min-y': '-5', 'data-max-y': '5',
            }
            marker = _element(plot, 'data-operating-marker', kind)
            assert 60 <= float(marker.get('cx')) <= 567
            assert 27 <= float(marker.get('cy')) <= 188
            for curve in (x for x in plot.iter(SVG_NS+'path') if x.get('data-rating')):
                assert all(60 <= x <= 567 and 27 <= y <= 188
                           for x, y in _path_points(curve)), entry['p']


@pytest.mark.skipif(not shutil.which('node'), reason='Node is optional')
def test_equal_phasor_and_waveform_quantities_have_unchanged_positions():
    source = (SOURCE / 'model.js').read_text(encoding='utf-8')
    source += '\n' + (SOURCE / 'figures.js').read_text(encoding='utf-8')
    source += '''
    const p1={E:1.10,V:1.00,X:.20,Imax:1.0};
    const p2={E:1.10,V:1.00,X:.10,Imax:.5};
    const p3={E:1.05,V:1.00,X:.10,Imax:1.5};
    process.stdout.write(JSON.stringify([p1,p2,p3].map(p=>({
      phasors:STATCOMViews.phasors(p), waveforms:STATCOMViews.waveforms(p,45),
      Q:STATCOMViews.trend(p,'Q')
    }))));
    '''
    entries = json.loads(subprocess.run(['node', '-e', source], capture_output=True,
                                        text=True, check=True).stdout)
    phasors = [_svg(value['phasors']) for value in entries]
    waveforms = [_svg(value['waveforms']) for value in entries]
    assert len({float(_element(p, 'data-vector', 'E').get('x2')) for p in phasors}) == 2
    # Current is -j0.5 pu in cases 1 and 3 despite their different X settings.
    assert float(_element(phasors[0], 'data-vector', 'I').get('y2')) == float(
        _element(phasors[2], 'data-vector', 'I').get('y2'))
    # Equal PCC voltage must keep the voltage waveform on the same y coordinates.
    assert len({float(_element(w, 'data-cursor-signal', 'v').get('cy')) for w in waveforms}) == 1
    # The current's mathematical magnitude must still respond to X.
    assert float(_element(waveforms[0], 'data-cursor-signal', 'i').get('cy')) != float(
        _element(waveforms[1], 'data-cursor-signal', 'i').get('cy'))

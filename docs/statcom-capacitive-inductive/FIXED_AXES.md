# Fixed axis ranges in the interactive STATCOM lesson

The laboratory deliberately does **not** autoscale charts when the `E`, `V`, `X`,
`Imax`, or electrical-angle sliders move. All axes keep their numerical limits
and pixel conversion factors. This allows direct comparison of capacitive,
neutral, and inductive operation without visual rescaling artifacts.

| Interactive graphic | Horizontal range | Vertical range |
| --- | --- | --- |
| Equivalent circuit | Not a data plot | Not a data plot |
| Voltage phasors | `0..1.5 pu` (magnitude) | Real-axis reference |
| Injected-current phasor | Imaginary-axis reference | `-4..+4 pu` |
| Fundamental waveforms | `0..360 degrees` | Voltage: `-2..+2 pu` (left axis); current: `-6..+6 pu` (right axis) |
| Reactive power versus `E` | `0.75..1.25 pu` | `-5..+5 pu` |
| Capacitive current versus `E` | `0.75..1.25 pu` | `-5..+5 pu` |

**Important:** Voltage and current represent different per-unit physical
quantities. The phasor chart uses independent but fixed voltage and current
scales; the waveform chart explicitly labels two fixed vertical scales. The
same numerical values are used in the underlying equations as in the Python
`facts_statcom.operation.physics` model. All scales are constant across
settings, not equal in pixels per per-unit between unlike quantities.

## Why these limits cover all slider settings

The supplied laboratory controls allow
`0.75 <= E <= 1.25`, `0.85 <= V <= 1.15`, and `0.10 <= X <= 0.40`.
With `delta = 0` and current positive from converter to PCC:

```text
Icap = (E - V) / X
Qinj = V * Icap
Iinj = -j * Icap
```

Across all slider combinations, `-4.0 <= Icap <= +4.0 pu`. With the
fixed voltage limits, `-4.6 <= Qinj <= +3.4 pu`. Thus
`|sqrt(2) * Iinj| <= 5.657 pu` and voltage waveform magnitudes remain
below `sqrt(2) * 1.25 = 1.768 pu`.

The axes have sufficient margins to render the full **ideal, unrestricted**
mathematical operating envelope. Values outside the selected current rating
are **still shown**, but the existing warning and dashed curves identify them
as outside the converter rating. They are not silently clipped.

The six original, non-interactive scientific SVG teaching figures remain
unchanged; their individual published axes are already static.

## Reproducibility and tests

The range constants are collected in `source/figures.js` as `AXIS_LIMITS`.
`tests/test_capacitive_inductive_fixed_axes.py` verifies fixed ranges, shared
coordinates, full-envelope path bounds, and consistency with the standalone
HTML. Rebuild the self-contained presentation using:

```bash
python docs/statcom-capacitive-inductive/source/build.py
```

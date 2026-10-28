# STATCOM capacitive and inductive operation — four-step lesson

This package is a **focused, self-contained HTML teaching lesson**, not a general STATCOM slide deck.

- **Read the illustrated lesson first:** [`../statcom-capacitive-inductive-lesson.md`](../statcom-capacitive-inductive-lesson.md).
- **Open the offline presentation:** [`index.html`](index.html), a single HTML file with embedded CSS, JavaScript and six unmodified SVGs from `examples/operation/gallery/`.
- **Five navigation tabs:** equivalent circuit, capacitive mode, inductive mode, continuous transition, and the interactive lab.

## Interactive laboratory

The **main E slider** controls three synchronized SVG views side by side on desktop:

1. An ideal converter fundamental-voltage source behind the coupling reactor.
2. The corresponding PCC/converter voltage and injected-current phasors.
3. One electrical cycle of fundamental voltage and current waveforms.

Two smaller charts underneath show the operating point on `Q_inj(E)` and `I_cap(E)` with semitransparent capacitive/inductive regions and dashed out-of-rating segments. Current limits are shown as validity constraints, not as artificial clipping of the same voltage-source equation.

The **Advanced** disclosure provides `V`, `X`, and `Imax` sliders for additional experiments. The `θ` slider and animation button move the waveform's instantaneous cursor; the phasors are stationary in their reference frame.

Default example: `V=1.00 pu`, `X=0.20 pu`, `E=1.10 pu`, `Imax=1.00 pu`, `delta=0°`. Use the `Inductive`, `Neutral`, and `Capacitive` presets to change only E.

## Numerical and sign conventions

This lesson reuses the conventions from [`docs/operation.md`](../operation.md) and `facts_statcom.operation.physics`:

```text
I_inj = (E - V)/(jX) = -j (E-V)/X    (delta = 0)
Q_inj = V*(E-V)/X
I_cap = (E-V)/X = -Im(I_inj)
```

Injected current is positive in the **converter → PCC reference**, and positive Q means capacitive injection. Voltages and current are in fundamental RMS-base per-unit; instantaneous sine waves contain `sqrt(2)` relative to that RMS base. The waveform plot shows **fundamental voltages/currents only**, not PWM switching or detailed EMT transients.

This simplified model assumes no losses, no power-transfer angle, and no modulation/DC-link limits. A reference AC circuit and an explanatory phasor diagram **do not constitute a validated converter transient simulation**.

## Rebuild offline HTML

From the repository root:

```bash
python docs/statcom-capacitive-inductive/source/build.py
```

The build uses **Python standard library only**. It embeds existing SVG files byte-for-byte into the output as `data:` images. All styles and behavior are bundled inline. The output is deterministic, and the generated `index.html` is committed to GitHub to work without a build step.

The implementation is organized in:

- `source/template.html`: lesson content and MathML equations.
- `source/styles.css`: layout, responsivity, engineering visual style, and MathML typography.
- `source/model.js`: isolated, pure mathematical functions.
- `source/figures.js`: circuit, phasor, waveform, and operating-point SVG generation.
- `source/app.js`: synchronization, buttons, navigation, animation, keyboard, and accessibility.
- `source/build.py`: self-contained HTML compilation and SVG injection.

Existing Python models and the original gallery are **not modified**.

## Validation

```bash
python -m pip install -e .
python -m pytest -q tests
```

`tests/test_capacitive_inductive_lesson.py` validates the file structure, the original image payloads, all three canonical numerical cases, offline packaging, and JavaScript/Python numerical agreement for 60 cases if Node.js is available. Browser inspection additionally checks the interactive controls and responsive views.

## Navigation

Use the top tabs or the **Previous**/**Next** buttons. With no input focused, `←`, `→`, `PageUp`, and `PageDown` change sections; `L` jumps directly to the laboratory. On mobile, panels stack vertically while keeping the same numerical state.

**This material is an independent engineering teaching aid. It is not an official Siemens PTI publication.**

# STATCOM — From Voltage to VARs (interactive HTML)

A **self-contained 15-slide interactive educational presentation** about STATCOM/STATCON converter physics, reactive compensation, current limitations, and voltage control. Slide 15 is the central **STATCOM Laboratory**: all live plots share the same operating point. The presentation is in simple English and uses only inline CSS, JavaScript and SVG; **no external libraries, CDN, web connection or server are required** to open `index.html`.

## Open the presentation

1. Download `index.html` from the [repository](https://github.com/angelohafner/facts-statcom/blob/main/docs/statcom-presentation/index.html) (choose **Download raw file**, not the GitHub preview page).
2. Double-click the file to open it in Chrome, Edge, or Firefox.
3. Navigate with **← / →**, **Page Up / Page Down**, **Home / End**, the bottom toolbar, or the slide progress track. Use the laboratory icon to jump directly to **Slide 15**. Fullscreen is available from the toolbar.

All figures, including the preexisting topologies from `examples/gallery/`, are embedded in the delivered HTML; the file does not make HTTP requests.

## Interactive scenes

| Slides | Subject | Interactive behavior |
| --- | --- | --- |
| 1–3 | What a STATCOM is, components, two-level switching | Selectable equipment and complementary illustrative switch toggles |
| 4–6 | Equivalent circuit, capacitive vs inductive operation | Shared sliders and operating presets; active/reactive current sign convention |
| 7–8 | Reactive power versus converter RMS voltage, current rating | Continuous curves and dashed mathematically out-of-rating operating points |
| 9–10 | Three-phase fundamental waveforms and finite DC capacitor energy | Operating modes, animated time cursor and editable DC energy parameters |
| 11–13 | Control block diagram, voltage response, V-I droop | Clickable blocks, selected grid disturbance, synchronous averaged PI model and V-I intersection |
| 14 | Converter topologies | Inlined existing Python SVG diagrams: 2L, NPC, CHB star/delta, MMC double-star |
| **15** | **Interactive STATCOM Laboratory** | **Synchronized equivalent circuit, phasors, reactive power curve, waveforms, droop and P/Q/I readouts** |

## Electrical model and sign conventions

The slide deck follows `facts_statcom.operation.physics.CouplingModel`:

```text
V = V + j0
E = E * exp(j * delta)
Iinj = (E - V)/(jX)
Sinj = V * conj(Iinj)
Pinj = (V*E/X)*sin(delta)
Qinj = (V/X)*(E*cos(delta) - V)
Icap = Qinj / V
```

All quantities are per unit on a compatible three-phase power base. `V` and `E` are fundamental **phase RMS** equivalent phasors; the injected current is defined **from converter toward PCC**. `Qinj>0` means capacitive reactive injection; `Qinj<0` means inductive absorption. Accordingly, the injected current at zero delta is −90° relative to V when capacitive, and +90° when inductive. Physical units and matrix notation are formatted separately from italic variable symbols.

**Ratings:** If `|I|>Imax`, the point is explicitly labelled **outside current rating**, and unfeasible sections of the Q(E) curve are dashed. The presentation **never silently clips I while leaving E unchanged**. Practical converter capability may also be limited by Vdc and PWM headroom; these are not solved here.

**Power balance:** Nonzero delta implies active power in the lossless phasor snapshot; the finite DC capacitor cannot sustain arbitrary active injection without a further energy source. The DC capacitor slide calculates physical energy from user-entered C in mF and Vdc in kV, but the energy store is not coupled dynamically to the AC port.

**Voltage control:** The illustrative averaged controller directly mirrors `facts_statcom.operation.control`, including a simplified network relationship `Vpcc=Vth+Xth*Icap`, PI regulation, measurement lag, current lag, current limit, back-calculation anti-windup, and forward Euler integration. This is a voltage-sensitive **educational surrogate**, not EMT, PWM, a PLL simulation, a calibrated real regulator, or a solved network fault. Do not interpret the arbitrary timing in seconds as hardware response time.

**Shared vs independent controls:** E, V, X, delta and Imax are shared among all fundamental model plots and the Slide 15 laboratory. Vref, droop, grid Thevenin voltage and grid reactance adjust the separate *voltage-regulation* characteristic and transient surrogate; the droop point is intentionally distinct from a manually commanded E/delta experiment.

## Architecture and reuse

This is a new **presentation-only** layer. Existing `src/facts_statcom/` Python modelling and diagram-rendering modules are **unchanged**. The slide deck is built from the following source files:

```text
docs/statcom-presentation/
├── index.html                       # Portable standalone delivery
├── README.md
└── source/
    ├── page.html                    # Page shell
    ├── slides.html                  # 15 teaching scenes
    ├── style.css                    # 16:9 projection layout
    ├── model.js                     # Pure STATCOMModel, VoltageController, DCLinkModel
    ├── graphics.js                  # Reusable SVG symbol and diagram engine
    ├── charts.js                    # Plots, phasors, waveforms, control diagram
    ├── ui.js                        # Sliders, navigation, animation, state synchronization
    └── build.py                     # Inlines SVGs already in examples/gallery/
```

The presentation uses its **own JavaScript mathematical models** but follows the same equations and conventions as the standalone Python operation modules. The underlying SVG asset gallery remains the original source of truth for converter topology illustrations; the build process **inlines** those illustrations, rather than introducing a runtime dependency or redrawing them.

To rebuild from a clone, at the repository root run:

```bash
python docs/statcom-presentation/source/build.py
```

No pip packages are necessary for the rebuild. The generated file contains inlined SVGs for 2L, NPC, CHB star, CHB delta and MMC double-star. To inspect them in editable form use the originals in `examples/gallery/`.

## Testing

Run the repository's tests, including the static HTML checks:

```bash
python -m pytest -q
```

The presentation has additionally been opened in headless Chromium for manual slide, responsive-layout, slider synchronization and sign-convention checks. The interactive source is vanilla JavaScript and can also be syntax-checked with `node --check` on the individual files.

## Future extension

The JavaScript mathematics, SVG drawing engine and presentation UI are deliberately separate. This is consistent with `facts-svc`, while avoiding imports between Git repositories. Later, shared electrical symbols may be extracted to a third project without joining the STATCOM and SVC electrical models.

# STATCOM operating diagrams — physical conventions and numerical scope

The 13 figures in `examples/operation/gallery/` illustrate **fundamental-frequency STATCOM operation** and a **low-order educational voltage-controller surrogate**. The figures are generated from pure numerical models without calling the `facts_statcom.renderer` schematic backend or its netlist/symbol routines. They are not calibrated power-system studies, EMT switching calculations, or PSCAD/PSSE substitutes.

## Design boundaries

| Module | Role | Coupling to schematic drawing |
| --- | --- | --- |
| `operation.physics` | Lossless complex phasors, active/reactive power, instantaneous fundamental waveforms | **None** |
| `operation.control` | Voltage droop, current saturation, averaged PI and simple weak-grid approximation | **None** |
| `operation.config` | Immutable validated numerical/plot-input configurations and JSON files | **None** |
| `operation.figures` | Matplotlib SVG/PNG charts only | Imports `Theme` for existing **colors**; not `SVGCanvas`, `symbols`, `netlist`, or `renderer` |
| `operation.cli` | Separate command `facts-statcom-plots` and JSON manifest | No circuit CLI imports |
| `facts_statcom.svg` | Existing circuit SVG primitives and independent theme | Unmodified |

The root `facts_statcom` package uses lazy exports so `import facts_statcom.operation.physics` does not import `facts_statcom.renderer`. The older `from facts_statcom import STATCOMRenderer, presets` interface remains available.

## Sign, base and direction conventions

- Three-phase balanced, fundamental-frequency quantities are in per-unit on a **consistent three-phase apparent-power base** and associated phase-voltage/current/impedance bases. Thus `S_pu = V_pu * conj(I_pu)` without an extra factor of three. Actual volts, amperes and Mvar require user-supplied base quantities and are not computed here.
- `V` is the **PCC voltage**; `E` is the **converter fundamental phase-voltage equivalent**, both phase RMS phasors.
- `I_inj` is positive when flowing **from converter toward the PCC**, not from the PCC into the STATCOM. The model uses a positive, pure coupling reactance `X`; resistance, transformer phase shift and harmonic phenomena are neglected.
- `P_inj`, `Q_inj` are signed **power injected into the PCC**. `Q_inj > 0` is **capacitive support**. `Q_inj < 0` is **inductive absorption**. Thus the ordinary grid-to-device current direction would have the opposite phasor sign.
- `i_q,dq` is the imaginary component of the converter-to-PCC current with d axis aligned with `V`; consequently **`i_q,dq = -I_cap`**, where `I_cap = Q_inj/V` is defined positive for capacitive injection. Do not identify `I_cap` directly with `i_q,dq`.

## Lossless converter-behind-reactance model

Using the PCC voltage as the zero-angle reference and `E` at the relative angle `delta`:

```text
V = V + j0
E = E * exp(j * delta)
I_inj = (E - V) / (j*X)
S_inj = V * conjugate(I_inj)
P_inj = V*E*sin(delta)/X
Q_inj = V*(E*cos(delta) - V)/X
```

At `delta = 0`, the current is purely reactive and:

```text
I_cap = (E - V)/X
Q_inj = V*I_cap
E_required = V + X*I_cap
```

For example `V=1.0 pu`, `X=0.2 pu`, `delta=0°`, and:

- `E=1.1 pu` gives `I_inj=-j0.5 pu`, `Q_inj=+0.5 pu`: capacitive injection.
- `E=0.9 pu` gives `I_inj=+j0.5 pu`, `Q_inj=-0.5 pu`: inductive absorption.
- `E=V` gives `I=0` and `Q=0` (with `delta=0`).

For `delta != 0`, the active power can be nonzero in this lossless snapshot, but **a conventional STATCOM with only a dc capacitor cannot sustain arbitrary positive or negative active power**. In practice a slight AC-power import maintains dc-link voltage against converter losses; the DC energy balance is not modeled here.

`CouplingModel.operating_point()` **does not silently saturate** a point exceeding the configured converter current rating: it exposes the `current_within_rating` flag. The Q(E) and I(E) figures render such out-of-rating segments dashed as *unrestricted hypothetical* operation. They do **not** pretend that Q is clipped while E remains unchanged; such clipping is not a physical solution of the same algebraic circuit.

The `waveforms-*` plots use phase-a fundamental sinusoids:

```text
v(t) = sqrt(2)*V*sin(omega*t)
e(t) = sqrt(2)*E*sin(omega*t + delta)
i(t) = sqrt(2)*|I|*sin(omega*t + angle(I_inj))
```

With the stated converter-to-grid current direction, at `delta=0` the capacitive injection current is **-90°** relative to the PCC voltage; inductive absorption is **+90°**. It is normal to see opposite phase labels in figures that reference current from the grid into the device.

## Voltage droop and current limitation

The idealized static voltage/current reference characteristic is:

```text
I_cap,ref = clip((V_ref - V_meas)/droop, -I_max, +I_max)
```

**Droop is `pu voltage` per `pu injected current`** and not a reactive-power-to-voltage ratio. Positive capacitive current tends to increase the PCC voltage. At the limits, the STATCOM delivers approximately constant reactive **current**, not constant Q:

```text
Q_cap_max(V) = V*I_max
Q_ind_min(V) = -V*I_max
```

Finite converter AC voltage headroom, dc-link voltage and modulation constraints can impose tighter limits than the nameplate current; these are **not** enforced by the simplified controller (the converter-voltage plot explicitly marks its voltage as **required**, not a feasible guaranteed command).

## Educational PI dynamic surrogate

The simplified grid surrogate, not a Newton-Raphson / RMS / EMT network, is:

```text
V_PCC(t) = V_TH(t) + X_TH*I_cap(t)
error(t) = V_ref - V_measured(t) - droop*I_cap(t)
raw_current_command = Kp*error + integral_state
limited_current_command = clip(raw_current_command, -I_max, +I_max)
d(integral_state)/dt = Ki*error + Kaw*(limited_current_command - raw_current_command)
d(I_cap)/dt = (limited_current_command - I_cap)/tau_current
d(V_measured)/dt = (V_PCC - V_measured)/tau_measure
Q_inj(t) = V_PCC(t)*I_cap(t)
E_required(t) = V_PCC(t) + X_coupling*I_cap(t)
```

The integrator has back-calculation **anti-windup**. Forward-Euler integration is used with a small configured step; the code checks step-size bounds for the two lags. All examples start in the analytical equilibrium of the initial grid voltage. The `GridVoltageEvent` array controls the applied step changes.

At steady state, ignoring PI transients, the analytical result is:

```text
I_cap = clip((V_ref - V_TH)/(droop + X_TH), -I_max, +I_max)
V_PCC = V_TH + X_TH*I_cap
```

For the default case, `V_TH = 0.88 pu`, `droop = 0.03`, `X_TH = 0.12`, `I_max = 0.8 pu`, the idealized settled current is `+0.8 pu` and `V_PCC = 0.976 pu`. Following the overvoltage step to `1.045 pu`, the settled current is `-0.3 pu` and `V_PCC = 1.009 pu`.

No PLL, current decoupling, dq-frame transformations, PWM pulses, semiconductor commutation, filter losses, capacitor energy balance, network fault dynamics, protection logic, detailed harmonic content, or actual model tuning is included. The numerical response **must not be interpreted as real hardware response time**.

## Figure inventory

| Figure | Didactic question |
| --- | --- |
| `reactive-power-vs-e` | Why does E > V supply Q, while E < V absorbs Q? |
| `reactive-current-vs-e` | How does fundamental current change with converter voltage? |
| `phasor-capacitive` | Why is the injected capacitive current -90° for the chosen direction? |
| `phasor-inductive` | What reverses during inductive absorption? |
| `power-angle` | How does the hypothetical phase shift delta affect P and Q? |
| `v-i-droop` | How does the voltage regulator request Q current while limiting its magnitude? |
| `reactive-current-limit` | Why is limited reactive power proportional to voltage? |
| `waveforms-capacitive` | How do PCC voltage, converter fundamental voltage and current relate? |
| `waveforms-inductive` | What changes in waveform orientation during absorption? |
| `voltage-response` | How does PCC voltage respond to grid disturbances? |
| `current-response` | How do PI demand and actual current respond, with saturation? |
| `reactive-power-response` | When does the compensator inject vs absorb reactive power? |
| `converter-voltage-response` | What fundamental converter voltage would the reactive-current model require? |

## Running and extending

```bash
python -m pip install -e '.[plots]'
python -m facts_statcom.operation --list-figures
python -m facts_statcom.operation --all --output-dir output/operation
python -m facts_statcom.operation --all --format both
python -m facts_statcom.operation --figure voltage-response --config examples/operation_default.json
```

SVG exports use `matplotlib.rc_context(svg.fonttype='none')` so mathematical labels, units and legends remain **editable text**. The renderer uses the palette vocabulary of the existing `Theme` class. PNG is an optional independent Matplotlib output format (it does not require CairoSVG).

Add future physics functions to `operation.physics`, averaged control models to `operation.control`, and plot methods to `operation.figures`. Keep all generic schematic symbols and transistor topology drawings in their existing files. Both packages are designed for a later extraction of a shared presentation palette, but do not introduce runtime imports from `facts-svc`.

## Supporting industry references

- [OPAL-RT, *Static Synchronous Compensator (Phasor Type)*](https://opal-rt.atlassian.net/wiki/spaces/PSPS/pages/1551733147/Static%2BSynchronous%2BCompensator%2BPhasor%2BType): voltage mode, var control and reactive-current limit interpretation.
- [EMTP, *Three-level inverter based STATCOM*](https://emtp.com/documents/EMTP-Documentation/doc/advanced/statcom.pdf): voltage-source equivalent, reactive support and droop concept.

The plotting CLI also writes an offline **`index.html` gallery** and a JSON manifest. To inspect the complete low-order time-series values in other software, add `--export-control-csv` and inspect `voltage_control_trace.csv` (time, open-circuit grid voltage, PCC voltage, measured voltage, current command, injected current, injected Q and converter fundamental-voltage requirement).

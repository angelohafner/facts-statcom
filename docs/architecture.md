# Architectural compatibility and reusable components

## Design principle

The public core symbols and canvas **parallel** `facts-svc`, but the device models do not mix SVC and STATCOM internals. The `svg.py` API (`SVGCanvas`, `Theme`, `node`) is intentionally aligned with [`facts_svc.svg`](https://github.com/angelohafner/facts-svc/blob/main/src/facts_svc/svg.py). There is currently **no shared third-party runtime package** and no need for sibling checkouts.

| Part | Purpose | Reuse path |
| --- | --- | --- |
| `model.STATCOMConfig` | Frozen, validated topology configurations | Equipment-specific |
| `netlist.CircuitGraph` / `Device` | Terminal-to-net association and structure tests | Equipment-neutral graph abstraction |
| `svg.SVGCanvas` / `Theme` | SVG groups, layers, paths, typography, styles | Extract alongside SVC core later |
| `symbols.ElectricalSymbols` | Primitive IGBT, diode, coil, capacitor and transformer | Extract neutral subset alongside SVC symbols |
| `symbols.SwitchingCell`, `MMCSubmodule` | Reusable physical converter cells | Reusable for converters and HVDC VSC |
| `renderer.STATCOMRenderer` | Layouts of 2L, NPC, CHB, MMC, grid and control | STATCOM-specific composition |
| `cli.main` | JSON, presets and galleries | Common CLI structure |
| `operation.physics` / `operation.control` | Fundamental AC phasors and a low-order controller surrogate | Independent numerical model usable without Matplotlib |
| `operation.figures` | Matplotlib charts, editable SVG text and PNG | Palette compatibility only; no circuit SVG renderer import |
| `operation.cli` | Separate JSON-configurable figure generation | Independent entry point, no changes to circuit CLI |

The reuse boundary is intentionally at the **public API** rather than directly importing `facts_svc` classes. A future migration could make both packages depend on `power_diagrams_core`, leaving re-export shims in both packages. It should be a distinct project with its own tests and semantic versioning.

## Port models

- `Port(x, y)` specifies exact graphic wire endpoint coordinates.
- `Device(name, kind, terminals)` maps power and gate pins to *electrical net names*. Graphs are independent of pixel location.
- An IGBT has `C`, `E` and `G`; a diode has `A`, `K`; a capacitor has `P`, `N`.
- A programmable cell's SVG group contains independently identifiable power devices, with stable `data-device` and `data-name` attributes.
- No net is electrically connected merely because SVG lines cross. A contact is represented by an actual terminal, a continuous intended wire, or an explicitly matching net label.

## Compatibility contract

- Export `SVGCanvas`, `Theme`, `node` and `render_svg` with matching names and calling conventions.
- Keep the `Theme` dataclass field names consistent across the two repositories.
- Use similar color semantics: main conductors dark blue, capacitors amber, reactors blue, active/switching elements teal (where appropriate).
- Use `canvas.math()` tokens: `variable`, `roman`, `unit`, `matrix`, `subscript-variable`, `subscript-roman`.
- SVG layers include editable scientific text, not outlines or PNG images.
- Examples use `examples/gallery/*.svg`, and default CLI outputs go to `output/`.

## Growth strategy

1. Keep STATCOM and SVC independently installable and continuously tested.
2. Add shared low-level interfaces only after both require the same behavior.
3. Extract a stable `power-diagrams-core` package after testing against both projects.
4. Add switch states, EMT waveform sources, control-system plots and optional simulator inputs as separate modules, **not inside** the SVG primitive engine.
5. Avoid treating diagram geometry as a simulation. Dynamic models will need separate equations and validation.

## Independent operation examples (v0.2)

The operating-point engine uses the immutable `OperationCase` configuration and the pure-stdlib `CouplingModel` / `VoltageControlConfig` numerical modules. Chart rendering is optional and depends on Matplotlib only; it does not instantiate `STATCOMRenderer` or `SVGCanvas`. The root `facts_statcom` exports its legacy schematic API lazily to avoid importing circuit geometry when a user imports only the operation models.

See [operation.md](operation.md) for the verified Q sign convention, phasor equations, controller assumptions and physical limitations. The `examples/operation/gallery` SVGs are independent of the eight existing circuit diagrams.

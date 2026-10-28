# Electrical and graphical audit

These notes record which parts of the diagrams are electrical connections, which are simplified and what is mechanically tested. They do **not** certify compliance with equipment construction standards, component ratings, or an EMT model.

## Two-level voltage-source converter (VSC)

- Six independently identified IGBT symbols (two per phase) across `DC+` and `DC-`.
- Three AC output nodes `A`, `B`, `C`, each located between the upper and lower devices of its leg.
- Six antiparallel diodes, each with anode at **E** and cathode at **C** of its corresponding IGBT.
- The DC capacitor is in parallel across the shared DC rails. It is not placed in series with the AC interface.
- A gate line is **insulated** from the collector-emitter conduction path in each SVG symbol.

## Three-level neutral-point-clamped (NPC)

- Twelve IGBTs: per leg four series switches from the positive to the negative DC rail.
- Twelve reverse diodes for the switches, plus six additional clamping diodes.
- Upper clamping diode anode at `M`, cathode at the internal node between S1 and S2.
- Lower clamping diode anode at the internal node between S3 and S4, cathode at `M`.
- Capacitors Cdc1 and Cdc2 connected in series: `DC+–M–DC-`.
- Each phase **AC output** is between S2 and S3; this is **not** the DC midpoint `M`.
- For readability, `M` is a labeled, equal-potential local terminal in every phase column. The separated schematic lines are not individually wired all the way to the DC midpoint (which would create unwanted line crossings). The netlist confirms equality of those net names.

## Cascaded H-bridge (CHB)

- Three phase arms, each with configurable 1–3 H-bridge cells in series.
- Every cell: four switches, four antiparallel diodes, and one floating **isolated** DC capacitor.
- The two AC cell terminals are the **midpoints of opposite switch legs**, not a DC bus terminal.
- In **star**, the three final AC terminals join at a common floating node `N`.
- In **delta**, arms connect between named terminals `A–B`, `B–C`, `C–A`. Repeated net labels denote the exact same nodes; there is no shared star junction.
- Power ratings, individual cell balancing, energy sources, charge management and switching patterns are not specified.

## Modular multilevel converter (MMC-type double star)

- Three phase columns, with upper and lower arms (six total).
- Each arm has a series arm reactor and configurable 1–3 half-bridge submodules.
- A half-bridge cell contains an upper and lower switch, their reverse diodes, and a floating capacitor.
- **Arm port A** reaches the switching midpoint; **arm port B** reaches capacitor negative. The positive capacitor rail is internal to the module.
- Upper arms run from floating `P` to the AC phase via reactors; lower arms run from the AC phase via reactors to floating `N`.
- The drawing is one double-star chopper-cell-inspired MMC arrangement; not all MMC and STATCOM topologies share it. No external DC terminal, source or lumped DC capacitor is assumed.

## Complete connection and controller

- The three grid interface phases are shown with a **symbolic three-phase transformer** and three series reactors; winding connections are not invented.
- Labeled `A`, `B`, `C` endpoints on grid and VSC panels are the same named electrical nets. They are separated to prevent falsely connected wire crossings.
- The controller uses a common voltage-oriented dq control teaching convention: PLL, abc/dq transformations, DC voltage and AC voltage/reactive loops, current regulator, inverse transform, PWM and VSC.
- The current sign convention and the tuning of all PI loops, current limits and modulation constraints must be defined before simulating an operating point.

## Automated checks

Run `python -m pytest -q` to check:

- JSON config validation and serialization (including illegal cell counts).
- Unique device names and no locally shorted two-terminal power components.
- Counts of IGBTs, antiparallel diodes, clamping diodes and capacitors.
- Directed diode terminals in 2L/NPC and upper/lower switch assignments.
- Isolation of CHB cell DC capacitors; star/delta AC endpoint identities.
- MMC internal cell connectivity, arm reactors and module counts.
- Valid XML, unique element IDs, editable text and SVG/device group attributes.
- All preset renderings, 1–3 cell variants and CLI manifest creation.

Visual review includes all eight SVG figures, with raster previews generated from the exact SVGs. It is still possible for subtler schematic errors to escape the automated checks, so further engineering review is appropriate before technical publication.

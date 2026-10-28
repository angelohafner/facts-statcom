# Project development brief

Build a reusable Python object-oriented library for publication-quality, editable STATCOM/STATCON diagrams, using standalone `angelohafner/facts-statcom` while following SVG and typography conventions of `angelohafner/facts-svc` and `angelohafner/three-phase-scr-rectifier-visualizer`.

Implement a basic STATCOM, 2-level VSC, 3-level diode-clamped NPC, CHB star/delta, double-star MMC-type STATCOM, complete three-phase grid interface and functional dq controller. Show actual IGBT power terminals and antiparallel diodes, transformer/inductor/capacitor symbols and valid, isolated DC buses. Keep electric topology, vectors, layouts, JSON parameters, export logic and tests independent. Always create SVGs editable in Inkscape; provide optional PNG export. Use italic scalar math, upright physical units, bold upright matrix typography and English Python comments/docstrings. Do not claim the figures simulate converter dynamics. Preserve independent installations today; eventually extract genuinely common interfaces into an optional shared `power-diagrams-core` library.

## Current implementation

See the full [README](README.md), architecture notes and audit. The versioned gallery is generated, not hand drawn. All device graphs and diagrams can be reproduced by running `python -m facts_statcom --all`.

## Future enhancements

- Add device-specific `ElectricalSymbols` render backends (Schemdraw as optional, not mandatory), with graphical regression tests.
- Add SVG graph-based detection of unexpected physical wire intersections.
- Model VSC and STATCOM switching states and time-domain educational plots **separately** from schematics.
- Add explicit three-phase transformer vector groups, filter banks and protective equipment where requested.
- Add CHB module DC charging/balancing and MMC capacitor energy regulation only with clearly defined dynamic/EMT models and controls.

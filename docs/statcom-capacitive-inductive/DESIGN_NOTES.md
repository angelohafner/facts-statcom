# Typography and engineering design

This interactive STATCOM lesson uses an independently authored Siemens-inspired engineering document layout, not official Siemens branding. No logos, proprietary corporate fonts or font files are included.

## Math rendering

The two major mathematical expressions are embedded directly as vector SVG paths rendered from LaTeX-style MathText. Their appearance is independent of installed browser math fonts, and their accessibility descriptions are stored in `aria-label` attributes. Inline and dynamic SVG mathematical variables use intentional italics. Numbers, units and descriptive subscripts remain upright.

## Visual system

The document uses white technical panels, restrained deep-blue headings and teal accents, clean section navigation, structured legends, consistent plot line patterns, and readable labels. The five-section interactive laboratory, the original six scientific figures, and the electrical equations are unchanged in substance.

## Rebuilding

Source assets remain in `source/template.html`, `source/styles.css`, `source/figures.js`, `source/model.js`, and `source/app.js`. Build the offline presentation with:

```bash
python docs/statcom-capacitive-inductive/source/build.py
```

The exported HTML is fully standalone; no PowerPoint file is produced.

## Fixed-scale laboratory plots

Phasors, dual-axis fundamental waveforms, and operating-point characteristics use invariant numerical scales throughout the entire slider envelope. The six static reference SVGs are intentionally preserved, and the original electrical model is unchanged. See [FIXED_AXES.md](FIXED_AXES.md) for ranges, derivation and tests.

"""Batch CLI for rendering all STATCOM diagrams in SVG and optional PNG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .model import STATCOMConfig, presets
from .renderer import render_svg


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="facts-statcom",
        description="Generate modular STATCOM/STATCON schematics as editable SVGs")
    jobs = p.add_mutually_exclusive_group()
    jobs.add_argument("--preset", choices=tuple(presets()))
    jobs.add_argument("--config", type=Path, help="JSON configuration")
    jobs.add_argument("--all", action="store_true", help="Render all example topologies")
    p.add_argument("--list-presets", action="store_true")
    p.add_argument("--output-dir", type=Path, default=Path("output"))
    p.add_argument("--format", choices=("svg", "png", "both"), default="svg")
    return p


def png(svg: Path) -> Path:
    try:
        import cairosvg
    except ImportError as exc:
        raise SystemExit("PNG requires: pip install 'facts-statcom[png]'") from exc
    output = svg.with_suffix(".png")
    cairosvg.svg2png(url=str(svg), write_to=str(output), output_width=2100)
    return output


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    known = presets()
    if args.list_presets:
        print("\n".join(known))
        return 0
    if args.config:
        jobs = [(args.config.stem, STATCOMConfig.from_json(args.config))]
    elif args.all:
        jobs = list(known.items())
    else:
        key = args.preset or "two-level"
        jobs = [(key, known[key])]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for key, config in jobs:
        svg = render_svg(config, args.output_dir / f"{key}.svg")
        output = [svg.name]
        if args.format in ("png", "both"):
            output.append(png(svg).name)
            if args.format == "png":
                svg.unlink()
                output.pop(0)
        manifest.append({"preset": key, "config": config.to_dict(),
                         "files": output})
        print(*[str(args.output_dir / name) for name in output], sep="\n")
    dest = args.output_dir / "manifest.json"
    dest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n",
                    encoding="utf-8")
    print(dest)
    return 0

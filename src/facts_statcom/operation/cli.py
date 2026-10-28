"""Independent CLI for Matplotlib STATCOM teaching plots, without circuit CLI imports."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .config import OperationCase
from .control import simulate_voltage_control
from .gallery import save_gallery
from .figures import FIGURE_NAMES, OperationFigureRenderer


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="facts-statcom-plots",
        description="STATCOM operating-point, phasor and voltage-control teaching plots",
    )
    selector = p.add_mutually_exclusive_group()
    selector.add_argument("--figure", choices=FIGURE_NAMES, help="Generate one figure")
    selector.add_argument("--all", action="store_true", help="Generate the entire gallery")
    p.add_argument("--list-figures", action="store_true", help="Print supported figure names")
    p.add_argument("--config", type=Path, help="JSON configuration of numerical models")
    p.add_argument("--output-dir", type=Path, default=Path("output/operation"))
    p.add_argument("--format", choices=("svg", "png", "both"), default="svg")
    p.add_argument("--export-control-csv", action="store_true",
                   help="Export all control surrogate time-history columns to CSV")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.list_figures:
        print("\n".join(FIGURE_NAMES))
        return 0
    case = OperationCase.from_json(args.config) if args.config else OperationCase()
    render = OperationFigureRenderer(case)
    names = FIGURE_NAMES if args.all or not args.figure else (args.figure,)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name in names:
        formats = ("svg", "png") if args.format == "both" else (args.format,)
        output = []
        for fmt in formats:
            path = render.save(name, args.output_dir / f"{name}.{fmt}")
            print(path)
            output.append(path.name)
        manifest.append({"figure": name, "files": output})
    output_file = args.output_dir / "manifest.json"
    output_file.write_text(json.dumps({
        "model": "lossless phasor + idealized PI voltage-control surrogate",
        "config": case.to_dict(),
        "figures": manifest,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_file)
    gallery = save_gallery(args.output_dir, manifest)
    print(gallery)
    if args.export_control_csv:
        trace = simulate_voltage_control(
            case.control, case.voltage_events,
            coupling_x_pu=case.coupling.x_coupling_pu,
            end_time_s=case.end_time_s, time_step_s=case.time_step_s,
        )
        names = list(trace.__dataclass_fields__)
        target = args.output_dir / "voltage_control_trace.csv"
        with target.open("w", encoding="utf-8", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(names)
            writer.writerows(zip(*(getattr(trace, name) for name in names)))
        print(target)
    return 0

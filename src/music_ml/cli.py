"""Command-line entry points for reproducible pipeline stages."""

import argparse
import json
from pathlib import Path

from music_ml.data import generate, load_data
from music_ml.drift import report_drift
from music_ml.training import train


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["generate", "validate", "train"]:
        command = commands.add_parser(name)
        command.add_argument("--data-dir", type=Path, default=Path("data/generated"))
        if name != "validate":
            command.add_argument("--seed", type=int, default=42)
        if name == "train":
            command.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    drift = commands.add_parser("drift")
    drift.add_argument("--model", type=Path, default=Path("artifacts/model.json"))
    drift.add_argument("--observations", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "generate":
        generate(args.data_dir, args.seed)
        print(f"Synthetic demo data written to {args.data_dir}")
    elif args.command == "validate":
        tracks, rows = load_data(args.data_dir)
        print(json.dumps({"tracks": len(tracks), "interactions": len(rows)}))
    elif args.command == "train":
        print(json.dumps(train(args.data_dir, args.output_dir, args.seed), indent=2))
    elif args.command == "drift":
        report = report_drift(args.model, args.observations)
        print(json.dumps(report, indent=2))
        if report["drift_detected"]:
            raise SystemExit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path


REQUIRED_COLUMNS = {
    "CHAMBER",
    "SCIFI_NUMBER",
    "SFP",
    "DEV",
    "BIAS_PARAMETER",
}

EXPECTED_PARAMETERS = {"SET", "RBV", "STATE"}

Channel = tuple[str, int, int, int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate SciFi SiPM bias substitutions from SET, RBV and STATE "
            "CSV rows."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/scifi_bias.csv"),
        help="Input CSV file",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("db/generated/scifi_bias.substitutions"),
        help="Generated substitutions file",
    )

    parser.add_argument(
        "--template",
        default="db/templates/scifi_bias.template",
        help="EPICS database template path",
    )

    return parser.parse_args()


def parse_non_negative_integer(
    value: str | None,
    column: str,
    line_number: int,
) -> int:
    text = (value or "").strip()

    try:
        number = int(text)
    except ValueError as exc:
        raise ValueError(
            f"Line {line_number}: {column} must be an integer, got {text!r}"
        ) from exc

    if number < 0:
        raise ValueError(
            f"Line {line_number}: {column} cannot be negative"
        )

    return number


def read_channels(csv_path: Path) -> list[Channel]:
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    parameters_by_channel: dict[Channel, set[str]] = defaultdict(set)

    with csv_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)

        if reader.fieldnames is None:
            raise ValueError("CSV file has no header")

        fieldnames = {name.strip() for name in reader.fieldnames}
        missing_columns = REQUIRED_COLUMNS - fieldnames

        if missing_columns:
            raise ValueError(
                "Missing required CSV columns: "
                + ", ".join(sorted(missing_columns))
            )

        for line_number, row in enumerate(reader, start=2):
            chamber = (row.get("CHAMBER") or "").strip().upper()

            if not chamber:
                raise ValueError(
                    f"Line {line_number}: CHAMBER is empty"
                )

            scifi_number = parse_non_negative_integer(
                row.get("SCIFI_NUMBER"),
                "SCIFI_NUMBER",
                line_number,
            )

            sfp = parse_non_negative_integer(
                row.get("SFP"),
                "SFP",
                line_number,
            )

            dev = parse_non_negative_integer(
                row.get("DEV"),
                "DEV",
                line_number,
            )

            parameter = (
                row.get("BIAS_PARAMETER") or ""
            ).strip().upper()

            if parameter not in EXPECTED_PARAMETERS:
                raise ValueError(
                    f"Line {line_number}: invalid BIAS_PARAMETER "
                    f"{parameter!r}. Expected SET, RBV or STATE"
                )

            channel = (chamber, scifi_number, sfp, dev)

            if parameter in parameters_by_channel[channel]:
                raise ValueError(
                    f"Line {line_number}: duplicate {parameter} for "
                    f"{chamber} SCIFI{scifi_number} SFP{sfp} DEV{dev}"
                )

            parameters_by_channel[channel].add(parameter)

    if not parameters_by_channel:
        raise ValueError("No SiPM bias channels found")

    incomplete_channels: list[str] = []

    for channel, parameters in parameters_by_channel.items():
        missing_parameters = EXPECTED_PARAMETERS - parameters

        if missing_parameters:
            chamber, scifi_number, sfp, dev = channel

            incomplete_channels.append(
                f"{chamber} SCIFI{scifi_number} SFP{sfp} DEV{dev}: "
                f"missing {', '.join(sorted(missing_parameters))}"
            )

    if incomplete_channels:
        message = "\n".join(
            f"  - {item}" for item in incomplete_channels[:20]
        )

        if len(incomplete_channels) > 20:
            message += (
                f"\n  ... and {len(incomplete_channels) - 20} more"
            )

        raise ValueError(
            "Incomplete bias channel definitions:\n" + message
        )

    return sorted(
        parameters_by_channel.keys(),
        key=lambda channel: (
            channel[0],
            channel[1],
            channel[2],
            channel[3],
        ),
    )


def write_substitutions(
    output_path: Path,
    template_path: str,
    channels: list[Channel],
    source_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# AUTO-GENERATED FILE - DO NOT EDIT",
        "# Generated by scripts/generate_scifi_bias_substitutions.py",
        f"# Source: {source_path}",
        f"# Physical SiPM channels: {len(channels)}",
        "#",
        "# P, OFF_THRESHOLD, BIAS_TOLERANCE and INITIAL_BIAS",
        "# are supplied by dbLoadTemplate() in st.cmd.",
        "",
        f'file "{template_path}"',
        "{",
        "    pattern",
        "    {",
        "        CHAMBER,ID,SFP,DEV",
        "    }",
        "",
    ]

    for chamber, scifi_number, sfp, dev in channels:
        lines.append(
            f"    {{ {chamber},{scifi_number},{sfp},{dev} }}"
        )

    lines.extend(
        [
            "}",
            "",
        ]
    )

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()

    try:
        channels = read_channels(args.input)

        write_substitutions(
            output_path=args.output,
            template_path=args.template,
            channels=channels,
            source_path=args.input,
        )

    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Input CSV parameter rows: {len(channels) * 3}")
    print(f"Physical SiPM channels: {len(channels)}")
    print(f"Public PVs generated by template: {len(channels) * 3}")
    print(f"Generated: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
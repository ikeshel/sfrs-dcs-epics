#!/usr/bin/env python3
"""
Generate a SciFi PV list from scifi_parameters.csv and optionally submit it
to an EPICS Archiver Appliance.

Expected CSV columns:
    CHAMBER,CH_NUMBER,SCIFI_NUMBER,SFP,DEV,SENSOR

Default PV format:
    SFRS:FPF2:SCIFI:1:SFP0:DEV0:TEMP_FPGA

Examples:
    python3 scripts/generate_archiver.py
    python3 scripts/generate_archiver.py --submit
    python3 scripts/generate_archiver.py --submit --sampling-period 5
    python3 scripts/generate_archiver.py --archiver-url http://localhost:17665/mgmt/bpl
"""

from __future__ import annotations

import argparse
import csv
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable


REQUIRED_COLUMNS = {
    "CHAMBER",
    "CH_NUMBER",
    "SCIFI_NUMBER",
    "SFP",
    "DEV",
    "SENSOR",
}

DEFAULT_PV_FORMAT = (
    "SFRS:{CHAMBER}{CH_NUMBER}:SCIFI:{SCIFI_NUMBER}:"
    "SFP{SFP}:DEV{DEV}:TEMP_{SENSOR}"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate and optionally register SciFi PVs in Archiver Appliance."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("../data/scifi_parameters.csv"),
        help="Input CSV file (default: ../data/scifi_parameters.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("../data/scifi_archiver_pvs.txt"),
        help="Generated PV-list file (default: ../data/scifi_archiver_pvs.txt)",
    )
    parser.add_argument(
        "--pv-format",
        default=DEFAULT_PV_FORMAT,
        help="Python format string used to build each PV name.",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Submit generated PVs to Archiver Appliance.",
    )
    parser.add_argument(
        "--archiver-url",
        default="http://localhost:17665/mgmt/bpl",
        help="Archiver Appliance management BPL URL.",
    )
    parser.add_argument(
        "--sampling-period",
        type=float,
        default=1.0,
        help="Sampling period in seconds (default: 1.0).",
    )
    parser.add_argument(
        "--sampling-method",
        choices=("MONITOR", "SCAN"),
        default="MONITOR",
        help="Sampling method (default: MONITOR).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="PVs submitted per HTTP request (default: 100).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds (default: 30).",
    )
    return parser.parse_args()


def normalise_row(row: dict[str, str], line_number: int) -> dict[str, str]:
    cleaned = {
        key: (value.strip() if value is not None else "")
        for key, value in row.items()
    }

    for numeric_column in ("CH_NUMBER", "SCIFI_NUMBER", "SFP", "DEV"):
        value = cleaned[numeric_column]
        try:
            cleaned[numeric_column] = str(int(value))
        except ValueError as exc:
            raise ValueError(
                f"CSV line {line_number}: {numeric_column} must be an integer, "
                f"got {value!r}"
            ) from exc

    cleaned["CHAMBER"] = cleaned["CHAMBER"].upper()
    cleaned["SENSOR"] = cleaned["SENSOR"].upper()

    if cleaned["SENSOR"] not in {"FPGA", "SIPM", "FEB"}:
        raise ValueError(
            f"CSV line {line_number}: unsupported SENSOR "
            f"{cleaned['SENSOR']!r}"
        )

    return cleaned


def load_pvs(csv_path: Path, pv_format: str) -> list[str]:
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)

        if reader.fieldnames is None:
            raise ValueError("CSV file has no header")

        missing = REQUIRED_COLUMNS.difference(reader.fieldnames)
        if missing:
            raise ValueError(
                "CSV is missing required columns: " + ", ".join(sorted(missing))
            )

        pvs: list[str] = []
        seen: set[str] = set()

        for line_number, row in enumerate(reader, start=2):
            values = normalise_row(row, line_number)

            try:
                pv = pv_format.format(**values)
            except KeyError as exc:
                raise ValueError(
                    f"PV format refers to unknown CSV column: {exc.args[0]}"
                ) from exc

            if not pv:
                raise ValueError(f"CSV line {line_number}: generated an empty PV")

            if pv in seen:
                print(
                    f"Warning: duplicate PV ignored at CSV line "
                    f"{line_number}: {pv}",
                    file=sys.stderr,
                )
                continue

            seen.add(pv)
            pvs.append(pv)

    if not pvs:
        raise ValueError("No PVs were generated")

    return pvs


def write_pv_list(output_path: Path, pvs: Iterable[str]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(f"{pv}\n" for pv in pvs),
        encoding="utf-8",
    )


def chunks(items: list[str], size: int) -> Iterable[list[str]]:
    if size <= 0:
        raise ValueError("Batch size must be greater than zero")

    for start in range(0, len(items), size):
        yield items[start : start + size]


def submit_batch(
    base_url: str,
    pvs: list[str],
    sampling_period: float,
    sampling_method: str,
    timeout: float,
) -> str:
    endpoint = base_url.rstrip("/") + "/archivePV"

    body = urllib.parse.urlencode(
        {
            "pv": ",".join(pvs),
            "samplingperiod": str(sampling_period),
            "samplingmethod": sampling_method,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def submit_all(
    base_url: str,
    pvs: list[str],
    sampling_period: float,
    sampling_method: str,
    batch_size: int,
    timeout: float,
) -> None:
    batches = list(chunks(pvs, batch_size))

    for index, batch in enumerate(batches, start=1):
        print(
            f"Submitting batch {index}/{len(batches)} "
            f"({len(batch)} PVs)..."
        )

        response_text = submit_batch(
            base_url=base_url,
            pvs=batch,
            sampling_period=sampling_period,
            sampling_method=sampling_method,
            timeout=timeout,
        )

        if response_text.strip():
            print(response_text.strip())


def main() -> int:
    args = parse_args()

    if args.sampling_period <= 0:
        print("Error: --sampling-period must be greater than zero", file=sys.stderr)
        return 2

    try:
        pvs = load_pvs(args.csv, args.pv_format)
        write_pv_list(args.output, pvs)

        print(f"Generated {len(pvs)} unique PV names")
        print(f"PV list written to: {args.output}")

        if not args.submit:
            print("Dry run only. Use --submit to register the PVs.")
            return 0

        submit_all(
            base_url=args.archiver_url,
            pvs=pvs,
            sampling_period=args.sampling_period,
            sampling_method=args.sampling_method,
            batch_size=args.batch_size,
            timeout=args.timeout,
        )

        print("Archiver submission completed.")
        return 0

    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        print(
            f"Archiver HTTP error {exc.code}: {exc.reason}\n{details}",
            file=sys.stderr,
        )
        return 1
    except urllib.error.URLError as exc:
        print(f"Cannot contact Archiver Appliance: {exc.reason}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

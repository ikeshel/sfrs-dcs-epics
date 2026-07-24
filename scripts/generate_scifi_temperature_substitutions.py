#!/usr/bin/env python3

import csv
from pathlib import Path

INPUT_CSV = Path("data/scifi_temperature.csv")
OUTPUT_SUBSTITUTIONS = Path("db/generated/scifi_temperature.substitutions")


def main():

    OUTPUT_SUBSTITUTIONS.parent.mkdir(parents=True, exist_ok=True)

    with INPUT_CSV.open(newline="") as csvfile:

        reader = csv.DictReader(csvfile)

        with OUTPUT_SUBSTITUTIONS.open("w") as out:

            out.write("###############################################################################\n")
            out.write("#\n")
            out.write("# Automatically generated.\n")
            out.write("# DO NOT EDIT!\n")
            out.write("#\n")
            out.write("###############################################################################\n\n")

            out.write('file "db/templates/scifi_temperature.template"\n')
            out.write("{\n")
            out.write("    pattern\n")
            out.write("    {\n")
            out.write("        P,CHAMBER,ID,SFP,DEV,SENSOR,INITIAL\n")
            out.write("    }\n\n")

            previous = None

            for row in reader:

                chamber = row["CHAMBER"]
                scifi = row["SCIFI_NUMBER"]
                sfp = row["SFP"]
                dev = row["DEV"]
                sensor = row["SENSOR"]

                detector = f"{chamber}"

                current = (detector, scifi)

                if current != previous:

                    if previous is not None:
                        out.write("\n")

                    out.write(f"    # {detector} SciFi {scifi}\n")
                    previous = current

                out.write(
                    f"    {{ "
                    f"SFRS,"
                    f"{detector},"
                    f"{scifi},"
                    f"{sfp},"
                    f"{dev},"
                    f"{sensor},"
                    f"22.0 "
                    f"}}\n"
                )

            out.write("}\n")


if __name__ == "__main__":
    main()
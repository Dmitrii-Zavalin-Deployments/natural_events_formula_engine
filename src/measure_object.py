#!/usr/bin/env python3

import csv
import os
import subprocess
import sys

from core.timestamp import parse_timestamp_from_filename
from core.grid import process_and_save_grid_image
from core.template_matching import process_image


def main():
    if len(sys.argv) != 4:
        print("Usage: python3 measure_object.py <raw_folder> <processed_folder> <output_csv>")
        sys.exit(1)

    raw_folder = sys.argv[1]
    processed_folder = sys.argv[2]
    output_csv = sys.argv[3]

    os.makedirs(processed_folder, exist_ok=True)

    files = sorted([
        f for f in os.listdir(raw_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    if not files:
        print(f"[ERROR] No valid images found in {raw_folder}")
        sys.exit(1)

    records = []

    print(f"\n[START] Found {len(files)} images to audit.")
    print("Each image will open in Firefox. Enter the measurement cell number.\n")

    # Manual mode
    for idx, fn in enumerate(files, start=1):
        raw_path = os.path.join(raw_folder, fn)
        processed_path = os.path.join(processed_folder, fn)
        timestamp = parse_timestamp_from_filename(fn)

        if not process_and_save_grid_image(raw_path, processed_path):
            print(f"[WARN] Could not read {fn}, skipping.")
            continue

        abs_processed_path = os.path.abspath(processed_path)
        subprocess.Popen(["firefox", abs_processed_path])

        print("--------------------------------------------------")
        print(f"[{idx}/{len(files)}] Image: {fn} | Time: {timestamp}")
        cell_input = input(" -> Enter Natural Event Cell Number: ").strip()

        records.append((timestamp, cell_input))

    # Automatic mode
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "manual_cell", "auto_x_px", "auto_y_px"])

        for ts, cell_val in records:
            writer.writerow([ts, cell_val, "", ""])

        for fn in files:
            raw_path = os.path.join(raw_folder, fn)
            processed_path = os.path.join(processed_folder, fn)
            timestamp = parse_timestamp_from_filename(fn)

            result = process_image(raw_path, processed_path)
            if result is None:
                print(f"[WARN] Could not detect object in {fn}")
                continue

            object_x, object_y = result
            writer.writerow([timestamp, "", object_x, object_y])
            print(f"[INFO] {timestamp} → X={object_x:.2f}px, Y={object_y:.2f}px")

    print(f"[INFO] Output written to {output_csv}")


if __name__ == "__main__":
    main()


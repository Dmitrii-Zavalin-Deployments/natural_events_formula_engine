#!/usr/bin/env python3

import csv
import logging
import os
import subprocess
import sys

import cv2

from core.config_loader import load_config
from core.grid import get_cell_info_by_coords, process_and_save_grid_image
from core.template_matching import process_image
from core.timestamp import parse_timestamp_from_filename

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Natural Events Formula Engine measurement run...")

    try:
        config = load_config()
    except (OSError, ValueError, KeyError, TypeError) as e:
        logger.error(str(e))
        sys.exit(1)

    try:
        mode = config["mode"]
        raw_folder = config["paths"]["raw_folder"]
        processed_folder = config["paths"]["processed_folder"]
        output_csv = config["paths"]["output_csv"]
        grid_config = config["grid"]
    except KeyError as e:
        logger.error(f"[CONFIG ERROR] Missing mandatory key in config: {e}")
        sys.exit(1)

    if mode not in {"dry_run", "measurements"}:
        logger.error(
            f"[CONFIG ERROR] Invalid execution mode '{mode}'. Expected 'dry_run' or 'measurements'."
        )
        sys.exit(1)

    if not os.path.exists(raw_folder):
        logger.error(f"[CONFIG ERROR] raw_folder does not exist: {raw_folder}")
        sys.exit(1)

    os.makedirs(processed_folder, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)

    files = sorted([
        f for f in os.listdir(raw_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    if not files:
        logger.error(f"[INPUT ERROR] No valid images found in {raw_folder}")
        sys.exit(1)

    logger.info(f"Found {len(files)} images to process.")
    records = []

    if mode == "measurements":
        print("\nEach image will open in Firefox. Enter the measurement cell number.\n")

    image_meta_map = {}
    for idx, fn in enumerate(files, start=1):
        raw_path = os.path.join(raw_folder, fn)
        processed_path = os.path.join(processed_folder, fn)
        timestamp = parse_timestamp_from_filename(fn)

        ok, meta = process_and_save_grid_image(raw_path, processed_path, grid_config)
        if not ok:
            logger.warning(f"Could not read {fn}, skipping.")
            continue
        image_meta_map[fn] = meta

        if mode == "measurements":
            abs_processed_path = os.path.abspath(processed_path)
            subprocess.Popen(["firefox", abs_processed_path])
            print("--------------------------------------------------")
            print(f"[{idx}/{len(files)}] Image: {fn} | Time: {timestamp}")
            cell_input = input(" -> Enter Natural Event Cell Number: ").strip()
        else:
            cell_input = "0"
            logger.info(f"[{idx}/{len(files)}] [DRY-RUN] Bypassed GUI/CLI prompt for {fn}")

        records.append((timestamp, fn, cell_input))

    if mode == "dry_run":
        logger.info(
            f"[DRY-RUN] Would process template matching and write to {output_csv}. Skipping file write."
        )
    else:
        logger.info("Running automatic template-matching measurements & serialization...")
        with open(output_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["datetime", "cell_number", "x_range", "y_range"])

            # Process manual reference entries
            for ts, fn, cell_val in records:
                meta = image_meta_map.get(fn, [])
                resolved_cell = int(cell_val) if cell_val.isdigit() else 0
                x_rng, y_rng = "N/A", "N/A"
                for m in meta:
                    if m["cell_number"] == resolved_cell:
                        x_rng, y_rng = m["x_range"], m["y_range"]
                        break
                writer.writerow([ts, resolved_cell, x_rng, y_rng])

            # Process automatic detections
            for fn in files:
                raw_path = os.path.join(raw_folder, fn)
                processed_path = os.path.join(processed_folder, fn)
                timestamp = parse_timestamp_from_filename(fn)

                img = cv2.imread(raw_path)
                h, w = img.shape[:2] if img is not None else (1000, 1000)

                result = process_image(raw_path, processed_path)
                if result is None:
                    logger.warning(f"Could not detect object in {fn}")
                    continue

                object_x, object_y = result
                cell_num, x_range, y_range = get_cell_info_by_coords(
                    object_x, object_y, w, h, grid_config
                )
                writer.writerow([timestamp, cell_num, x_range, y_range])
                logger.info(
                    f"{timestamp} → cell={cell_num}, x_range={x_range}, y_range={y_range}"
                )

    logger.info("Measurement run complete.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import csv
import logging
import os
import subprocess
import sys

from core.config_loader import load_config
from core.timestamp import parse_timestamp_from_filename
from core.grid import process_and_save_grid_image
from core.template_matching import process_image

# ------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Natural Events Formula Engine measurement run...")

    # ------------------------------------------------------------
    # Load configuration (strict, no-default policy)
    # ------------------------------------------------------------
    try:
        config = load_config()
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

    try:
        mode = config["mode"]
        raw_folder = config["paths"]["raw_folder"]
        processed_folder = config["paths"]["processed_folder"]
        output_csv = config["paths"]["output_csv"]
    except KeyError as e:
        logger.error(f"[CONFIG ERROR] Missing mandatory key in config: {e}")
        sys.exit(1)

    logger.info(f"Mode: {mode} | Raw folder: {raw_folder} | Processed folder: {processed_folder}")

    # ------------------------------------------------------------
    # Validate folders & mode compliance
    # ------------------------------------------------------------
    if mode not in {"dry_run", "measurements"}:
        logger.error(f"[CONFIG ERROR] Invalid execution mode '{mode}'. Expected 'dry_run' or 'measurements'.")
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

    # ------------------------------------------------------------
    # Manual mode / Inspection preparation
    # ------------------------------------------------------------
    for idx, fn in enumerate(files, start=1):
        raw_path = os.path.join(raw_folder, fn)
        processed_path = os.path.join(processed_folder, fn)
        timestamp = parse_timestamp_from_filename(fn)

        if not process_and_save_grid_image(raw_path, processed_path):
            logger.warning(f"Could not read {fn}, skipping.")
            continue

        if mode == "measurements":
            abs_processed_path = os.path.abspath(processed_path)
            subprocess.Popen(["firefox", abs_processed_path])
            print("--------------------------------------------------")
            print(f"[{idx}/{len(files)}] Image: {fn} | Time: {timestamp}")
            cell_input = input(" -> Enter Natural Event Cell Number: ").strip()
        else:
            cell_input = "DRY_RUN_SKIPPED"
            logger.info(f"[{idx}/{len(files)}] [DRY-RUN] Bypassed GUI/CLI prompt for {fn}")

        records.append((timestamp, cell_input))

    # ------------------------------------------------------------
    # Automatic mode / Output serialization
    # ------------------------------------------------------------
    if mode == "dry_run":
        logger.info(f"[DRY-RUN] Would process template matching and write to {output_csv}. Skipping file write.")
    else:
        logger.info("Running automatic template-matching measurements...")
        with open(output_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "manual_cell", "auto_x_px", "auto_y_px"])

            # Manual entries
            for ts, cell_val in records:
                writer.writerow([ts, cell_val, "", ""])

            # Automatic entries
            for fn in files:
                raw_path = os.path.join(raw_folder, fn)
                processed_path = os.path.join(processed_folder, fn)
                timestamp = parse_timestamp_from_filename(fn)

                result = process_image(raw_path, processed_path)
                if result is None:
                    logger.warning(f"Could not detect object in {fn}")
                    continue

                object_x, object_y = result
                writer.writerow([timestamp, "", object_x, object_y])
                logger.info(f"{timestamp} → X={object_x:.2f}px, Y={object_y:.2f}px")

    logger.info("Measurement run complete.")


if __name__ == "__main__":
    main()

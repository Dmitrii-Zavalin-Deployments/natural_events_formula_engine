#!/usr/bin/env python3

import csv
from datetime import datetime
import os
import subprocess
import sys
import cv2
import numpy as np

# ============================================================
# Natural Events Formula Engine – Universal Image Measurement Script (Hybrid Mode)
#
# Purpose:
#   Extract measurement data from natural events captured in images.
#   Supports ANY moving object whose motion you want to convert into a formula:
#       - wave crests
#       - shoreline edges
#       - floating objects
#       - drifting debris
#       - cloud boundaries
#       - snow accumulation lines
#       - any object visible across multiple frames
#
# Workflow:
#   1. Select the moving object of interest.
#   2. Take multiple photos from the SAME fixed spot.
#   3. Define measurement grid in config/config.json (future).
#   4. Run this script:
#        - Manual mode: user selects grid cell where object appears.
#        - Automatic mode: template matching estimates object geometry.
#
# Modes:
#   Manual Mode:
#       - Displays measurement grid overlay.
#       - User selects the grid cell where the object is located.
#       - Future: full X×Y square grid loaded from config/config.json.
#
#   Automatic Mode:
#       - Template matching detects the object automatically.
#       - Returns geometric measurements (pixel distances).
#       - Future: multi-template detection, configurable ROIs.
#
# Output:
#   CSV with:
#       time, height
#           - manual mode: user-selected grid cell
#           - automatic mode: pixel distance from image top to object
#
#   processed images:
#       - manual mode: grid overlay
#       - automatic mode: bounding box around detected object
# ============================================================

OBJECT_TEMPLATE = None
OBJECT_OFFSET_X = 0  # horizontal offset from template left to object reference point
OBJECT_OFFSET_Y = 0  # vertical offset from template top to object reference point


# ------------------------------------------------------------
# Timestamp Parsing
# ------------------------------------------------------------
def parse_timestamp_from_filename(fn):
    """Extract timestamp from IMG_YYYYMMDD_HHMMSS-style filenames or return base name."""
    base = os.path.basename(fn)
    try:
        parts = base.split("_")
        if len(parts) >= 3 and parts[0].upper() == "IMG":
            date_str = parts[1]
            time_str = parts[2].split(".")[0]
            dt = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    return os.path.splitext(base)[0]


# ------------------------------------------------------------
# Manual Mode: High‑Visibility Grid Overlay
# ------------------------------------------------------------
def draw_high_visibility_grid(img):
    """
    Draw extra-large, high-contrast grid cells optimized for human reading.

    Universal manual measurement surface:
    - divides the image into vertical cells (future: full X×Y grid)
    - labels each cell with its Y‑range
    - allows human mapping of object position to a discrete cell index
    """
    h, w = img.shape[:2]
    overlay = img.copy()

    cell_height = 100
    cell_width = 250
    cell_idx = 0

    for y in range(0, h, cell_height):
        cv2.line(overlay, (0, y), (w, y), (0, 255, 255), 3, cv2.LINE_AA)
        y_end = min(y + cell_height, h)

        if y < h:
            label = f"CELL {cell_idx} (Y:{y}-{y_end})"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.1
            font_thickness = 3

            for x_pos in [30, int(w * 0.35), int(w * 0.68)]:
                (tw, th), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
                cv2.rectangle(
                    overlay,
                    (x_pos - 8, y + 45 - th - 8),
                    (x_pos + tw + 8, y + 45 + baseline + 4),
                    (0, 0, 0),
                    cv2.FILLED,
                )
                cv2.putText(
                    overlay,
                    label,
                    (x_pos, y + 45),
                    font,
                    font_scale,
                    (0, 255, 255),
                    font_thickness,
                    cv2.LINE_AA,
                )
        cell_idx += 1

    for x in range(0, w, cell_width):
        cv2.line(overlay, (x, 0), (x, h), (255, 255, 0), 1, cv2.LINE_AA)

    return cv2.addWeighted(overlay, 0.60, img, 0.40, 0)


def process_and_save_grid_image(raw_path, processed_path):
    """Load image, overlay measurement grid, save to processed path."""
    img = cv2.imread(raw_path)
    if img is None:
        return False
    grid_img = draw_high_visibility_grid(img)
    cv2.imwrite(processed_path, grid_img)
    return True


# ------------------------------------------------------------
# Automatic Mode: Template Matching (generic object detection)
# ------------------------------------------------------------
def init_object_template(img):
    """
    Initialize template for the object of interest from the first image.

    Concept:
    - define ROI where object is expected
    - detect strong horizontal feature
    - build template patch around that feature

    Future:
    - configurable ROI from config
    - multiple templates
    """
    global OBJECT_TEMPLATE, OBJECT_OFFSET_X, OBJECT_OFFSET_Y

    h, w = img.shape[:2]
    x_min = int(w * 0.15)
    x_max = int(w * 0.35)
    y_min = int(h * 0.55)
    y_max = int(h * 0.85)

    roi = img[y_min:y_max, x_min:x_max]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=50,
        minLineLength=40,
        maxLineGap=10,
    )

    if lines is None or len(lines) == 0:
        tpl_h = int((y_max - y_min) * 0.2)
        tpl_w = int((x_max - x_min) * 0.6)
        y1 = y_min + (y_max - y_min) // 2 - tpl_h // 2
        x1 = x_min + (x_max - x_min) // 2 - tpl_w // 2
        OBJECT_TEMPLATE = img[y1:y1 + tpl_h, x1:x1 + tpl_w].copy()
        OBJECT_OFFSET_X = tpl_w // 2
        OBJECT_OFFSET_Y = tpl_h // 2
        return

    best = None
    best_len = 0
    for line in lines:
        arr = np.array(line).reshape(-1)
        if arr.size != 4:
            continue
        x1, y1, x2, y2 = arr
        if abs(y2 - y1) > 3:
            continue
        length = abs(x2 - x1)
        if length > best_len:
            best_len = length
            best = (x1, y1, x2, y2)

    if best is None:
        tpl_h = int((y_max - y_min) * 0.2)
        tpl_w = int((x_max - x_min) * 0.6)
        y1 = y_min + (y_max - y_min) // 2 - tpl_h // 2
        x1 = x_min + (x_max - x_min) // 2 - tpl_w // 2
        OBJECT_TEMPLATE = img[y1:y1 + tpl_h, x1:x1 + tpl_w].copy()
        OBJECT_OFFSET_X = tpl_w // 2
        OBJECT_OFFSET_Y = tpl_h // 2
        return

    x1, y1, x2, y2 = best
    line_y = int((y1 + y2) / 2)

    pad_x = 10
    pad_y_top = 10
    pad_y_bottom = 20

    tpl_x1 = max(x_min + min(x1, x2) - pad_x, 0)
    tpl_x2 = min(x_min + max(x1, x2) + pad_x, w)
    tpl_y1 = max(y_min + line_y - pad_y_top, 0)
    tpl_y2 = min(y_min + line_y + pad_y_bottom, h)

    OBJECT_TEMPLATE = img[tpl_y1:tpl_y2, tpl_x1:tpl_x2].copy()
    tpl_h, tpl_w = OBJECT_TEMPLATE.shape[:2]

    OBJECT_OFFSET_X = tpl_w // 2
    OBJECT_OFFSET_Y = tpl_h // 2


def find_object_xy(img):
    """
    Return object (x, y) coordinates using template matching.

    Semantics:
    - x: horizontal position (pixels) from image left
    - y: vertical position (pixels) from image top
    """
    global OBJECT_TEMPLATE, OBJECT_OFFSET_X, OBJECT_OFFSET_Y

    if OBJECT_TEMPLATE is None:
        init_object_template(img)

    h, w = img.shape[:2]
    tpl_h, tpl_w = OBJECT_TEMPLATE.shape[:2]

    x_min = int(w * 0.10)
    x_max = int(w * 0.40)
    y_min = int(h * 0.50)
    y_max = int(h * 0.90)

    search = img[y_min:y_max, x_min:x_max]
    res = cv2.matchTemplate(search, OBJECT_TEMPLATE, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(res)

    sx, sy = max_loc

    object_x = x_min + sx + OBJECT_OFFSET_X
    object_y = y_min + sy + OBJECT_OFFSET_Y

    return object_x, object_y, (
        x_min + sx,
        y_min + sy,
        x_min + sx + tpl_w,
        y_min + sy + tpl_h,
    )


def mark_image(img, object_box, processed_path):
    """Draw bounding box around detected object and save image."""
    marked = img.copy()
    x1, y1, x2, y2 = object_box
    cv2.rectangle(marked, (x1, y1), (x2, y2), (0, 0, 255), 3)
    cv2.imwrite(processed_path, marked)


def process_image(raw_path, processed_path):
    """
    Automatic measurement pipeline:
    - detect object
    - annotate image
    - return (x, y) pixel coordinates
    """
    img = cv2.imread(raw_path)
    if img is None:
        return None

    object_x, object_y, object_box = find_object_xy(img)
    mark_image(img, object_box, processed_path)

    return float(object_x), float(object_y)


# ------------------------------------------------------------
# Main – Hybrid Measurement Run
# ------------------------------------------------------------
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

    # --------------------------------------------------------
    # Manual mode
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # Automatic mode
    # --------------------------------------------------------
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

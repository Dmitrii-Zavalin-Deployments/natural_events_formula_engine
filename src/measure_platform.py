#!/usr/bin/env python3

import csv
from datetime import datetime
import os
import subprocess
import sys
import cv2

<<<<<<< Updated upstream
=======
# ============================================================
# Floating Platform Tide Measurement Script (Template Matching)
# Baseline: top of image
# Platform: top edge of floating platform (auto-detected)
#
# Input:
#   - raw_folder
#   - processed_folder
#   - output_csv_path
#
# Output:
#   - CSV with time,height_pixels (distance from top to platform)
#   - processed images with marked platform
# ============================================================
>>>>>>> Stashed changes

PLATFORM_TEMPLATE = None
PLATFORM_OFFSET_Y = 0  # offset from template top to platform top (pixels)


def parse_timestamp_from_filename(fn):
    """Extract timestamp from filenames or return base filename."""
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


<<<<<<< Updated upstream
def draw_high_visibility_grid(img):
    """Draws extra-large, high-contrast grid cells optimized for immediate human reading."""
    h, w = img.shape[:2]
    overlay = img.copy()

    cell_height = 100
    cell_width = 250

    # Horizontal grid lines and enlarged text labels
    cell_idx = 0
    for y in range(0, h, cell_height):
        # Bright yellow divider line
        cv2.line(overlay, (0, y), (w, y), (0, 255, 255), 3, cv2.LINE_AA)

        y_end = min(y + cell_height, h)
        if y < h:
            label = f"CELL {cell_idx} (Y:{y}-{y_end})"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.1
            font_thickness = 3

            # Display labels at left, center, and right coordinates
            for x_pos in [30, int(w * 0.35), int(w * 0.68)]:
                (tw, th), baseline = cv2.getTextSize(
                    label, font, font_scale, font_thickness
                )

                # Solid black background box for ultra-high contrast
                cv2.rectangle(
                    overlay,
                    (x_pos - 8, y + 45 - th - 8),
                    (x_pos + tw + 8, y + 45 + baseline + 4),
                    (0, 0, 0),
                    cv2.FILLED,
                )
                # High-visibility yellow text
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

    # Vertical column markers
    for x in range(0, w, cell_width):
        cv2.line(overlay, (x, 0), (x, h), (255, 255, 0), 1, cv2.LINE_AA)

    # Blend grid with image (60% grid opacity for maximum legibility)
    return cv2.addWeighted(overlay, 0.60, img, 0.40, 0)


def process_and_save_grid_image(raw_path, processed_path):
    """Reads raw image, overlays high-visibility grid, and saves processed file."""
=======
def init_platform_template(img):
    """
    Initialize platform template from the first image.
    Heuristic: platform is in lower-left/mid region.
    """
    global PLATFORM_TEMPLATE, PLATFORM_OFFSET_Y

    h, w = img.shape[:2]

    # ROI where platform is expected (tuned for your scene)
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
        # fallback: take a fixed small patch in ROI
        tpl_h = int((y_max - y_min) * 0.2)
        tpl_w = int((x_max - x_min) * 0.6)
        y1 = y_min + (y_max - y_min) // 2 - tpl_h // 2
        x1 = x_min + (x_max - x_min) // 2 - tpl_w // 2
        PLATFORM_TEMPLATE = img[y1:y1 + tpl_h, x1:x1 + tpl_w].copy()
        PLATFORM_OFFSET_Y = tpl_h // 2
        return

    # find strongest horizontal line in ROI (platform top)
    best = None
    best_len = 0
    for line in lines:
        arr = np.array(line).reshape(-1)
        if arr.size != 4:
            continue
        x1, y1, x2, y2 = arr
        if abs(y2 - y1) > 3:
            continue  # keep near-horizontal
        length = abs(x2 - x1)
        if length > best_len:
            best_len = length
            best = (x1, y1, x2, y2)

    if best is None:
        # fallback as above
        tpl_h = int((y_max - y_min) * 0.2)
        tpl_w = int((x_max - x_min) * 0.6)
        y1 = y_min + (y_max - y_min) // 2 - tpl_h // 2
        x1 = x_min + (x_max - x_min) // 2 - tpl_w // 2
        PLATFORM_TEMPLATE = img[y1:y1 + tpl_h, x1:x1 + tpl_w].copy()
        PLATFORM_OFFSET_Y = tpl_h // 2
        return

    x1, y1, x2, y2 = best
    line_y = int((y1 + y2) / 2)

    # define template around this line
    pad_x = 10
    pad_y_top = 10
    pad_y_bottom = 20

    tpl_x1 = max(x_min + min(x1, x2) - pad_x, 0)
    tpl_x2 = min(x_min + max(x1, x2) + pad_x, w)
    tpl_y1 = max(y_min + line_y - pad_y_top, 0)
    tpl_y2 = min(y_min + line_y + pad_y_bottom, h)

    PLATFORM_TEMPLATE = img[tpl_y1:tpl_y2, tpl_x1:tpl_x2].copy()
    PLATFORM_OFFSET_Y = line_y - (tpl_y1 - y_min)


def find_platform_y(img):
    """
    Find platform top y-coordinate using template matching.
    Returns y (distance from top of image to platform top).
    """
    global PLATFORM_TEMPLATE, PLATFORM_OFFSET_Y

    if PLATFORM_TEMPLATE is None:
        init_platform_template(img)

    h, w = img.shape[:2]
    tpl_h, tpl_w = PLATFORM_TEMPLATE.shape[:2]

    # search region: same general area as template
    x_min = int(w * 0.10)
    x_max = int(w * 0.40)
    y_min = int(h * 0.50)
    y_max = int(h * 0.90)

    search = img[y_min:y_max, x_min:x_max]
    res = cv2.matchTemplate(search, PLATFORM_TEMPLATE, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(res)

    sx, sy = max_loc  # top-left in search ROI
    platform_top_y = y_min + sy + PLATFORM_OFFSET_Y

    return platform_top_y, (x_min + sx, y_min + sy,
                            x_min + sx + tpl_w, y_min + sy + tpl_h)


def mark_image(img, platform_box, processed_path):
    """Draw detected platform box on the image and save it."""
    marked = img.copy()
    x1, y1, x2, y2 = platform_box
    cv2.rectangle(marked, (x1, y1), (x2, y2), (0, 0, 255), 3)
    cv2.imwrite(processed_path, marked)


def process_image(raw_path, processed_path):
>>>>>>> Stashed changes
    img = cv2.imread(raw_path)
    if img is None:
        return False

<<<<<<< Updated upstream
    grid_img = draw_high_visibility_grid(img)
    cv2.imwrite(processed_path, grid_img)
    return True
=======
    platform_y, platform_box = find_platform_y(img)
    mark_image(img, platform_box, processed_path)

    # distance from top of image to platform top
    return float(platform_y)
>>>>>>> Stashed changes


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python3 measure_platform_manual.py <raw_folder>"
            " <processed_folder> <output_csv>"
        )
        sys.exit(1)

    raw_folder = sys.argv[1]
    processed_folder = sys.argv[2]
    output_csv = sys.argv[3]

    os.makedirs(processed_folder, exist_ok=True)
    files = sorted(
        [
            f
            for f in os.listdir(raw_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
    )

    if not files:
        print(f"[ERROR] No valid images found in {raw_folder}")
        sys.exit(1)

    records = []

    print(f"\n[START] Found {len(files)} images to audit.")
    print("Each image will open in Firefox. Enter the cell number in terminal.\n")

    for idx, fn in enumerate(files, start=1):
        raw_path = os.path.join(raw_folder, fn)
        processed_path = os.path.join(processed_folder, fn)
        timestamp = parse_timestamp_from_filename(fn)

        # Generate overlay image
        if not process_and_save_grid_image(raw_path, processed_path):
            print(f"[WARN] Could not read {fn}, skipping.")
            continue

        # Open image non-blockingly in Firefox
        abs_processed_path = os.path.abspath(processed_path)
        firefox_proc = subprocess.Popen(["firefox", abs_processed_path])

        # Interactive Terminal Prompt
        print(f"--------------------------------------------------")
        print(f"[{idx}/{len(files)}] Image: {fn} | Time: {timestamp}")
        cell_input = input(" -> Enter Floating Platform Cell Number: ").strip()

        records.append((timestamp, cell_input))

        # Close Firefox instance if desired (optional: leave open or let Firefox reuse tab)

    # Export to CSV
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "height"])
        for ts, cell_val in records:
            writer.writerow([ts, cell_val])

<<<<<<< Updated upstream
    print(f"\n[COMPLETE] Successfully saved {len(records)} entries to {output_csv}")
=======
        for fn in files:
            if not fn.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            raw_path = os.path.join(raw_folder, fn)
            processed_path = os.path.join(processed_folder, fn)

            timestamp = parse_timestamp_from_filename(fn)
            if timestamp is None:
                print(f"[WARN] Could not parse timestamp from {fn}")
                continue

            dist = process_image(raw_path, processed_path)
            if dist is None:
                print(f"[WARN] Could not detect platform in {fn}")
                continue

            writer.writerow([timestamp, dist])
            print(f"[INFO] {timestamp} → {dist:.2f} px")

    print(f"[INFO] Output written to {output_csv}")
>>>>>>> Stashed changes


if __name__ == "__main__":
    main()
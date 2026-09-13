import cv2
import numpy as np


def hex_to_bgr(hex_str):
    h = hex_str.lstrip("#")
    return (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))


def draw_high_visibility_grid(img, grid_config):
    h, w = img.shape[:2]
    overlay = img.copy()

    cell_w = int(grid_config["cell_width_px"])
    cell_h = int(grid_config["cell_height_px"])
    thickness = int(grid_config["grid_thickness"])
    color = hex_to_bgr(grid_config["grid_color"])
    text_color = hex_to_bgr(grid_config["text_color"])

    cols = (w + cell_w - 1) // cell_w
    rows = (h + cell_h - 1) // cell_h

    # Uniform grid lines for both X and Y
    for x in range(0, w + 1, cell_w):
        cv2.line(overlay, (x, 0), (x, h), color, thickness, cv2.LINE_AA)
    for y in range(0, h + 1, cell_h):
        cv2.line(overlay, (0, y), (w, y), color, thickness, cv2.LINE_AA)

    font = cv2.FONT_HERSHEY_SIMPLEX
    fs = 0.7
    ft = 2

    cell_metadata = []
    cell_idx = 0
    for cy in range(rows):
        y_start = cy * cell_h
        y_end = min((cy + 1) * cell_h, h)
        for cx in range(cols):
            x_start = cx * cell_w
            x_end = min((cx + 1) * cell_w, w)

            x_range_str = f"[{x_start},{x_end})"
            y_range_str = f"[{y_start},{y_end})"
            cell_metadata.append({
                "cell_number": cell_idx,
                "x_range": x_range_str,
                "y_range": y_range_str,
                "box": (x_start, y_start, x_end, y_end),
            })

            label = str(cell_idx)
            cx_center = x_start + (x_end - x_start) // 2
            cy_center = y_start + (y_end - y_start) // 2
            (tw, th), baseline = cv2.getTextSize(label, font, fs, ft)
            org = (cx_center - tw // 2, cy_center + th // 2)

            cv2.rectangle(
                overlay,
                (org[0] - 4, org - th - 3),
                (org[0] + tw + 4, org + baseline + 3),
                (0, 0, 0),
                cv2.FILLED,
            )
            cv2.putText(overlay, label, org, font, fs, text_color, ft, cv2.LINE_AA)
            cell_idx += 1

    blended = cv2.addWeighted(overlay, 0.65, img, 0.35, 0)
    return blended, cell_metadata


def get_cell_info_by_coords(px, py, w, h, grid_config):
    cell_w = int(grid_config["cell_width_px"])
    cell_h = int(grid_config["cell_height_px"])
    cols = (w + cell_w - 1) // cell_w
    cx = min(int(px // cell_w), cols - 1) if px >= 0 else 0
    cy = int(py // cell_h) if py >= 0 else 0
    cell_idx = cy * cols + cx
    x_start = cx * cell_w
    x_end = min((cx + 1) * cell_w, w)
    y_start = cy * cell_h
    y_end = min((cy + 1) * cell_h, h)
    return cell_idx, f"[{x_start},{x_end})", f"[{y_start},{y_end})"


def process_and_save_grid_image(raw_path, processed_path, grid_config):
    img = cv2.imread(raw_path)
    if img is None:
        return False, []
    grid_img, meta = draw_clean_cell_grid(img, grid_config)
    cv2.imwrite(processed_path, grid_img)
    return True, meta

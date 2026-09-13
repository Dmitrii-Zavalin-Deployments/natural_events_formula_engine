import logging

import cv2

logger = logging.getLogger(__name__)


def hex_to_bgr(hex_str):
    h = hex_str.lstrip("#")
    return (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))


def draw_high_visibility_grid(img, grid_config):
    h, w = img.shape[:2]
    logger.info(f"Initializing grid overlay for dimensions w={w}, h={h}")
    overlay = img.copy()

    cell_w = int(grid_config["cell_width_px"])
    cell_h = int(grid_config["cell_height_px"])
    thickness = int(grid_config["grid_thickness"])
    color = hex_to_bgr(grid_config["grid_color"])
    text_color = hex_to_bgr(grid_config["text_color"])

    cols = (w + cell_w - 1) // cell_w
    rows = (h + cell_h - 1) // cell_h
    logger.info(
        f"Computed grid layout: {cols} cols x {rows} rows ({cell_w}x{cell_h}px/cell)"
    )

    # Uniform grid lines for both X and Y
    for x in range(0, w + 1, cell_w):
        cv2.line(overlay, (x, 0), (x, h), color, thickness, cv2.LINE_AA)
    for y in range(0, h + 1, cell_h):
        cv2.line(overlay, (0, y), (w, y), color, thickness, cv2.LINE_AA)
    logger.debug("Rendered uniform X/Y grid boundary lines.")

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

            # Fixed tuple indexing org for vertical text bounding box
            cv2.rectangle(
                overlay,
                (org[0] - 4, org[1] - th - 3),
                (org[0] + tw + 4, org[1] + baseline + 3),
                (0, 0, 0),
                cv2.FILLED,
            )
            cv2.putText(
                overlay, label, org, font, fs, text_color, ft, cv2.LINE_AA
            )
            cell_idx += 1

    logger.debug(f"Stamped {cell_idx} integer ID boxes.")
    blended = cv2.addWeighted(overlay, 0.65, img, 0.35, 0)
    logger.info("Alpha blending completed (0.65 overlay, 0.35 base).")
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
    x_str = f"[{x_start},{x_end})"
    y_str = f"[{y_start},{y_end})"
    logger.info(
        f"Spatial lookup coords ({px}, {py}) -> cell_idx={cell_idx}, x_range={x_str}, y_range={y_str}"
    )
    return cell_idx, x_str, y_str


def process_and_save_grid_image(raw_path, processed_path, grid_config):
    logger.info(f"Loading raw image for processing: {raw_path}")
    img = cv2.imread(raw_path)
    if img is None:
        logger.error(
            f"Failed to read image at {raw_path}. Returning False/empty meta."
        )
        return False, []

    grid_img, meta = draw_high_visibility_grid(img, grid_config)
    logger.info(f"Writing grid-annotated output to {processed_path}")
    success = cv2.imwrite(processed_path, grid_img)
    if not success:
        logger.error(f"Failed to write image to disk: {processed_path}")
        return False, []

    logger.info(
        f"Successfully saved {processed_path} with {len(meta)} cell records."
    )
    return True, meta
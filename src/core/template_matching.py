import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

OBJECT_TEMPLATE = None
OBJECT_OFFSET_X = 0
OBJECT_OFFSET_Y = 0


def init_object_template(img):
    global OBJECT_TEMPLATE

    h, w = img.shape[:2]
    logger.info(f"Initializing object template for image dimensions w={w}, h={h}")
    x_min = int(w * 0.15)
    x_max = int(w * 0.35)
    y_min = int(h * 0.55)
    y_max = int(h * 0.85)

    roi = img[y_min:y_max, x_min:x_max]
    if roi.size == 0:
        logger.warning("Empty ROI encountered; fallback to full-frame center.")
        OBJECT_TEMPLATE = img[int(h * 0.4):int(h * 0.6), int(w * 0.4):int(w * 0.6)].copy()
        return

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength=40, maxLineGap=10)

    if lines is None or len(lines) == 0:
        logger.warning("No Hough lines detected in ROI; falling back to ROI center.")
        tpl_h = max(int((y_max - y_min) * 0.2), 10)
        tpl_w = max(int((x_max - x_min) * 0.6), 10)
        y1 = y_min + (y_max - y_min) // 2 - tpl_h // 2
        x1 = x_min + (x_max - x_min) // 2 - tpl_w // 2
        OBJECT_TEMPLATE = img[y1:y1 + tpl_h, x1:x1 + tpl_w].copy()
        return

    best = None
    best_len = 0
    for line in lines:
        flat_line = line.ravel()
        x1, y1, x2, y2 = flat_line[:4]
        if abs(y2 - y1) > 3:
            continue
        length = abs(x2 - x1)
        if length > best_len:
            best_len = length
            best = (x1, y1, x2, y2)

    if best is None:
        logger.warning("No horizontal line met criteria; using default ROI center slice.")
        OBJECT_TEMPLATE = roi[0:max(int(roi.shape[0] * 0.5), 10), 0:max(int(roi.shape[1] * 0.5), 10)].copy()
        return

    x1, y1, x2, y2 = best
    line_y = int((y1 + y2) / 2)
    
    pad_x, pad_y_top, pad_y_bottom = 10, 10, 20
    tpl_x1 = max(x_min + min(x1, x2) - pad_x, 0)
    tpl_x2 = min(x_min + max(x1, x2) + pad_x, w)
    tpl_y1 = max(y_min + line_y - pad_y_top, 0)
    tpl_y2 = min(y_min + line_y + pad_y_bottom, h)

    OBJECT_TEMPLATE = img[tpl_y1:tpl_y2, tpl_x1:tpl_x2].copy()


def find_object_xy(img):
    if OBJECT_TEMPLATE is None or OBJECT_TEMPLATE.size == 0:
        init_object_template(img)

    h, w = img.shape[:2]
    tpl_h, tpl_w = OBJECT_TEMPLATE.shape[:2]

    x_min = int(w * 0.10)
    x_max = int(w * 0.40)
    y_min = int(h * 0.50)
    y_max = int(h * 0.90)

    search = img[y_min:y_max, x_min:x_max]
    if search.shape[0] < tpl_h or search.shape[1] < tpl_w:
        logger.warning("Search area smaller than template; using base coordinates.")
        return x_min, y_min, (x_min, y_min, x_min + tpl_w, y_min + tpl_h)

    res = cv2.matchTemplate(search, OBJECT_TEMPLATE, cv2.TM_CCOEFF_NORMED)
    _, _max_val, _, max_loc = cv2.minMaxLoc(res)

    sx, sy = max_loc
    object_x = x_min + sx + OBJECT_OFFSET_X
    object_y = y_min + sy + OBJECT_OFFSET_Y
    box = (x_min + sx, y_min + sy, x_min + sx + tpl_w, y_min + sy + tpl_h)

    return object_x, object_y, box


def mark_image(img, object_box, processed_path):
    x1, y1, x2, y2 = object_box
    marked = img.copy()
    cv2.rectangle(marked, (x1, y1), (x2, y2), (0, 0, 255), 3)
    cv2.imwrite(processed_path, marked)


def process_image(raw_path, processed_path):
    img = cv2.imread(raw_path)
    if img is None:
        logger.error(f"Failed to read image at {raw_path}")
        return None

    object_x, object_y, object_box = find_object_xy(img)
    mark_image(img, object_box, processed_path)

    return float(object_x), float(object_y)

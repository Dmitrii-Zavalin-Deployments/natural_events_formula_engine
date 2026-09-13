import cv2


def draw_high_visibility_grid(img):
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
    img = cv2.imread(raw_path)
    if img is None:
        return False
    grid_img = draw_high_visibility_grid(img)
    cv2.imwrite(processed_path, grid_img)
    return True


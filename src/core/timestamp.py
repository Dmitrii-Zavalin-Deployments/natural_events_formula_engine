import os
from datetime import datetime


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


from datetime import datetime, timezone
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_timestamp_from_filename(fn):
    """Extract timestamp from IMG_YYYYMMDD_HHMMSS-style filenames or return base name."""
    base = os.path.basename(fn)
    logger.debug(f"Attempting to parse timestamp from filename: {base}")
    try:
        parts = base.split("_")
        if len(parts) >= 3 and parts[0].upper() == "IMG":
            date_str = parts[1]
            time_str = parts[2].split(".")[0]
            dt = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            res = dt.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Parsed timestamp {res} from {base}")
            return res
        else:
            logger.debug(f"Filename {base} does not conform to IMG_YYYYMMDD_HHMMSS pattern.")
    except Exception as e:
        logger.warning(f"Exception encountered while parsing timestamp for {base}: {e}", exc_info=True)
    
    fallback = os.path.splitext(base)[0]
    logger.info(f"Falling back to base name without extension: {fallback}")
    return fallback
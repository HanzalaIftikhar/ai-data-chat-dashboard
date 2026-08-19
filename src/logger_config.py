import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def setup_logging():
    """
    Configures logging for the whole app: writes to both the terminal
    (for live debugging) and a rotating log file (for later review).
    Call this once, at app startup.
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return  # already configured — avoid duplicate handlers on Streamlit reruns

    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler: keeps log files from growing forever.
    # Once app.log hits 1MB, it rolls over and keeps 3 old backups.
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
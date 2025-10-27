import os
import logging
import datetime
from logging.handlers import TimedRotatingFileHandler
from .config import Config


def setup_logginger(name: str) -> logging.Logger:
    # Ensure the logs directory exists
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Generate the log file name with the current date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{current_date}.log")

    # Create a TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=7,  # Keep logs for 7 days
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Add the handler to the root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    # Set the log level from the configuration
    root_logger.setLevel(Config.LOG_LEVEL)

    return logging.getLogger(name)

def get_logger(name: str) -> logging.Logger:
    return setup_logginger(name)

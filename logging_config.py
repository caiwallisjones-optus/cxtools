# logging_config.py
import logging
from logging.handlers import TimedRotatingFileHandler


def setup_logging():
    # Create a custom logger
    app_log = logging.getLogger('cxtools')
    app_log.setLevel(logging.DEBUG)

    # Create handlers

    file_handler = TimedRotatingFileHandler('cxtools.log', when='midnight', interval=1)
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Set the logging level for the handler

    # Create formatters and add them to handlers
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    console_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    console_formatter.datefmt = "%H:%M:%S"
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add handlers to the logger
    app_log.addHandler(file_handler)
    app_log.addHandler(console_handler)

    return app_log
# app.py
logger = setup_logging()

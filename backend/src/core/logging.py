"""Logging configuration for the application."""

import logging
import sys

from src.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure and return the application logger."""
    # Create logger
    logger = logging.getLogger("trading_wizard")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


# Global logger instance
logger = setup_logging()

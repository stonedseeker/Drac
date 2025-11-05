import sys
from pathlib import Path
from loguru import logger
from app.config import settings


def setup_logging():    
    # Remove default logger
    logger.remove()
    
    # Console logging
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # File logging
    log_path = Path(settings.log_dir) / settings.log_file
    logger.add(
        log_path,
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
    )
    
    # Error logging (separate file)
    error_log_path = Path(settings.log_dir) / "error.log"
    logger.add(
        error_log_path,
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
    )
    
    logger.info(f"Logging initialized - Level: {settings.log_level}")
    return logger


# Initialize logging
log = setup_logging()


__all__ = ["log"]
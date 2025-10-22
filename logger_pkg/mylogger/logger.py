import logging
import sys
import time
from functools import wraps

# For colored output
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except ImportError:
    Fore = Style = type("", (), {"RESET_ALL": "", "BRIGHT": "", "RED": "", "YELLOW": "", "GREEN": "", "BLUE": "", "MAGENTA": "", "CYAN": ""})()

class Logger:
    """
    Reusable Logger class for console and file logging with optional colors.
    Features:
    - Colored console output
    - File logging
    - Decorators for timing/logging functions
    """

    LEVEL_COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA,
    }

    def __init__(self, name: str = "mylogger", log_file: str = None, level=logging.DEBUG):
        """
        Args:
            name (str): Logger name
            log_file (str, optional): Path to log file (default None)
            level: logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # Prevent duplicate logs

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(self.ColoredFormatter())
        self.logger.addHandler(ch)

        # Optional file handler
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(level)
            fh.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(fh)

    class ColoredFormatter(logging.Formatter):
        """Custom formatter with colors based on log level"""
        def format(self, record):
            color = Logger.LEVEL_COLORS.get(record.levelname, "")
            message = super().format(record)
            return f"{color}{message}{Style.RESET_ALL}"

    # --- Shortcut methods ---
    def debug(self, msg, *args, **kwargs): self.logger.debug(msg, *args, **kwargs)
    def info(self, msg, *args, **kwargs): self.logger.info(msg, *args, **kwargs)
    def warning(self, msg, *args, **kwargs): self.logger.warning(msg, *args, **kwargs)
    def error(self, msg, *args, **kwargs): self.logger.error(msg, *args, **kwargs)
    def critical(self, msg, *args, **kwargs): self.logger.critical(msg, *args, **kwargs)

    # --- Decorator for logging execution time ---
    def log_execution(self, level="INFO"):
        """
        Decorator to log the start, end, and execution time of a function.
        Usage:
            @logger.log_execution(level="DEBUG")
            def my_func(...):
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                log_func = getattr(self, level.lower(), self.info)
                log_func(f"Started: {func.__name__}")
                start = time.time()
                result = func(*args, **kwargs)
                end = time.time()
                log_func(f"Finished: {func.__name__} in {end-start:.4f}s")
                return result
            return wrapper
        return decorator

"""
Custom Logger module for Django projects

Provides:
- Colored console logging based on log level
- Optional file logging with timestamps
- Automatic context tagging (views, middleware, functions)
- Execution time tracking via decorator and context manager
"""

import logging
import sys
import time
import os
from functools import wraps
from contextlib import contextmanager


# ---------------------- COLOR SUPPORT  ----------------------
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True, strip=False)
except ImportError:
    class Dummy:
        RESET_ALL = ""
        BRIGHT = ""
        RED = ""
        YELLOW = ""
        GREEN = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
    Fore = Style = Dummy()


# ---------------------- LOGGER CLASS  ----------------------
class Logger:
    """ Reusable Logger class for console and file logging """

    LEVEL_COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA,
    }

    def __init__(self, name: str = None, log_file: str = None, level=logging.DEBUG):
        """
        Args:
            name (str): Logger name (auto module name if None)
            log_file (str): Optional path for log file
            level: Logging level
        """
        # Auto-use caller module name if not provided
        if name is None:
            name = self._get_caller_module_name()

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  

        if not self.logger.handlers: 
            # Console handler
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(level)
            ch.setFormatter(self.ColoredFormatter())
            self.logger.addHandler(ch)

            # File handler
            if log_file:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                fh = logging.FileHandler(log_file)
                fh.setLevel(level)
                fh.setFormatter(logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S",)
                )
                self.logger.addHandler(fh)

    
    # ---------------------- INTERNAL HELPERS ----------------------

    class ColoredFormatter(logging.Formatter):
        """ Custom formatter with colors based on log level """

        def format(self, record):
            color = Logger.LEVEL_COLORS.get(record.levelname, "")
            message = super().format(record)
            return f"{color}{message}{Style.RESET_ALL}"
        
        def __init__(self):
            fmt = "%(asctime)s | [%(levelname)s] | %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
            super().__init__(fmt, datefmt=datefmt)


    def _get_caller_module_name(self):
        """ Automatically get the module name of the caller """
        import inspect
        stack = inspect.stack()
        if len(stack) > 2:
            module = inspect.getmodule(stack[2][0])
            return module.__name__ if module else "main"
        return "main"
    

    # ---------------------- SHORTCUT METHODS ----------------------
    
    def _add_view_context(self, msg):
        """ Add context label based on the current execution (View, Function, or Middleware) """
        import inspect
        stack = inspect.stack()

        for frame_info in stack:
            filename = frame_info.filename or ""
            func_name = frame_info.function
            self_obj = frame_info.frame.f_locals.get("self")

            # Middleware-specific logging 
            if "middleware" in filename.lower():
                cls_name = getattr(self_obj, "__class__", None)
                if cls_name:
                    return f"[{cls_name.__name__}] {msg}"
                return f"[Middleware] {msg}"

            # Skip framework and irrelevant internals
            if any(skip in filename for skip in ("django", "runserver", "socketserver", "wsgi")):
                continue

            # Class-based views
            if self_obj and hasattr(self_obj, "__class__"):
                cls_name = self_obj.__class__.__name__
                if cls_name.endswith("View"):
                    return f"[{cls_name}] {msg}"

            # -Function-based views
            if func_name.startswith("_") or func_name in {
                "info", "debug", "warning", "error", "critical", "run", "main"
            }:
                continue
            return f"[{func_name}] {msg}"

        return msg

    
    def debug(self, msg, *args, **kwargs):
        msg = self._add_view_context(msg)
        kwargs.setdefault("stacklevel", 2)
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        msg = self._add_view_context(msg)
        kwargs.setdefault("stacklevel", 2)
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        msg = self._add_view_context(msg)
        kwargs.setdefault("stacklevel", 2)
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        msg = self._add_view_context(msg)
        kwargs.setdefault("stacklevel", 2)
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        msg = self._add_view_context(msg)
        kwargs.setdefault("stacklevel", 2)
        self.logger.critical(msg, *args, **kwargs)


    # ---------------------- DECORATOR ----------------------

    def log_execution(self, level="INFO"):
        """ Decorator that logs start, end, and runtime (in ms) for functions  """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                log_func = getattr(self, level.lower(), self.info)
                start = time.time()
                log_func(f"START {func.__name__}", stacklevel=3)
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    # ensure exception trace is recorded as well
                    self.logger.exception(f"EXCEPTION in {func.__name__}", stacklevel=3)
                    raise
                duration_ms = (time.time() - start) * 1000.0
                log_func(f"END {func.__name__} | Duration={duration_ms:.2f}ms", stacklevel=3)
                return result
            return wrapper
        return decorator
    

    # ---------------------- Context Manager ----------------------

    @contextmanager
    def timer(self, name="block", level="DEBUG"):
        """ Context manager to measure and log the execution time of a code block """
        start = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000.0
            getattr(self, level.lower(), self.debug)(f"TIMER {name} | Duration={duration_ms:.2f}ms", stacklevel=3)
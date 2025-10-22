from mylogger import Logger
import time

# --- Create a logger that logs to file and console ---
logger = Logger()

# Log one message per level to see colors
logger.debug("This is a DEBUG message")       # Cyan
logger.info("This is an INFO message")        # Green
logger.warning("This is a WARNING message")   # Yellow
logger.error("This is an ERROR message")      # Red
logger.critical("This is a CRITICAL message") # Magenta


# --- Demonstrate execution time decorator ---
@logger.log_execution(level="INFO")
def slow_function():
    """Function that sleeps 2 seconds to simulate work"""
    time.sleep(2)

@logger.log_execution(level="DEBUG")
def fast_function():
    """Function that sleeps 0.5 seconds"""
    time.sleep(0.5)

slow_function()
fast_function()

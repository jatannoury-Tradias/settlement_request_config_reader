import logging
import inspect

from config.constants import ColorCodes
from tools.decorators import level

all_logs = []
class Formatter(logging.Formatter):
    """
    Defines the logs output format
    """
    color = ColorCodes.COLORS
    reset = ColorCodes.RESET_SEQ
    format = " %(levelname)s : (%(filename)s:%(lineno)d) : %(message)s - %(asctime)s"
    FORMATS = {
        logging.DEBUG: color['DEBUG'] + format + reset,
        logging.INFO: color['INFO'] + format + reset,
        logging.WARNING: color['WARNING'] + format + reset,
        logging.ERROR: color['ERROR'] + format + reset,
        logging.CRITICAL: color['CRITICAL'] + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class CustomLogger(logging.StreamHandler):
    def __init__(self) -> None:
        logging.StreamHandler.__init__(self)
        self.setFormatter(Formatter())


class FileLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.addHandler(CustomLogger())
        self.logger.propagate = False
        self.record = logging.LogRecord(
            name=self.logger.name,
            level=logging.INFO,
            pathname=self.get_caller(level=2).filename,
            lineno=self.get_caller(level=2).lineno,
            msg="",
            args=None,
            exc_info=None,
            func=None,
            sinfo=None
        )
    def get_all_logs(self):
        return all_logs
    def get_caller(self, level):
        """
        Defines from where the error has been raised(filepath and lineno)
        Args:
            level: Call Stack level

        Returns:Frame of error

        """
        frame = inspect.stack()[level]
        return frame

    @level(curr_level=logging.DEBUG)
    def log_debug(self, message):
        all_logs.append(message)
        self.logger.handle(self.record)

    @level(curr_level=logging.INFO)
    def log_info(self, message):
        all_logs.append(message)
        self.logger.handle(self.record)

    @level(curr_level=logging.WARNING)
    def log_warning(self, message):
        all_logs.append(message)
        self.logger.handle(self.record)

    @level(curr_level=logging.ERROR)
    def log_error(self, message):
        all_logs.append(message)
        self.logger.handle(self.record)

    @level(curr_level=logging.CRITICAL)
    def log_critical(self, message):
        all_logs.append(message)
        self.logger.handle(self.record)

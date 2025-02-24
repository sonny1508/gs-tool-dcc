import logging

import unreal

from logging import StreamHandler


class UnrealLogHandler(StreamHandler):
    """Basic Wrapper for python logging to output to unreal via it's dedicated log functions"""

    def emit(self, record):
        msg = self.format(record)
        if record.levelno >= logging.ERROR:
            unreal.log_error(msg)
        elif record.levelno == logging.WARNING:
            unreal.log_warning(msg)
        else:
            unreal.log(msg)

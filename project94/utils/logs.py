import io
import logging

from project94.utils.printer import Printer


class _PrinterFormatter(logging.Formatter):
    format_1 = "[%(asctime)s]"
    format_2 = "%(levelname)-8s %(message)s"

    FORMATS = {
        logging.DEBUG:    Printer.paint_gray(f"{format_1} {format_2}"),
        logging.INFO:     Printer.paint_gray(format_1) + " " + Printer.paint_light_purple(format_2),
        logging.WARNING:  Printer.paint_gray(format_1) + " " + Printer.paint_yellow(format_2),
        logging.ERROR:    Printer.paint_gray(format_1) + " " + Printer.paint_red(format_2),
        logging.CRITICAL: Printer.paint_gray(format_1) + " " + Printer._default_bold(Printer.paint_red(format_2))
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def create_full_logger(name):
    stream_handler = logging.StreamHandler(io.StringIO())
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(_PrinterFormatter())

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(stream_handler)
    return logger



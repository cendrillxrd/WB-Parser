import logging.config
import json
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
MAX_BYTES = 5_000_000
BACK_UP_COUNT = 5


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def setup_logging():
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console_fmt": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json_fmt": {
                "()": JsonFormatter
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console_fmt",
                "level": "INFO"
            },
            "file_debug": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json_fmt",
                "filename": os.path.join(LOG_DIR, "app.log"),
                "maxBytes": MAX_BYTES,
                "backupCount": BACK_UP_COUNT,
                "encoding": "utf-8",
                "level": "DEBUG"
            },
            "file_errors": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json_fmt",
                "filename": os.path.join(LOG_DIR, "errors.log"),
                "maxBytes": MAX_BYTES,
                "backupCount": BACK_UP_COUNT,
                "encoding": "utf-8",
                "level": "DEBUG"
            }
        },
        "root": {
            "handlers": ["console", "file_debug", "file_errors"],
            "level": "DEBUG"
        }
    }

    logging.config.dictConfig(logging_config)

import logging
import json
import uuid

class JsonFormatter(logging.Formatter):
    def format(self, record):
        if isinstance(record.msg, dict):
            log_record = record.msg.copy()
        else:
            log_record = {"message": record.msg}

        log_record["level"] = record.levelname
        log_record["timestamp"] = self.formatTime(record, self.datefmt)

        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        return json.dumps(log_record)


def get_logger():
    logger = logging.getLogger("schemaflowai")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = JsonFormatter()

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)

        # File handler
        fh = logging.FileHandler("logs/app.log")
        fh.setFormatter(formatter)

        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger


logger = get_logger()
import json
import logging
import time
from datetime import timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "event": record.getMessage(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "timestamp": time.time(),
        }
        if hasattr(record, "duration_ms"):
            payload["duration_ms"] = record.duration_ms
        if record.exc_info and record.exc_info[0]:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)

import time
import logging
from django.http import HttpRequest
from django.http.response import HttpResponseBase

logger = logging.getLogger("aop.metrics")


class AOPMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000
        extra = {
            "duration_ms": round(duration_ms, 2),
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
        }
        logger.info("request.completed", extra=extra)
        return response

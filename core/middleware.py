import time
import uuid
import logging
from django.http import HttpRequest
from django.http.response import HttpResponseBase

logger = logging.getLogger("aop.metrics")


class AOPMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        correlation_id = str(uuid.uuid4())
        request.correlation_id = correlation_id
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000
        ip = request.META.get("REMOTE_ADDR") or request.META.get("HTTP_X_FORWARDED_FOR", "unknown")
        extra = {
            "correlation_id": correlation_id,
            "duration_ms": round(duration_ms, 2),
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "ip": ip,
        }
        if request.user.is_authenticated:
            extra["user_id"] = str(request.user.id)
            extra["username"] = request.user.username
        logger.info("request.completed", extra=extra)
        return response

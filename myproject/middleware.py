import time
from django.utils.deprecation import MiddlewareMixin
from mylogger import Logger

logger = Logger()

class Middleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        start = getattr(request, "_start_time", None)
        if start:
            duration_ms = (time.time() - start) * 1000

            # Choose log level based on HTTP status
            if response.status_code >= 500:
                log_func = logger.error
            elif response.status_code >= 400:
                log_func = logger.warning
            else:
                log_func = logger.info

            log_func(
                f"Request {request.method} {request.path} | "
                f"Status={response.status_code} | Duration={duration_ms:.2f}ms"
            )
        return response
    
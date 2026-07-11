from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import uuid
import json
import time
import logging


logger = logging.getLogger(__name__)

class SecurityCheckToBlockMalaciousIPS(MiddlewareMixin):

    BLOCKED_IPS = {
        "192.168.1.100",
        "10.0.0.55",
    }

    SUSPICIOUS_AGENTS = [
        "sqlmap",
        "curl",
        "wget",
        "python-requests",
        "bot",
        "scanner",
    ]


    EXCLUDED_PATHS = [
        "/admin/",
        "/health/",
    ]

    @staticmethod
    def get_agent_ip(request):
        farwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if farwarded:

            return farwarded.split(",")[0]
        return request.META.get("REMOTE_ADDR")

    def process_request(self, request):
        logger.info("Process request has started")
        path = request.path

        if any(path.startswith(p) for p in self.EXCLUDED_PATHS):
            return JsonResponse(
                {"error": "access denied"},
                status=403
            )
        ip = self.get_agent_ip(request)

        user_agent = request.META.get("HTTP_USER_AGENT","").lower()

        if ip in self.BLOCKED_IPS:
            logger.warning(f"Blocked IP attempted access: {ip}")
            return JsonResponse(
                {"error": "access denied"},
                status=403
            )
        if any(ag in user_agent for ag in self.SUSPICIOUS_AGENTS):
            logger.warning(
                f"Suspicious agent detected | IP={ip} | UA={user_agent}"
            )
            return JsonResponse(
                {"error": "Suspicious activity detected"},
                status=403
            )
        
        request.audit_data = {
            "ip": ip,
            "path": path,
            "method": request.method,
            "user_agent": user_agent,
        }
    
    def process_response(self, request, response):
        logger.info("The response is being sent to the client")

        # logger.info(json.dumps({
        #         "request": request.audit_data,
        #         "status_code": response.status_code,
        #     }))
        
        if hasattr(request, "audit_data"):
            logger.info(json.dumps({
                "request": request.audit_data,
                "status_code": response.status_code,
            }))

        return response
    


class ProductionExceptionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info("The request is recieved in middlware")
        request.request_id = str(uuid.uuid4())
        start_time = time.time()

        try: 
            response = self.get_response(request)
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                {
                    "request_id": request.request_id,
                    "path": request.path,
                    "method": request.method,
                    "error": str(e),
                    "duration_sec": round(duration, 3),
                },
                exc_info=True,
            )

            return JsonResponse(
                {
                    "success": False,
                    "message": "Internal server error",
                    "request_id": request.request_id,
                },
                status=500,
            )
        logger.info("response is sent without any error successfully")
        response["X-Request-ID"] = request.request_id
        response["X-Response-Time"] = f"{round(time.time() - start_time, 3)}s"

        return response
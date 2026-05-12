"""
api/middleware.py — Minimal CORS middleware.

Allows the frontend index.html (opened as a local file) to call our Django API.
In production, replace "*" with your actual frontend domain.
"""

class CORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle preflight OPTIONS request
        if request.method == "OPTIONS":
            response = self._cors_response()
            return response

        response = self.get_response(request)
        response["Access-Control-Allow-Origin"]  = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    def _cors_response(self):
        from django.http import HttpResponse
        response = HttpResponse()
        response["Access-Control-Allow-Origin"]  = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

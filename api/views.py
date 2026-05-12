"""
api/views.py — Django views for the Finance Agent.

Two views:
  health_view  →  GET  /health
  query_view   →  POST /query

Senior note: Django views are just functions that take a request and return a response.
No magic here — same logic as the FastAPI version, different framework syntax.
"""

import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from agent import build_agent, run_query

# ── Build agent once at module load (equivalent to FastAPI's startup event) ───
_GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
_agent_executor = None

if _GROQ_API_KEY:
    _agent_executor = build_agent(api_key=_GROQ_API_KEY, verbose=True)
    print("✅ Finance Agent ready.")
else:
    print("⚠️  WARNING: GROQ_API_KEY not set. Agent will fail on queries.")


# ── GET /health ───────────────────────────────────────────────────────────────
@require_http_methods(["GET"])
def health_view(request):
    return JsonResponse({
        "status": "ok",
        "agent_ready": _agent_executor is not None
    })


# ── POST /query ───────────────────────────────────────────────────────────────
@csrf_exempt                          # needed since we're calling from plain HTML
@require_http_methods(["POST"])
def query_view(request):
    if not _agent_executor:
        return JsonResponse(
            {"detail": "Agent not initialized. Check GROQ_API_KEY."},
            status=503
        )

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    query = body.get("query", "").strip()
    if not query:
        return JsonResponse({"detail": "Query cannot be empty."}, status=400)

    result = run_query(_agent_executor, query)
    return JsonResponse(result)

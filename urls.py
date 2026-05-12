"""
urls.py — Two routes, that's all we need.
"""

from django.urls import path
from api.views import query_view, health_view

urlpatterns = [
    path("query",  query_view),
    path("health", health_view),
]

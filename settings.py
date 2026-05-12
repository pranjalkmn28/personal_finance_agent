"""
settings.py — Minimal Django settings for the Finance Agent API.

Keeping it lean — no database, no templates, no static files.
Just the JSON API we need.
"""

import os

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-in-prod")

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "api",              # our app
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "api.middleware.CORSMiddleware",   # simple CORS for the frontend HTML
]

ROOT_URLCONF = "urls"

# No database needed — all data comes from the CSV
DATABASES = {}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

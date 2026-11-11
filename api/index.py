import sys, os
from urllib.parse import parse_qs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
from main import app


original_wsgi_app = app.wsgi_app


def route_vercel_rewrite(environ, start_response):
    if environ.get("PATH_INFO") == "/api/index.py":
        rewritten_path = parse_qs(environ.get("QUERY_STRING", "")).get("path", [None])[0]
        if rewritten_path:
            environ["PATH_INFO"] = f"/api/{rewritten_path.lstrip('/')}"
    return original_wsgi_app(environ, start_response)


app.wsgi_app = route_vercel_rewrite

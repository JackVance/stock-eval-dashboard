#!/usr/bin/env python3
"""Local dev server: serves frontend static files + proxies /api/* to Lambda handler."""
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Must be set before handler import — handler reads these at module load
os.environ["LOCAL_MODE"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"

LAMBDA_PATH = Path(__file__).parent.parent / "src" / "lambda"
FRONTEND_PATH = Path(__file__).parent.parent / "src" / "frontend"
sys.path.insert(0, str(LAMBDA_PATH))


class LocalDevHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_PATH), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._invoke_lambda("GET")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            self._invoke_lambda("POST", body)
        else:
            self.send_error(404)

    def do_DELETE(self):
        if self.path.startswith("/api/"):
            self._invoke_lambda("DELETE")
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _invoke_lambda(self, method: str, body: str = "") -> None:
        """Build a fake API Gateway event and pass it to the Lambda handler."""
        from handler import main

        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)
        flat_params = {k: v[0] for k, v in query_params.items()} if query_params else None

        event = {
            "requestContext": {
                "http": {
                    "method": method,
                    "path": parsed.path,
                }
            },
            "queryStringParameters": flat_params,
            "body": body,
        }

        result = main(event, None)

        self.send_response(result.get("statusCode", 200))
        for key, value in result.get("headers", {}).items():
            self.send_header(key, value)
        self.end_headers()

        body_bytes = result.get("body", "").encode("utf-8")
        self.wfile.write(body_bytes)

    def log_message(self, format: str, *args) -> None:
        """Only log API requests — suppress static file noise."""
        if "/api/" in (args[0] if args else ""):
            print(f"[API] {args[0]}")


def create_local_config():
    """Write config.js with localhost API URL."""
    config_path = FRONTEND_PATH / "js" / "config.js"
    config_content = "window.CONFIG = { API_URL: 'http://localhost:3000' };\n"
    config_path.write_text(config_content)
    print(f"Created {config_path} for local development")


def main() -> None:
    port = int(os.environ.get("PORT", 3000))
    create_local_config()

    server = HTTPServer(("localhost", port), LocalDevHandler)

    print(f"""
=====================================
  Stock Dashboard - Local Dev Server
=====================================

Frontend: http://localhost:{port}
API Base: http://localhost:{port}/api

Endpoints:
  GET  /api/stock/AAPL?start_year=2020&end_year=2024
  GET  /api/tickers
  POST /api/tickers  {{"ticker": "NVDA"}}
  DELETE /api/tickers/AAPL

Press Ctrl+C to stop
=====================================
""")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()

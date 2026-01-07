"""
Simplified Mobile Backend - ULTRA MINIMAL version for testing
NO external dependencies - only Python standard library
Simple HTTP server with /health endpoint using http.server
"""

import os
import sys
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# Simple print-based logging (faster than logging module)
def log_info(message):
    print(f"INFO: {message}", flush=True)

def log_error(message):
    print(f"ERROR: {message}", flush=True, file=sys.stderr)


class SimpleBackendHandler(BaseHTTPRequestHandler):
    """
    Simple HTTP request handler with /health endpoint
    """

    def log_message(self, format, *args):
        # Override to use our logging
        log_info(f"{self.address_string()} - {format % args}")

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            # Health check endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {
                'status': 'healthy',
                'service': 'data20-mobile-backend',
                'version': 'simple-0.1.0',
                'message': 'Backend is running (minimal version)'
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

        elif self.path == '/':
            # Root endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            html = """
            <html>
            <head><title>Data20 Mobile Backend</title></head>
            <body>
                <h1>Data20 Mobile Backend</h1>
                <p>Status: <strong>Running</strong></p>
                <p>Version: Simple 0.1.0 (Python stdlib only)</p>
                <p><a href="/health">Health Check</a></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

        else:
            # 404 for other paths
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {'error': 'Not found', 'path': self.path}
            self.wfile.write(json.dumps(response).encode('utf-8'))

# Global variables
database_path = None
upload_path = None
logs_path = None
is_running = False
http_server = None


def setup_environment(db_path: str, upload_dir: str, logs_dir: str):
    """
    Setup environment for mobile backend
    """
    global database_path, upload_path, logs_path

    database_path = db_path
    upload_path = upload_dir
    logs_path = logs_dir

    # Create directories (without pathlib to be faster)
    for path in [upload_dir, logs_dir]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    # Set environment variables
    os.environ['DATA20_DATABASE_PATH'] = db_path
    os.environ['DATA20_UPLOAD_PATH'] = upload_dir
    os.environ['DATA20_LOGS_PATH'] = logs_dir
    os.environ['ENVIRONMENT'] = 'mobile'

    log_info("Environment configured:")
    log_info(f"  Database: {db_path}")
    log_info(f"  Uploads: {upload_dir}")
    log_info(f"  Logs: {logs_dir}")


def run_server(host: str = "127.0.0.1", port: int = 8001):
    """
    Run simple HTTP server with /health endpoint

    NOTE: This is a SIMPLIFIED version using only Python standard library.
    NO pip dependencies - uses http.server from stdlib.
    """
    global is_running, http_server

    try:
        log_info(f"Starting simple HTTP backend on {host}:{port}")
        log_info("Python backend initialized successfully!")
        log_info("  Using http.server from Python standard library")
        log_info("  Endpoints: / and /health")

        # Create HTTP server
        server_address = (host, port)
        http_server = HTTPServer(server_address, SimpleBackendHandler)

        is_running = True

        log_info(f"HTTP server listening on {host}:{port}")
        log_info("Backend is ready to accept requests!")

        # Serve requests (blocking call)
        http_server.serve_forever()

    except Exception as e:
        log_error(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        is_running = False
        raise
    finally:
        if http_server:
            http_server.server_close()
        log_info("HTTP server shut down")


def stop_server():
    """
    Stop the HTTP server
    """
    global is_running, http_server

    try:
        log_info("Stopping HTTP server...")
        is_running = False

        if http_server:
            http_server.shutdown()
            http_server.server_close()
            log_info("HTTP server stopped successfully")
        else:
            log_info("No HTTP server to stop")

    except Exception as e:
        log_error(f"Error stopping server: {e}")


# For testing
if __name__ == "__main__":
    import tempfile
    temp_dir = tempfile.gettempdir()

    setup_environment(
        db_path=os.path.join(temp_dir, "test_data20.db"),
        upload_dir=os.path.join(temp_dir, "data20_uploads"),
        logs_dir=os.path.join(temp_dir, "data20_logs")
    )

    run_server(host="127.0.0.1", port=8001)

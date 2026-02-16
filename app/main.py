from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict[str, str]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            self._send_json(200, {"service": "SCENI_01", "status": "ok"})
            return
        if self.path == "/health":
            self._send_json(200, {"health": "up"})
            return
        self._send_json(404, {"error": "not_found"})


def run() -> None:
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("SCENI_01 running on http://localhost:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()

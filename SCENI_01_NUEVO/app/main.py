from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(200, {
                "name": "SCENI_01",
                "message": "Super Critical Energy Infrastructure platform",
                "status": "ok"
            })
            return

        if self.path == "/health":
            self._send(200, {"status": "healthy"})
            return

        self._send(404, {"error": "Not found"})


def main():
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("Servidor SCENI_01 escuchando en http://localhost:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()

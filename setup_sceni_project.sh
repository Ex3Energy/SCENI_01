#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="SCENI_01_NUEVO"

mkdir -p "$PROJECT_DIR/app"

cat > "$PROJECT_DIR/app/main.py" <<'PYEOF'
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
PYEOF

cat > "$PROJECT_DIR/requirements.txt" <<'REQEOF'
# Este proyecto demo usa solo librería estándar de Python.
REQEOF

cat > "$PROJECT_DIR/.dockerignore" <<'DOCKIGNORE'
__pycache__/
*.pyc
*.pyo
*.pyd
.env
.venv
.git
.gitignore
DOCKIGNORE

cat > "$PROJECT_DIR/Dockerfile" <<'DOCKEOF'
FROM python:3.11-slim

WORKDIR /app
COPY app ./app
COPY requirements.txt ./requirements.txt

EXPOSE 8000
CMD ["python", "app/main.py"]
DOCKEOF

cat > "$PROJECT_DIR/docker-compose.yml" <<'COMPOSEEOF'
services:
  sceni:
    build: .
    container_name: sceni_01_demo
    ports:
      - "8000:8000"
    restart: unless-stopped
COMPOSEEOF

cat > "$PROJECT_DIR/README.md" <<'RDEOF'
# SCENI_01_NUEVO

## Ejecutar local
```bash
python app/main.py
```

Endpoints:
- http://localhost:8000/
- http://localhost:8000/health

## Ejecutar con Docker
```bash
docker compose up --build -d
docker compose logs -f
```

Detener:
```bash
docker compose down
```
RDEOF

echo "Estructura creada en: $PROJECT_DIR"

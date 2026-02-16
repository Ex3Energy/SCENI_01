#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-SCENI_01_NUEVO}"

if [ -e "$TARGET_DIR" ]; then
  echo "❌ La ruta '$TARGET_DIR' ya existe. Usa otra ruta o bórrala primero."
  exit 1
fi

mkdir -p "$TARGET_DIR/app"

cat > "$TARGET_DIR/app/main.py" <<'PYEOF'
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
PYEOF

cat > "$TARGET_DIR/requirements.txt" <<'REQEOF'
# No external dependencies required.
REQEOF

cat > "$TARGET_DIR/Dockerfile" <<'DOCKEOF'
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY app ./app

EXPOSE 8000

CMD ["python", "app/main.py"]
DOCKEOF

cat > "$TARGET_DIR/docker-compose.yml" <<'COMPOSEEOF'
services:
  sceni-api:
    build: .
    container_name: sceni_api
    ports:
      - "8000:8000"
    restart: unless-stopped
COMPOSEEOF

cat > "$TARGET_DIR/.dockerignore" <<'IGNOREEOF'
.git
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/
.vscode/
IGNOREEOF

cat > "$TARGET_DIR/README.md" <<'READEOF'
# SCENI_01 (carpeta generada automáticamente)

## 1) Ejecutar local (sin dependencias externas)

```bash
python app/main.py
```

Abrir:
- http://localhost:8000/
- http://localhost:8000/health

## 2) Ejecutar con Docker

```bash
docker compose up --build -d
docker compose logs -f
```

Detener:

```bash
docker compose down
```
READEOF

echo "✅ Proyecto creado en: $TARGET_DIR"
echo "👉 Siguiente paso: cd $TARGET_DIR"
echo "👉 Luego ábrelo en VS Code con: code $TARGET_DIR"

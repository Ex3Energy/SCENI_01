$ErrorActionPreference = "Stop"

$ProjectDir = "SCENI_01_NUEVO"
New-Item -ItemType Directory -Force -Path "$ProjectDir\app" | Out-Null

@'
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
'@ | Set-Content -Encoding UTF8 "$ProjectDir\app\main.py"

@'
# Este proyecto demo usa solo librería estándar de Python.
'@ | Set-Content -Encoding UTF8 "$ProjectDir\requirements.txt"

@'
__pycache__/
*.pyc
*.pyo
*.pyd
.env
.venv
.git
.gitignore
'@ | Set-Content -Encoding UTF8 "$ProjectDir\.dockerignore"

@'
FROM python:3.11-slim

WORKDIR /app
COPY app ./app
COPY requirements.txt ./requirements.txt

EXPOSE 8000
CMD ["python", "app/main.py"]
'@ | Set-Content -Encoding UTF8 "$ProjectDir\Dockerfile"

@'
services:
  sceni:
    build: .
    container_name: sceni_01_demo
    ports:
      - "8000:8000"
    restart: unless-stopped
'@ | Set-Content -Encoding UTF8 "$ProjectDir\docker-compose.yml"

@'
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
'@ | Set-Content -Encoding UTF8 "$ProjectDir\README.md"

Write-Host "Estructura creada en: $ProjectDir"

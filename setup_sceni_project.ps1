param(
    [string]$TargetDir = "SCENI_01_NUEVO"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (Test-Path -Path $TargetDir) {
    Write-Host "❌ La ruta '$TargetDir' ya existe. Usa otra ruta o bórrala primero."
    exit 1
}

New-Item -ItemType Directory -Path (Join-Path $TargetDir "app") -Force | Out-Null

@'
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
'@ | Set-Content -Path (Join-Path $TargetDir "app/main.py") -Encoding UTF8

@'
# No external dependencies required.
'@ | Set-Content -Path (Join-Path $TargetDir "requirements.txt") -Encoding UTF8

@'
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY app ./app

EXPOSE 8000

CMD ["python", "app/main.py"]
'@ | Set-Content -Path (Join-Path $TargetDir "Dockerfile") -Encoding UTF8

@'
services:
  sceni-api:
    build: .
    container_name: sceni_api
    ports:
      - "8000:8000"
    restart: unless-stopped
'@ | Set-Content -Path (Join-Path $TargetDir "docker-compose.yml") -Encoding UTF8

@'
.git
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/
.vscode/
'@ | Set-Content -Path (Join-Path $TargetDir ".dockerignore") -Encoding UTF8

@'
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
'@ | Set-Content -Path (Join-Path $TargetDir "README.md") -Encoding UTF8

Write-Host "✅ Proyecto creado en: $TargetDir"
Write-Host "👉 Siguiente paso: Set-Location $TargetDir"
Write-Host "👉 Luego ábrelo en VS Code con: code $TargetDir"

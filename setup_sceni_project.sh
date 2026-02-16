#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-SCENI_01_NUEVO}"

if [ -e "$TARGET_DIR" ]; then
  echo "❌ La ruta '$TARGET_DIR' ya existe. Usa otra ruta o bórrala primero."
  exit 1
fi

mkdir -p "$TARGET_DIR/app"

cat > "$TARGET_DIR/app/main.py" <<'PYEOF'
from fastapi import FastAPI

app = FastAPI(title="SCENI_01 API", version="0.1.0")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"service": "SCENI_01", "status": "ok"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"health": "up"}
PYEOF

cat > "$TARGET_DIR/requirements.txt" <<'REQEOF'
fastapi==0.116.1
uvicorn[standard]==0.35.0
REQEOF

cat > "$TARGET_DIR/Dockerfile" <<'DOCKEOF'
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
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

## 1) Ejecutar local (sin Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Abrir:
- http://localhost:8000/
- http://localhost:8000/health
- http://localhost:8000/docs

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

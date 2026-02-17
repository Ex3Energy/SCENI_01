#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATIC_PORT="4173"
API_PORT="8000"

cleanup() {
  if [[ -n "${STATIC_PID:-}" ]] && kill -0 "$STATIC_PID" 2>/dev/null; then
    kill "$STATIC_PID" || true
  fi
  if [[ -n "${API_PID:-}" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" || true
  fi
}
trap cleanup EXIT

echo "[1/5] Verificando estructura..."
[[ -f "$ROOT_DIR/index.html" ]] || { echo "Falta index.html"; exit 1; }
[[ -f "$ROOT_DIR/styles.css" ]] || { echo "Falta styles.css"; exit 1; }
[[ -f "$ROOT_DIR/app.js" ]] || { echo "Falta app.js"; exit 1; }
[[ -f "$ROOT_DIR/SCENI_01_NUEVO/app/main.py" ]] || { echo "Falta SCENI_01_NUEVO/app/main.py"; exit 1; }

echo "[2/5] Levantando sitio estático en puerto ${STATIC_PORT}..."
python3 -m http.server "$STATIC_PORT" --directory "$ROOT_DIR" >/tmp/sceni_static.log 2>&1 &
STATIC_PID=$!
sleep 1

echo "[3/5] Levantando API demo en puerto ${API_PORT}..."
python3 "$ROOT_DIR/SCENI_01_NUEVO/app/main.py" >/tmp/sceni_api.log 2>&1 &
API_PID=$!
sleep 1

echo "[4/5] Ejecutando smoke tests..."
curl -fsS "http://127.0.0.1:${STATIC_PORT}/" | rg -q "SCENI_01"
curl -fsS "http://127.0.0.1:${STATIC_PORT}/app.js" | rg -q "renderCards"

for _ in {1..10}; do
  if curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

curl -fsS "http://127.0.0.1:${API_PORT}/" | rg -q '"status": "ok"'
curl -fsS "http://127.0.0.1:${API_PORT}/health" | rg -q '"status": "healthy"'

echo "[5/5] OK - Desarrollo en acción"
echo "- Frontend: http://localhost:${STATIC_PORT}"
echo "- API:      http://localhost:${API_PORT}/health"

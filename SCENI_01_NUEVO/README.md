# SCENI_01_NUEVO Backend

Backend HTTP del motor de decisión SCENI con persistencia SQLite.

## Ejecutar
```bash
python app/main.py
```

## Variable opcional
- `SCENI_DB_PATH` (default: `SCENI_01_NUEVO/data/sceni.db`)

## Endpoints principales
- `GET /health`
- `GET /api/v1/storage/status`
- `POST /api/v1/opportunities`
- `POST /api/v1/opportunities/{id}/simulate`
- `GET /api/v1/opportunities/{id}/designs`
- `GET /api/v1/snapshots/{snapshot_id}`
- `GET /api/v1/market/ercot/{node}`
- `GET /docs`

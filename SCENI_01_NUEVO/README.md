# SCENI_01_NUEVO Backend

Backend HTTP del motor de decisión SCENI.

## Ejecutar
```bash
python app/main.py
```

## Endpoints principales
- `GET /health`
- `POST /api/v1/opportunities`
- `POST /api/v1/opportunities/{id}/simulate`
- `GET /api/v1/opportunities/{id}/designs`
- `GET /api/v1/snapshots/{snapshot_id}`
- `GET /api/v1/market/ercot/{node}`
- `GET /docs`

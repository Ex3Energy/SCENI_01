# SCENI_01_NUEVO Backend

Backend HTTP del motor de decisión SCENI con persistencia SQLite cloud-ready e ingesta externa.

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
- `GET /api/v1/data-sources`
- `POST /api/v1/data-sources`
- `POST /api/v1/data-sources/{id}/sync`
- `GET /api/v1/observations?source_id=<id>`
- `POST /api/v1/ingestion/bootstrap-demo`
- `GET /api/v1/network/constraints?node=HB_HOUSTON`
- `GET /api/v1/market/prices?node=HB_HOUSTON`
- `GET /api/v1/weather?node=HB_HOUSTON`
- `GET /docs`


## Arquitectura objetivo
Ver `../docs/SCENI_ARCHITECTURE_BLUEPRINT.md` para la arquitectura recomendada (frontend, backend, data platform, observabilidad y roadmap).

# SCENI_01
Super Critical Energy Infrastructure platform.

## Demo SCENI (Backend + Frontend)
Esta versión incluye:
- **Backend HTTP determinístico** con persistencia SQLite cloud-ready.
- **Frontend dashboard** para crear oportunidad, simular y comparar diseños.
- **Capa de ingesta de datos externos** (ERCOT open data vía EIA + meteorología Open-Meteo).

## Ejecutar backend (local)
```bash
cd SCENI_01_NUEVO
python app/main.py
```
Backend disponible en:
- `http://localhost:8000/health`
- `http://localhost:8000/api/v1/storage/status`
- `http://localhost:8000/docs`

## Ejecutar frontend
En otra terminal:
```bash
python3 -m http.server 4173
```
Abrir:
- `http://localhost:4173`

En el dashboard, deja `API Base URL = http://localhost:8000` y pulsa **Crear y simular**.

## Base de datos en la nube desde GitHub
Ya está preparado para desplegar backend desde GitHub con persistencia:
- `render.yaml` crea servicio + disco persistente.
- `SCENI_DB_PATH=/var/data/sceni.db`.

### Pasos (Render + GitHub)
1. Push del repo a GitHub.
2. En Render: **New + Blueprint** y conecta el repo.
3. Verifica disco persistente `/var/data`.
4. Deploy.
5. Probar `https://<tu-backend>.onrender.com/api/v1/storage/status`.
6. Usar esa URL HTTPS en el frontend (GitHub Pages).

## Integración de fuentes externas (nuevo)
### 1) Crear fuente meteorológica (Open-Meteo)
```bash
curl -X POST http://localhost:8000/api/v1/data-sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenMeteo Houston",
    "source_type": "weather_openmeteo",
    "base_url": "https://api.open-meteo.com/v1/forecast",
    "config": {"lat": 29.7604, "lon": -95.3698}
  }'
```

### 2) Crear fuente ERCOT open data (EIA)
```bash
curl -X POST http://localhost:8000/api/v1/data-sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ERCOT EIA",
    "source_type": "ercot_open_data",
    "base_url": "https://api.eia.gov/v2/electricity/rto/region-data/data",
    "config": {"eia_api_key": "DEMO_KEY"}
  }'
```

### 3) Sincronizar una fuente
```bash
curl -X POST http://localhost:8000/api/v1/data-sources/<SOURCE_ID>/sync
```

### 4) Consultar observaciones ingeridas
```bash
curl "http://localhost:8000/api/v1/observations?source_id=<SOURCE_ID>&limit=20"
```


## Arquitectura objetivo (Frontend + Backend + Data)
- Revisa el blueprint detallado: `docs/SCENI_ARCHITECTURE_BLUEPRINT.md`.
- Incluye arquitectura de referencia para SaaS energético, modelo de datos cloud y roadmap de integración ERCOT + clima + restricciones de red.

## Nuevos endpoints de datos energéticos
- `POST /api/v1/ingestion/bootstrap-demo` (inyecta dataset inicial de restricciones/precios/clima por nodo).
- `GET /api/v1/network/constraints?node=HB_HOUSTON`
- `GET /api/v1/market/prices?node=HB_HOUSTON`
- `GET /api/v1/weather?node=HB_HOUSTON`

Ejemplo rápido:
```bash
curl -X POST http://localhost:8000/api/v1/ingestion/bootstrap-demo \
  -H "Content-Type: application/json" \
  -d '{"node": "HB_HOUSTON"}'

curl "http://localhost:8000/api/v1/network/constraints?node=HB_HOUSTON&limit=10"
curl "http://localhost:8000/api/v1/market/prices?node=HB_HOUSTON&limit=10"
curl "http://localhost:8000/api/v1/weather?node=HB_HOUSTON&limit=10"
```


## Pasos sugeridos (ejecución inmediata)
1. Registrar fuentes por defecto:
```bash
curl -X POST http://localhost:8000/api/v1/ingestion/register-default-sources
```
2. Ejecutar sincronización completa:
```bash
curl -X POST http://localhost:8000/api/v1/ingestion/run-all
```
3. Revisar estado de calidad y frescura de datos:
```bash
curl "http://localhost:8000/api/v1/data-quality/status?max_age_minutes=120"
```
4. Consultar datasets integrados por nodo:
```bash
curl "http://localhost:8000/api/v1/network/constraints?node=HB_HOUSTON&limit=10"
curl "http://localhost:8000/api/v1/market/prices?node=HB_HOUSTON&limit=10"
curl "http://localhost:8000/api/v1/weather?node=HB_HOUSTON&limit=10"
```

## Smoke test completo
```bash
./compile_and_smoke_test.sh
```
Windows:
```powershell
powershell -ExecutionPolicy Bypass -File .\compile_and_smoke_test.ps1
```

## Troubleshooting: "Failed to fetch" en Crear y simular
- Si el backend no responde, el dashboard activa un **modo local de contingencia** para que puedas seguir probando simulación y ranking (sin persistencia en DB).
- En frontend publicado (GitHub Pages), **API Base URL debe ser HTTPS pública** (ej. `https://sceni-backend.onrender.com`).
- Si abres la UI desde GitHub Pages, `localhost` apunta a tu computador local, no al backend en la nube.
- Si persiste el error, prueba `https://<tu-backend>/health` en navegador.
- Algunos backends en free tier (ej. Render) tardan 30-60s en despertar (cold start). Usa **Probar conexión backend** y espera ese tiempo antes de reintentar.
- Puedes forzar backend demo cloud con el botón **Usar backend cloud demo** (apunta a `https://sceni-backend.onrender.com`).


## Runbook de salida a producción
- Revisa `docs/GO_LIVE_RUNBOOK.md` para checklist operativo y KPIs de valor real.
- Nuevo endpoint de valor: `GET /api/v1/value/summary`.
- Script de validación integral: `python3 scripts/release_readiness_check.py`

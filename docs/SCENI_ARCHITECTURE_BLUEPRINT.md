# SCENI Architecture Blueprint (Frontend + Backend + Data)

## 1) Objetivo
Diseñar SCENI como plataforma cloud-native para decisiones de infraestructura crítica con trazabilidad, reproducibilidad y conectividad robusta a fuentes externas (ERCOT, red, meteorología).

## 2) Arquitectura de referencia

### Frontend (BFF-friendly)
- **SPA dashboard** (actual) para:
  - Gestión de oportunidades.
  - Ejecución de simulaciones.
  - Comparación de diseños y snapshots.
  - Visualización de series de precio, restricciones y clima.
- **Evolución recomendada**:
  - Migrar a React + TypeScript + TanStack Query.
  - Feature flags para entornos (local/staging/prod).
  - Auth (OIDC) + RBAC por rol (analyst/investor/admin).

### Backend (servicios)
- **API Core** (FastAPI recomendado en siguiente etapa):
  - Oportunidades, simulación, ranking, snapshots.
  - Endpoints de mercado/red/clima y data quality.
- **Ingestion Service**:
  - Conectores ERCOT/EIA, Open-Meteo/NOAA, red/restricciones.
  - Scheduler (cron/queue), retry/backoff, deduplicación, watermark por fuente.
- **Scoring Engine**:
  - Firm energy, unserved, IRR, riesgo, emisiones.
  - Versionado de motor y supuestos.

### Datos
- **OLTP**: PostgreSQL (cloud) para entidades de negocio.
- **Time-series**: TimescaleDB/ClickHouse para precio y clima horario.
- **Object storage**: snapshots raw y reportes (S3-compatible).
- **Cache**: Redis para resultados calientes y throttling.

### Observabilidad y operación
- Logging estructurado JSON.
- Métricas de API e ingestion (Prometheus/OpenTelemetry).
- Alertas por latencia, error rate, data freshness.
- CI/CD: test + lint + smoke + deploy canary.

## 3) Modelo de datos mínimo recomendado
- `opportunities`
- `designs_v2`
- `snapshots`
- `grid_constraints` (POI, seguridad N-1, mantenimientos)
- `market_prices` (LMP, volatilidad)
- `weather_samples` (temperatura, viento, nubosidad)
- `data_sources`, `ingestion_runs`, `source_observations`

## 4) Integraciones externas
- **ERCOT/EIA**: precios nodales, estadísticas de volatilidad.
- **Meteorología**: Open-Meteo (rápido), NOAA (productivo).
- **Restricciones de red**: datasets públicos ERCOT/TSO + catálogos propios.

## 5) Roadmap de implementación (rápido)
1. Estabilización API + DB cloud + migraciones.
2. Ingestion robusta (retry/backoff/caching + scheduler).
3. Data contracts y validaciones de calidad.
4. Dashboard analítico (curvas, mapas, comparador de escenarios).
5. Financiero avanzado (NPV/DSCR/LCOE + sensibilidad).

## 6) KPIs de plataforma
- Disponibilidad API > 99.5%.
- p95 latencia < 400 ms en consultas.
- Freshness mercado/clima < 60 min.
- Trazabilidad 100% de snapshots y versiones de motor.

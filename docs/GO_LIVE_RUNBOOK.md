# SCENI Go-Live Runbook (enfoque de valor real)

## Objetivo de salida a producción
Asegurar que SCENI entregue valor en decisiones de infraestructura crítica con tres pilares:
1. **Conectividad de datos** (restricciones, precios, clima).
2. **Calidad y frescura** de información para decisiones.
3. **Resultados accionables** (Firm Energy, IRR, riesgo operativo).

## Checklist de coherencia técnica
- Backend saludable: `GET /health`.
- Persistencia activa: `GET /api/v1/storage/status`.
- Ingesta base ejecutada: `POST /api/v1/ingestion/bootstrap-demo`.
- Simulación completa disponible: `POST /api/v1/opportunities/{id}/simulate`.
- Resumen de valor disponible: `GET /api/v1/value/summary`.
- Calidad de datos visible: `GET /api/v1/data-quality/status`.

## KPI mínimos para considerar valor real
- `avg_firm_energy_pct >= 70%`
- `avg_irr_pct >= 8%`
- `data_quality.grid_constraints|market_prices|weather_samples == fresh`

## Flujo sugerido de operación diaria
1. Ejecutar sincronización de fuentes (`register-default-sources`, `run-all`).
2. Revisar `data-quality/status`.
3. Correr simulaciones de oportunidades prioritarias.
4. Revisar `value/summary` para decisión ejecutiva.
5. Publicar memo de decisión con snapshot IDs.

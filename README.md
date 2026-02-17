# SCENI_01
Super Critical Energy Infrastructure platform.

## Demo SCENI (Backend + Frontend)
Esta versión incluye:
- **Backend HTTP determinístico** con persistencia SQLite (opportunities, snapshots, designs_v2).
- **Frontend dashboard** para crear oportunidad, simular y comparar diseños.

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

## Incluir base de datos en la nube desde GitHub
Sí se puede. En este repo ya quedó preparado para eso:
- Backend persiste en SQLite usando variable `SCENI_DB_PATH`.
- Archivo `render.yaml` incluido para despliegue automático desde GitHub en Render con disco persistente.

### Opción recomendada (Render + GitHub)
1. Sube este repo a GitHub.
2. En Render, crea **New + Blueprint** y conecta el repo.
3. Render detecta `render.yaml` y crea servicio `sceni-backend`.
4. Verifica que exista el disco persistente montado en `/var/data`.
5. Confirma variable: `SCENI_DB_PATH=/var/data/sceni.db`.
6. Deploy.
7. Prueba: `https://<tu-servicio>.onrender.com/api/v1/storage/status`
8. Usa esa URL en el frontend publicado en GitHub Pages en el campo **API Base URL**.

> Importante: GitHub Pages no ejecuta backend ni base de datos; solo sirve archivos estáticos.

## Smoke test completo
```bash
./compile_and_smoke_test.sh
```
Windows:
```powershell
powershell -ExecutionPolicy Bypass -File .\compile_and_smoke_test.ps1
```

## Troubleshooting: "Failed to fetch" en Crear y simular
- En frontend publicado (GitHub Pages), **API Base URL debe ser HTTPS pública** (ej. `https://sceni-backend.onrender.com`).
- Ese error significa que el frontend no puede llegar al backend en `API Base URL`.
- Si el frontend está en **HTTPS** y tu backend está en **HTTP** (no localhost), el navegador bloquea la petición (mixed content). Usa backend con HTTPS.
- La UI intenta autocorregir `http://`→`https://` para backends públicos cuando presionas **Probar conexión backend**.
- Si abres la UI desde GitHub Pages, `http://localhost:8000` apunta a **tu PC**, no a GitHub.
- Solución rápida:
  1. Ejecuta backend local: `cd SCENI_01_NUEVO && python app/main.py`
  2. Ejecuta frontend local: `python3 -m http.server 4173`
  3. Abre `http://localhost:4173` y usa `API Base URL = http://localhost:8000`
- Alternativa: publica el backend (Render/Railway/Fly) y usa esa URL pública en el campo `API Base URL`.

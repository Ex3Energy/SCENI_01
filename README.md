# SCENI_01
Super Critical Energy Infrastructure platform.

## Demo SCENI (Backend + Frontend)
Esta versión incluye:
- **Backend HTTP determinístico** con oportunidades, generación de candidatos, snapshots, firm energy, scoring/ranking y mock ERCOT.
- **Frontend dashboard** para crear oportunidad, simular y comparar diseños.

## Ejecutar backend
```bash
cd SCENI_01_NUEVO
python app/main.py
```
Backend disponible en:
- `http://localhost:8000/health`
- `http://localhost:8000/docs`

## Ejecutar frontend
En otra terminal:
```bash
python3 -m http.server 4173
```
Abrir:
- `http://localhost:4173`

En el dashboard, deja `API Base URL = http://localhost:8000` y pulsa **Crear y simular**.

## Smoke test completo
```bash
./compile_and_smoke_test.sh
```
Windows:
```powershell
powershell -ExecutionPolicy Bypass -File .\compile_and_smoke_test.ps1
```

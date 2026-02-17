# SCENI_01
Super Critical Energy Infrastructure platform.

## ¿Por qué falla `cd /workspace/SCENI_01` en Windows?
Esa ruta (`/workspace/SCENI_01`) pertenece al entorno Linux de este chat, no a tu PC con PowerShell.
En tu equipo debes usar la ruta local, por ejemplo:

```powershell
cd "C:\Users\SantiagoParraPosada\OneDrive - ERCO ENERGIA SAS\Desktop\EX3Energy\SCENI_1"
```

## Compilación completa (ver el desarrollo en acción)

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File .\compile_and_smoke_test.ps1
```

### Linux / macOS / Git Bash
```bash
./compile_and_smoke_test.sh
```

Estos scripts levantan automáticamente:
- Frontend estático en `http://localhost:4173`
- API demo en `http://localhost:8000`

Y validan smoke tests de ambos servicios (`/`, `/app.js`, `/health`).

## Flujo recomendado para principiantes

### Opción A (Windows / PowerShell)
1. Abre PowerShell dentro de la carpeta del proyecto.
2. Ejecuta:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\setup_sceni_project.ps1
   ```
3. Entra a la carpeta creada y levanta el servicio:
   ```powershell
   cd .\SCENI_01_NUEVO
   python .\app\main.py
   ```
4. Prueba en navegador:
   - http://localhost:8000/
   - http://localhost:8000/health

### Opción B (Linux / macOS / Git Bash)
```bash
./setup_sceni_project.sh
cd SCENI_01_NUEVO
python app/main.py
```

### Alternativa con Docker
```bash
cd SCENI_01_NUEVO
docker compose up --build -d
docker compose logs -f
```

Para detener:
```bash
docker compose down
```

## Archivos que genera el script

```text
SCENI_01_NUEVO/
├── app/
│   └── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .dockerignore
└── README.md
```

## Publicación en GitHub Pages (sitio estático demo)
Si en GitHub solo ves `README.md`, casi siempre estás viendo otra rama o no hiciste push de la rama correcta.

1. Verifica rama actual:
   ```bash
   git branch --show-current
   ```
2. Sube exactamente esa rama:
   ```bash
   git push -u origin <tu-rama>
   ```
3. Para Pages en rama `main`, haz merge/push a `main`.
4. En GitHub, ve a **Settings → Pages** y selecciona **Source: GitHub Actions**.
5. Espera el workflow **Deploy static site to GitHub Pages** en verde.


## Nuevo en la demo
- Estimador de infraestructura crítica para Texas (CAPEX, cronograma y recomendación de ubicación).

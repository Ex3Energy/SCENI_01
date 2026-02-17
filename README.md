# SCENI_01
Super Critical Energy Infrastructure platform.

## ¿Por qué falla `cd /workspace/SCENI_01` en Windows?
Esa ruta (`/workspace/SCENI_01`) pertenece al entorno Linux de este chat, no a tu PC con PowerShell.
En tu equipo debes usar tu ruta local, por ejemplo:

```powershell
cd "C:\Users\SantiagoParraPosada\OneDrive - ERCO ENERGIA SAS\Desktop\EX3Energy\SCENI_1"
```

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
El repositorio también contiene una demo web estática (`index.html`, `styles.css`, `app.js`) y workflow para GitHub Pages.
Si quieres probar esa versión visual:
1. Haz push a `main`.
2. En GitHub, ve a **Settings → Pages** y selecciona **Source: GitHub Actions**.
3. Espera el workflow **Deploy static site to GitHub Pages** en verde.

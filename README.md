# SCENI_01

Super Critical Energy Infrastructure platform.

## ¿Por qué te falló `cd /workspace/SCENI_01` en Windows?

Esa ruta (`/workspace/SCENI_01`) es del entorno Linux de este chat, no de tu PC con PowerShell.
En tu equipo debes usar la ruta local donde está tu carpeta, por ejemplo:

```powershell
cd "C:\Users\SantiagoParraPosada\OneDrive - ERCO ENERGIA SAS\Desktop\EX3Energy\SCENI_1"
```

## Flujo recomendado para principiantes

### Opción A (Windows / PowerShell)

1) Abre PowerShell dentro de tu carpeta del proyecto (la que ya tienes en tu escritorio).

2) Ejecuta el script para crear una carpeta nueva lista:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_sceni_project.ps1
```

3) Entra a la carpeta creada y ejecuta:

```powershell
cd .\SCENI_01_NUEVO
python .\app\main.py
```

4) Abre en navegador:

- http://localhost:8000/
- http://localhost:8000/health

### Opción B (Linux / macOS / Git Bash)

```bash
./setup_sceni_project.sh
cd SCENI_01_NUEVO
python app/main.py
```

## Alternativa con Docker

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

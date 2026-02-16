# SCENI_01

Super Critical Energy Infrastructure platform.

## Si tienes poca experiencia: usa este camino (recomendado)

### Paso 1: crea una carpeta nueva con todo listo (1 comando)

Desde una terminal dentro de este repositorio ejecuta:

```bash
./setup_sceni_project.sh
```

Eso te crea automáticamente una carpeta llamada `SCENI_01_NUEVO` con todos los archivos necesarios.

Si quieres otro nombre/ruta:

```bash
./setup_sceni_project.sh /ruta/que-tu-quieras/MI_PROYECTO
```

### Paso 2: abre esa carpeta en VS Code

```bash
code SCENI_01_NUEVO
```

### Paso 3: ejecuta la app (sin Docker)

En la terminal de VS Code:

```bash
cd SCENI_01_NUEVO
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Abre en navegador:

- http://localhost:8000/
- http://localhost:8000/health
- http://localhost:8000/docs

---

## Alternativa con Docker

Si tienes Docker instalado:

```bash
cd SCENI_01_NUEVO
docker compose up --build -d
docker compose logs -f
```

Para detener:

```bash
docker compose down
```

---

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

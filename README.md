# SCENI_01

Super Critical Energy Infrastructure platform.

## Raíz del proyecto

Trabaja siempre desde esta ruta:

```bash
/workspace/SCENI_01
```

Verifica ubicación:

```bash
pwd
```

## Estructura mínima del proyecto

```text
SCENI_01/
├── app/
│   └── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .dockerignore
└── README.md
```

## Ejecutar local (sin Docker)

```bash
cd /workspace/SCENI_01
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Probar endpoints:

- `http://localhost:8000/`
- `http://localhost:8000/health`
- `http://localhost:8000/docs`

## Ejecutar con Docker Compose

```bash
cd /workspace/SCENI_01
docker compose up --build -d
```

Ver logs:

```bash
docker compose logs -f
```

Detener:

```bash
docker compose down
```

## Qué ejecutar en GitHub vs terminal

- En **GitHub web** solo ves/editar archivos y CI.
- Los comandos `python`, `pip`, `docker`, `uvicorn` se ejecutan en tu **terminal** (local, VPS o Codespaces).

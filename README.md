# SCENI_01

Super Critical Energy Infrastructure platform.

## Si tienes poca experiencia: usa este camino (recomendado)

### Paso 1: crea una carpeta nueva con todo listo (1 comando)

```bash
./setup_sceni_project.sh
```

Crea `SCENI_01_NUEVO` con todos los archivos.

### Paso 2: abre esa carpeta en VS Code

```bash
code SCENI_01_NUEVO
```

### Paso 3: ejecuta la app (sin instalar paquetes)

```bash
cd SCENI_01_NUEVO
python app/main.py
```

Abre en navegador:

- http://localhost:8000/
- http://localhost:8000/health

---

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

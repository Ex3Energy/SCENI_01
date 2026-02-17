# SCENI_01
Super Critical Energy Infraestructure platform

## Demo local (prueba real del sitio)
Este repositorio incluye una demo web funcional para validar navegación, UI y un flujo básico de formulario.

### Requisitos
- Python 3 (para levantar un servidor estático rápido)

### Ejecutar la demo local
```bash
python3 -m http.server 4173
```

Abrir en el navegador:
- http://localhost:4173

## Publicar y dejar el repo completo en GitHub
Si en GitHub solo ves el `README`, normalmente se debe a que no se subió el último commit o se subió otra rama.

### 1) Verifica tu rama local
```bash
git branch --show-current
git log --oneline -n 5
git status
```

### 2) Configura el remoto (si aún no existe)
```bash
git remote add origin <URL_DE_TU_REPO>
```

Si ya existe:
```bash
git remote -v
```

### 3) Sube esta rama a GitHub
```bash
git push -u origin main
```

> Si tu rama no se llama `main`, reemplázala por el nombre real de tu rama.

### 4) Confirma en GitHub
Debes ver estos archivos en la raíz:
- `index.html`
- `styles.css`
- `app.js`
- `README.md`
- `.nojekyll`
- `.github/workflows/deploy-pages.yml`

## Ejecutar desde GitHub (GitHub Pages)
Este repo ya incluye workflow para publicar automáticamente el sitio estático en GitHub Pages al hacer push a `main`.

### Activación en GitHub
1. En tu repo, entra a **Settings → Pages**.
2. En **Build and deployment**, selecciona **Source: GitHub Actions**.
3. Haz push a `main`.
4. Espera que el workflow **Deploy static site to GitHub Pages** termine en verde.
5. Abre la URL publicada que mostrará GitHub Pages.

## Qué incluye esta demo
- Landing de SCENI_01.
- Panel simulado de estado de infraestructura.
- Formulario de solicitud de piloto (simulado en frontend).
- Estilos responsivos básicos para escritorio/móvil.

## Próximo paso recomendado
Conectar este frontend a una API real para persistir solicitudes de piloto y estados operativos.

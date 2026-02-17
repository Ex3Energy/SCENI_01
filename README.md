# SCENI_01
Super Critical Energy Infraestructure platform

## Demo local (prueba real del sitio)
Este repositorio ahora incluye una demo web funcional para validar navegación, UI y un flujo básico de formulario.

### Requisitos
- Python 3 (para levantar un servidor estático rápido)

### Ejecutar la demo
```bash
python3 -m http.server 4173
```

Abrir en el navegador:
- http://localhost:4173

## Qué incluye esta demo
- Landing de SCENI_01.
- Panel simulado de estado de infraestructura.
- Formulario de solicitud de piloto (simulado en frontend).
- Estilos responsivos básicos para escritorio/móvil.

## Próximo paso recomendado
Conectar este frontend a una API real para persistir solicitudes de piloto y estados operativos.

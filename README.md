# Bot de Control de No Conformidades (NC) — Celsia / ISES

API en **FastAPI** para auditar el ciclo de vida de las No Conformidades del
proyecto: detectar las NC que no fueron notificadas al contratista dentro del
plazo, calcular semáforos de tiempos (SLA) y exponer los datos al dashboard en
Angular.

> El bot **audita y alerta**; no envía notificaciones a los contratistas (eso
> sigue siendo responsabilidad del supervisor).

## Arquitectura por capas

```
app/
├── main.py                # App FastAPI, CORS, arranque (lifespan)
├── core/                  # Config, logging y motor de tiempos (SLA)
│   ├── config.py          #   settings desde .env (tipado)
│   ├── logging.py
│   └── sla.py             #   días hábiles + festivos Colombia + semáforos
├── db/                    # Conexiones
│   ├── session.py         #   BD LOCAL de control (SQLite por defecto)
│   └── origin.py          #   BD de ORIGEN (Formap), solo lectura
├── models/                # ORM SQLAlchemy (contratista, control_nc, bitacora)
├── schemas/               # Pydantic (validación / serialización)
├── repositories/          # Acceso a datos (sin reglas de negocio)
├── services/              # Lógica de negocio (NC, contratistas, auditoría)
└── api/
    ├── deps.py            # Inyección de dependencias
    └── v1/                # Routers y endpoints versionados
```

Flujo de una petición: **endpoint → service → repository → modelo**. Cada capa
tiene una sola responsabilidad, así que crece sin enredarse.

## Puesta en marcha

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # ajustar valores

uvicorn app.main:app --reload
```

- Documentación interactiva: http://localhost:8000/docs
- Estado del servicio: http://localhost:8000/health

Datos de demostración (opcional):

```bash
python -m scripts.seed
```

## Endpoints (v1, prefijo `/api`)

| Método | Ruta                        | Descripción                          |
|--------|-----------------------------|--------------------------------------|
| GET    | `/api/nc/stats`             | Tarjetas del dashboard               |
| GET    | `/api/nc/alertas`           | NCs críticas / por vencer            |
| GET    | `/api/nc`                   | Listar NCs (filtros y paginación)    |
| GET    | `/api/nc/{id}`              | Detalle de una NC                    |
| GET/PUT| `/api/contratistas`         | Administrar contratistas y correos   |
| POST   | `/api/auditoria/ejecutar`   | Ejecutar auditoría en segundo plano  |
| GET    | `/api/auditoria/ultima`     | Última corrida (bitácora)            |

## Estado del desarrollo

- [x] Semana 1 — Estructura, configuración, modelos, BD local y de origen.
- [x] Semana 1 — Endpoints base y servicio de auditoría (sincronización + SLA).
- [ ] Semana 2 — Verificación de correo con Microsoft Graph (`_verificar_correos`).
- [ ] Semana 2 — Motor de cruce plano ↔ informe ↔ correo (llave única).
- [ ] Semana 3 — Integración con el frontend Angular.

## Configuración pendiente (depende de terceros)

- `ORIGIN_DATABASE_URL`: credenciales de solo lectura a la BD de Formap.
- Permisos `Mail.Read` de Microsoft Graph (trámite con TI).

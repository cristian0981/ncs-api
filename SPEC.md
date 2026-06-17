# SPEC — Bot de Control de No Conformidades (NC)

> Documento de especificación para agentes de IA y desarrolladores.
> Léelo completo antes de modificar el proyecto. Describe **qué hace** el
> sistema, **por qué**, **cómo está organizado**, **qué está hecho** y **qué
> falta**. Complementa a `PLAN_DE_TRABAJO.md` (cronograma por fases) y al
> `README.md` (instalación).

---

## 1. Contexto del negocio

> Fuente original de los requisitos: `docs/transcripcion-reunion-nc.md`
> (transcripción de la reunión "Procedimiento NC - Int Celsia").

Cliente: **Celsia**. Ejecutor (interventoría): **ISES**.

ISES inspecciona actividades de campo (Control de Energía, Mantenimiento, etc.).
Cuando una actividad sale **No Conforme (NC)**, ISES debe:

1. Generar un **informe de soporte** de la NC (desde el aplicativo **Formap**).
2. **Notificar al contratista** por correo, adjuntando ese informe, dentro de
   **8 días hábiles** desde la fecha de ejecución.
3. Recibir la **respuesta** del contratista.
4. **Validar** esa respuesta dentro de **5 días hábiles** y cerrar la NC.

**El problema que resuelve el bot:** hoy el proceso es manual. A veces se
registra la NC pero **no se notifica** (o no se adjunta el soporte). El tiempo
corre igual y Celsia aplica **multas** a ISES. Celsia exige un control que
garantice que toda NC registrada fue **realmente notificada** al contratista, y
que la respuesta se validó a tiempo.

**Qué hace el bot:** **audita y alerta**. Cruza lo que dice el sistema (NC
registrada) contra la evidencia real (correo enviado con su soporte) y marca lo
que falta o está por vencerse. **NO envía notificaciones a los contratistas**
(eso lo sigue haciendo el supervisor manualmente, porque requiere ajustes al
informe).

### Glosario
- **NC:** No Conformidad.
- **Formap:** aplicativo de origen donde se ejecutan/califican las actividades. BD = **SQL Server**.
- **Supervisor:** persona de ISES responsable de una o más **zonas**.
- **Zona:** región geográfica (ej. "Tolima Norte"). Viene de Formap.
- **Sector:** proceso (ej. "Control de Energía", "Mantenimiento"). Viene de Formap.
- **Tipo de actividad:** clasificación de la actividad. Viene de Formap.
- **Semáforo:** estado de plazo de una NC (VERDE / AMARILLO / ROJO).

---

## 2. Decisiones y restricciones (NO cambiar sin acordar)

- **Stack:** Python + **FastAPI**. Arquitectura por capas.
- **SIN autenticación.** No hay login ni usuarios del sistema. La tabla de
  `supervisores` es solo un catálogo propio del bot (no credenciales).
- **Supervisor → zona(s):** cada supervisor tiene asignadas una o más zonas. Su
  alcance son esas zonas; dentro de ellas filtra por sector y tipo de actividad.
- **Las listas de zona / sector / tipo de actividad provienen de Formap**, no se
  administran a mano.
- **BD de origen (Formap) = SQL Server, SOLO LECTURA.** Nunca escribir ahí. Se
  lee con un conector directo (`pyodbc`); **no usar un ORM para el origen**.
- **BD local de control** (estado del bot): por defecto SQLite en desarrollo;
  configurable a PostgreSQL vía `LOCAL_DATABASE_URL`.
- **El bot audita; no notifica a contratistas.** Cualquier envío de correo a
  contratistas está fuera de alcance. El correo de Graph es **solo lectura**
  (verificar envíos), salvo alertas internas al supervisor.
- **SLA en días hábiles:** 8 hábiles para notificar, 5 hábiles para validar,
  con festivos de Colombia. Parametrizable en configuración.

---

## 3. Arquitectura

Flujo de una petición: **endpoint → service → repository → modelo**.
Cada capa tiene una sola responsabilidad. Reglas de negocio **solo** en
`services/`. Acceso a datos **solo** en `repositories/`.

```
app/
├── main.py                     # App FastAPI, CORS, arranque (lifespan -> init_db)
├── core/
│   ├── config.py               # Settings tipadas desde .env (objeto `settings`)
│   ├── logging.py              # Configuración de logs
│   └── sla.py                  # Motor de tiempos: días hábiles, festivos CO, semáforos
├── db/
│   ├── base.py                 # Base declarativa SQLAlchemy
│   ├── session.py              # BD LOCAL de control (engine + SessionLocal + init_db)
│   └── origin.py               # BD de ORIGEN Formap (SQL Server, solo lectura, lazy)
├── models/                     # ORM SQLAlchemy
│   ├── enums.py                # EstadoNotificacion, EstadoNC, TipoCorrida
│   ├── control_nc.py           # ControlNC (entidad central)
│   ├── supervisor.py           # Supervisor, SupervisorZona
│   ├── contratista.py          # Contratista, CorreoContratista
│   └── bitacora.py             # Bitacora (registro de corridas)
├── schemas/                    # Pydantic (validación/serialización)
│   ├── nc.py                   # NCRead, NCAlerta, NCStats, FiltrosDisponibles
│   ├── supervisor.py
│   ├── contratista.py
│   └── common.py
├── repositories/               # Acceso a datos (sin reglas de negocio)
│   ├── nc_repository.py
│   ├── supervisor_repository.py
│   ├── contratista_repository.py
│   ├── bitacora_repository.py
│   └── origin_repository.py    # Lectura de Formap (SQL parametrizado)
├── services/                   # Lógica de negocio
│   ├── nc_service.py
│   ├── supervisor_service.py
│   ├── contratista_service.py
│   └── auditoria_service.py    # Orquestación: sync + SLA + (futuro) correo
└── api/
    ├── deps.py                 # Inyección de dependencias (factories de servicios)
    └── v1/
        ├── router.py           # Agrega los routers
        └── endpoints/          # nc, supervisores, contratistas, auditoria
scripts/
├── seed.py                     # Datos de demostración
└── (futuro) bot.ts/worker      # Auditoría programada (Task Scheduler)
tests/
└── test_smoke.py + conftest.py
```

---

## 4. Modelo de datos

### ControlNC (`control_nc`) — entidad central
- **Llaves de cruce** (para amarrar con informe y correo): `numero_orden_trabajo`,
  `numero_orden_interventoria`, `numero_medidor`, `numero_archivo_soporte`.
- **Dimensiones de filtro (de Formap):** `zona`, `sector`, `tipo_actividad`.
- **Datos de la NC:** `tipificacion`, `observacion`, `fecha_ejecucion`, `contratista_id`.
- **Evidencia de correo (Fase 3):** `fecha_notificacion`, `correo_verificado`,
  `correo_mensaje_id`, `soporte_adjunto_ok`.
- **Respuesta/validación:** `fecha_respuesta_contratista`, `fecha_validacion_ises`.
- **Estados derivados:** `estado_notificacion`, `estado_nc`, `semaforo`.
- Trazabilidad: `created_at`, `updated_at`.

### Supervisor (`supervisores`) + SupervisorZona (`supervisor_zonas`)
- `Supervisor`: `nombre`, `correo` (opcional), `activo`.
- `SupervisorZona`: `supervisor_id`, `zona` (string; valor de la lista de Formap).
- Relación 1‑a‑N: un supervisor tiene varias zonas (único por supervisor+zona).

### Contratista (`contratistas`) + CorreoContratista (`correos_contratista`)
- `Contratista`: `nombre` (único), `nit`, `activo`.
- `CorreoContratista`: `correo`, `nombre_contacto`, `rol`, `activo`. (Varios por
  contratista, porque el personal rota.)

### Bitacora (`bitacora`)
- `tipo` (SINCRONIZACION | AUDITORIA), `estado` (OK | ERROR), `inicio`, `fin`,
  `nc_procesadas`, `nc_nuevas`, `nc_con_alerta`, `detalle`.

### Enumeraciones
- `EstadoNotificacion`: PENDIENTE | NOTIFICADA | VENCIDA.
- `EstadoNC`: EN_CURSO | CORREGIDA | FINALIZADA | PENDIENTE_CELSIA.
- `Semaforo` (en `core/sla.py`): VERDE | AMARILLO | ROJO | SIN_DATO.

---

## 5. Reglas del motor de tiempos (`core/sla.py`)

- `es_habil(dia)`: no fin de semana ni festivo (librería `holidays`, país `CO`, por año).
- `fecha_limite_notificacion(fecha_ejecucion)` = sumar **8 días hábiles**.
- `fecha_limite_validacion(fecha_respuesta)` = sumar **5 días hábiles**.
- **Semáforo de notificación:**
  - Si ya hay `fecha_notificacion`: VERDE si fue ≤ límite, si no ROJO.
  - Si no se ha notificado: ROJO si ya pasó el límite; AMARILLO si quedan ≤ 2
    días hábiles; VERDE en otro caso.
- Los días (8 y 5) y el país de festivos son **parametrizables** vía `settings`.

---

## 6. Lógica de filtrado y alcance

- Los valores de `zona`, `sector`, `tipo_actividad` se sincronizan a cada NC desde Formap.
- `GET /api/nc/filtros` devuelve los valores disponibles (para poblar desplegables).
- En el listado de NCs:
  - `supervisor_id` → acota a **las zonas asignadas** a ese supervisor.
  - `zona`, `sector`, `tipo_actividad` → filtros adicionales.
  - La consulta a Formap (`origin_repository.fetch_nc`) acepta esos mismos filtros
    para traer solo lo relevante.

---

## 7. Endpoints (prefijo `/api`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servicio y flags de configuración |
| GET | `/api/nc/stats` | Tarjetas del dashboard (conteos por zona/sector/tipo y semáforo) |
| GET | `/api/nc/alertas` | NCs en rojo/amarillo, ordenadas por urgencia |
| GET | `/api/nc/filtros` | Valores disponibles de zona/sector/tipo de actividad |
| GET | `/api/nc` | Listar NCs. Filtros: `supervisor_id, zona, sector, tipo_actividad, estado_notificacion, semaforo, skip, limit` |
| GET | `/api/nc/{id}` | Detalle de una NC |
| GET/POST | `/api/supervisores` | Listar / crear supervisores |
| GET/PUT/DELETE | `/api/supervisores/{id}` | Obtener / editar / eliminar |
| POST | `/api/supervisores/{id}/zonas` | Asignar una zona |
| GET/POST | `/api/contratistas` | Listar / crear contratistas |
| GET/PUT/DELETE | `/api/contratistas/{id}` | Obtener / editar / eliminar |
| POST | `/api/contratistas/{id}/correos` | Agregar correo |
| POST | `/api/auditoria/ejecutar` | Ejecuta la auditoría en segundo plano (NO notifica contratistas) |
| GET | `/api/auditoria/ultima` | Última corrida |
| GET | `/api/auditoria/bitacora` | Historial de corridas |

---

## 8. Configuración (`.env`, ver `.env.example`)

- App: `APP_NAME`, `ENVIRONMENT`, `DEBUG`, `API_V1_PREFIX`, `BACKEND_CORS_ORIGINS` (texto separado por comas).
- BD local: `LOCAL_DATABASE_URL` (SQLite por defecto; PostgreSQL en producción).
- Formap: `ORIGIN_DATABASE_URL` (SQL Server, vacío hasta tener credenciales),
  `ORIGIN_NC_TABLE`, `ORIGIN_NC_CALIFICACION_VALUE`.
- SLA: `SLA_DIAS_NOTIFICACION` (8), `SLA_DIAS_VALIDACION_ISES` (5), `SLA_PAIS_FESTIVOS` (CO).
- Graph (Fase 3): `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`, `GRAPH_BOT_MAILBOX`.

---

## 9. Estado actual

**Hecho y probado (8 pruebas en verde):**
- Estructura, configuración, base local, modelos (NC, supervisores+zonas, contratistas, bitácora).
- Motor de tiempos (8 hábiles / 5 hábiles, festivos CO, semáforos).
- Endpoints de semáforo, listado/detalle, filtros, supervisores y contratistas, auditoría.
- Filtrado por zona/sector/tipo de actividad y alcance por supervisor.
- Datos de ejemplo (`scripts/seed.py`).

**Construido pero sin validar contra datos reales:** la conexión a SQL Server y
la consulta a Formap (faltan credenciales).

**Pendiente:** sincronización real filtrada (Fase 2), verificación de correo con
Microsoft Graph + motor de cruce (Fase 3), reportes y pantalla (Fase 4).
Detalle por día en `PLAN_DE_TRABAJO.md`.

---

## 10. Puntos de extensión / integraciones a confirmar

- **`repositories/origin_repository.py` → `_COLUMNAS`:** mapeo columna lógica →
  columna real de Formap. **Ajustar al confirmar el esquema real de SQL Server.**
- **`db/origin.py`:** engine de Formap (lazy). Activar con `ORIGIN_DATABASE_URL`.
  Requiere el "ODBC Driver 17/18 for SQL Server" en el sistema.
- **`services/auditoria_service.py` → `_verificar_correos`:** placeholder
  (`NotImplementedError`) para la integración con Microsoft Graph (Fase 3).
- **Motor de cruce (Fase 3):** usar la cadena de llaves
  `numero_archivo_soporte → numero_orden_interventoria → numero_orden_trabajo →
  numero_medidor` para amarrar NC ↔ informe ↔ correo. Validar con datos históricos
  y medir % de aciertos antes de construir lo demás.
- **Worker programado:** la auditoría diaria debe correr como proceso aparte
  (Task Scheduler de Windows / cron), no como petición web.

---

## 11. Pendientes externos (bloquean ciertas fases)

1. **Credenciales de solo lectura de SQL Server (Formap)** → cierra Fase 1 (Días 4–5) y habilita Fase 2.
2. **Permisos `Mail.Read` de Microsoft Graph** (trámite con TI) → Fase 3.
3. **Excel consolidado + correos de ejemplo** → spike del motor de cruce (Fase 3).

---

## 12. Cómo ejecutar y probar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload          # docs: http://localhost:8000/docs
python -m scripts.seed                 # datos de demostración
pytest -q                              # pruebas
```

---

## 13. Convenciones para agentes de IA

- **Idioma:** nombres de dominio, comentarios y mensajes en **español**.
- **No romper la separación por capas:** lógica en `services/`, acceso a datos en
  `repositories/`, validación en `schemas/`. Los endpoints son delgados.
- **No introducir autenticación** salvo que se acuerde explícitamente.
- **No escribir nunca en la BD de origen (Formap).**
- **El bot no envía correos a contratistas.** La integración con Graph es de lectura.
- **SLA y parámetros** se cambian en `core/config.py` / `.env`, no incrustados en el código.
- **Antes de dar una tarea por terminada:** correr `pytest` y, si se tocan
  fórmulas o reglas, verificar con casos límite.
- **Mantener actualizados** `PLAN_DE_TRABAJO.md` (estado de fases) y este `SPEC.md`
  cuando cambien decisiones o el modelo de datos.

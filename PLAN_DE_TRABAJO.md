# Plan de Trabajo — Bot de Control de No Conformidades (NC)

Proyecto **Celsia / ISES**. API en **Python (FastAPI)** que audita el ciclo de
vida de las No Conformidades: detecta las que no fueron notificadas al
contratista dentro del plazo, calcula los semáforos de tiempos y expone los
datos para su consulta y, más adelante, para un tablero.

> El bot **audita y alerta**; no envía notificaciones a los contratistas (eso
> sigue siendo responsabilidad del supervisor).

## Decisiones clave

- **Lenguaje:** Python con FastAPI, arquitectura por capas (endpoints → servicios → repositorios → modelos).
- **Sin autenticación:** el sistema no maneja login. Se trabaja con una tabla propia de supervisores.
- **Supervisores y zonas:** existe una tabla de supervisores y a cada uno se le asigna una o más zonas. Con su zona fijada, el supervisor filtra por sector y tipo de actividad.
- **Origen de datos (Formap):** base de datos **SQL Server**, en solo lectura. De ahí vienen las NCs y los valores de zona, sector y tipo de actividad.
- **Base local de control:** guarda el estado del bot (NCs en control, supervisores, contratistas, bitácora).
- **Plazos (SLA):** 8 días hábiles para notificar y 5 días hábiles para validar, descontando fines de semana y festivos de Colombia.

## Estado general

| Fase | Semana | Estado |
|------|--------|--------|
| Fase 1 — Cimientos, supervisores/zonas y conexión a Formap | 1 | Días 1–3 ✅ · Días 4–5 ⏳ (faltan credenciales) |
| Fase 2 — Sincronización filtrada y motor de tiempos | 2 | Pendiente (motor de tiempos ya construido) |
| Fase 3 — Verificación de correo y cruce | 3 | Pendiente |
| Fase 4 — Reportes, pantalla y cierre | 4 | Pendiente |

Leyenda: ✅ hecho · ⏳ en curso / pendiente de insumo externo.

---

## Fase 1 (Semana 1) — Cimientos, supervisores/zonas y conexión a Formap

- **Día 1 — Revisar y cerrar la base.** ✅
  Estructura del proyecto FastAPI por capas, configuración central y base local de control.
- **Día 2 — Tabla de Supervisores + zonas.** ✅
  Modelo de supervisor y asignación de una o varias zonas; creación de las tablas.
- **Día 3 — Endpoints de supervisores.** ✅
  Crear, listar, editar y asignar zona a un supervisor.
- **Día 4 — Conexión a SQL Server (Formap).** ⏳
  Driver y prueba de conexión de solo lectura. *Requiere credenciales de TI.*
- **Día 5 — Consulta base a Formap.** ⏳
  Traer actividades con calificación = NC y leer los valores de zona / sector / tipo de actividad. *Estructura lista; se valida con datos reales al tener credenciales.*

Además ya quedó funcionando: el **filtrado por zona, sector y tipo de actividad**, el **alcance por supervisor** (cada supervisor ve solo lo de sus zonas) y el endpoint de **filtros disponibles**.

## Fase 2 (Semana 2) — Sincronización filtrada y motor de tiempos

- **Día 6 — Filtros desde Formap.** Endpoint que trae de Formap las listas de zona, sector y tipo de actividad.
- **Día 7 — Sincronización filtrada.** Traer las NC de Formap acotadas por la zona del supervisor + sector + tipo de actividad y guardarlas en la base local, con registro en bitácora.
- **Día 8 — Calidad de datos.** Normalizar y marcar registros incompletos o corruptos.
- **Día 9 — Motor de tiempos (SLA).** ✅ ya construido. Integrar/afinar el cálculo (8 hábiles notificar / 5 validar, festivos CO, semáforos) recalculando en cada sincronización.
- **Día 10 — Endpoints del semáforo.** stats / alertas / listado filtrados por zona, sector y tipo de actividad.

## Fase 3 (Semana 3) — Verificación de correo y cruce

- **Día 11 — Conexión a Microsoft Graph.** Autenticación del bot. *Requiere permisos de TI.*
- **Día 12 — Búsqueda de correos.** Localizar correos enviados y adjuntos; estrategia del buzón bot en copia (CC).
- **Día 13 — Casos especiales.** Cargue a SharePoint de Celsia y caso "dicen 7 NCs pero hay 6 archivos".
- **Día 14 — Motor de cruce (llave única).** Amarrar NC ↔ informe ↔ correo, validado con datos históricos. *Requiere Excel + correos de ejemplo.*
- **Día 15 — Worker del bot.** Auditoría diaria que sincroniza, calcula tiempos y verifica correos.

## Fase 4 (Semana 4) — Reportes, pantalla y cierre

- **Día 16 — Reporte de conciliación.** Lo que pide Celsia: por cada NC, si se notificó, cuándo, con qué soporte y cuáles faltan.
- **Día 17 — Tablero.** Tarjetas de semáforo + selector de supervisor/zona y filtros de sector y tipo de actividad.
- **Día 18 — Alertas y detalle.** Tabla de NCs críticas + detalle de NC con su cruce.
- **Día 19 — Pruebas extremo a extremo.** Con datos reales/históricos.
- **Día 20 — Puesta en marcha.** Programar el bot diario (Task Scheduler) y ajustes finales.

---

## Pendientes externos (destrabar cuanto antes)

1. **Credenciales de solo lectura de SQL Server (Formap)** — para cerrar la Fase 1 (Días 4–5).
2. **Permisos de Microsoft Graph (`Mail.Read`)** — para la Fase 3; la aprobación de TI puede tardar.
3. **Un Excel consolidado + correos de ejemplo** — para el motor de cruce (Fase 3, Día 14).

## Lo que ya está construido y probado

- Estructura del proyecto y configuración.
- Modelos de datos: NC, contratistas, supervisores (con zonas) y bitácora.
- Motor de tiempos con días hábiles y festivos de Colombia.
- Servicios y endpoints: semáforo (stats / alertas), listado y detalle de NC, filtros disponibles, administración de contratistas y supervisores, ejecución de auditoría.
- Filtrado por zona, sector y tipo de actividad, con alcance por supervisor.
- Pruebas automáticas (8) en verde y datos de ejemplo para demostración.

"""Motor de tiempos (SLA).

Calcula días hábiles (excluyendo fines de semana y festivos de Colombia) y
deriva el estado del semáforo de cada NC según las reglas del contrato:

* Notificación: 8 días HÁBILES desde la fecha de ejecución.
* Validación ISES: 5 días HÁBILES desde que el contratista responde.

El cálculo de festivos usa la librería `holidays`, parametrizada por año, de
modo que sirve para 2026 y años siguientes sin tocar el código.
"""
from __future__ import annotations

from datetime import date, timedelta
from enum import Enum

import holidays

from app.core.config import settings


class Semaforo(str, Enum):
    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    ROJO = "ROJO"
    SIN_DATO = "SIN_DATO"


# Caché de calendarios de festivos por país (se construye una vez por proceso).
_holiday_calendars: dict[str, holidays.HolidayBase] = {}


def _calendario(pais: str) -> holidays.HolidayBase:
    if pais not in _holiday_calendars:
        # years=[] => se expande dinámicamente al consultar cualquier fecha.
        _holiday_calendars[pais] = holidays.country_holidays(pais)
    return _holiday_calendars[pais]


def es_habil(dia: date, pais: str | None = None) -> bool:
    """True si `dia` es día hábil (no fin de semana ni festivo)."""
    pais = pais or settings.SLA_PAIS_FESTIVOS
    if dia.weekday() >= 5:  # 5=sábado, 6=domingo
        return False
    return dia not in _calendario(pais)


def sumar_dias_habiles(inicio: date, dias: int, pais: str | None = None) -> date:
    """Devuelve la fecha resultante de sumar `dias` hábiles a `inicio`."""
    resultado = inicio
    restantes = dias
    while restantes > 0:
        resultado += timedelta(days=1)
        if es_habil(resultado, pais):
            restantes -= 1
    return resultado


def dias_habiles_entre(inicio: date, fin: date, pais: str | None = None) -> int:
    """Cuenta los días hábiles entre `inicio` y `fin` (sin incluir `inicio`)."""
    if fin <= inicio:
        return 0
    dias = 0
    cursor = inicio
    while cursor < fin:
        cursor += timedelta(days=1)
        if es_habil(cursor, pais):
            dias += 1
    return dias


def fecha_limite_notificacion(fecha_ejecucion: date) -> date:
    """Fecha tope para notificar la NC (días hábiles)."""
    return sumar_dias_habiles(fecha_ejecucion, settings.SLA_DIAS_NOTIFICACION)


def fecha_limite_validacion(fecha_respuesta: date) -> date:
    """Fecha tope para que ISES valide la respuesta (días hábiles)."""
    return sumar_dias_habiles(fecha_respuesta, settings.SLA_DIAS_VALIDACION_ISES)


def semaforo_notificacion(
    fecha_ejecucion: date | None,
    fecha_notificacion: date | None,
    hoy: date | None = None,
) -> Semaforo:
    """Semáforo del plazo de NOTIFICACIÓN (8 días hábiles).

    * VERDE   : notificada dentro del plazo, o aún quedan >2 días hábiles.
    * AMARILLO: sin notificar, quedan 2 días hábiles o menos.
    * ROJO    : sin notificar y el plazo ya venció.
    """
    if fecha_ejecucion is None:
        return Semaforo.SIN_DATO

    hoy = hoy or date.today()
    limite = fecha_limite_notificacion(fecha_ejecucion)

    if fecha_notificacion is not None:
        return Semaforo.VERDE if fecha_notificacion <= limite else Semaforo.ROJO

    if hoy > limite:
        return Semaforo.ROJO
    return Semaforo.AMARILLO if dias_habiles_entre(hoy, limite) <= 2 else Semaforo.VERDE


def semaforo_validacion(
    fecha_respuesta: date | None,
    fecha_validacion: date | None,
    hoy: date | None = None,
) -> Semaforo:
    """Semáforo del plazo de VALIDACIÓN ISES (5 días hábiles)."""
    if fecha_respuesta is None:
        return Semaforo.SIN_DATO

    hoy = hoy or date.today()
    limite = fecha_limite_validacion(fecha_respuesta)

    if fecha_validacion is not None:
        return Semaforo.VERDE if fecha_validacion <= limite else Semaforo.ROJO

    if hoy > limite:
        return Semaforo.ROJO
    return Semaforo.AMARILLO if dias_habiles_entre(hoy, limite) <= 1 else Semaforo.VERDE

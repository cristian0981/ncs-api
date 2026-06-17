"""Enumeraciones del dominio de No Conformidades."""
from __future__ import annotations

from enum import Enum


class EstadoNotificacion(str, Enum):
    """Estado de la notificacion de la NC al contratista."""

    PENDIENTE = "PENDIENTE"      # registrada, aun sin notificar
    NOTIFICADA = "NOTIFICADA"    # correo verificado por el bot
    VENCIDA = "VENCIDA"          # paso el plazo sin notificar


class EstadoNC(str, Enum):
    """Ciclo de vida de la NC (segun respuesta del contratista y validacion)."""

    EN_CURSO = "EN_CURSO"
    CORREGIDA = "CORREGIDA"
    FINALIZADA = "FINALIZADA"
    PENDIENTE_CELSIA = "PENDIENTE_CELSIA"


class TipoCorrida(str, Enum):
    """Tipo de corrida registrada en la bitacora."""

    SINCRONIZACION = "SINCRONIZACION"
    AUDITORIA = "AUDITORIA"

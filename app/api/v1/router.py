"""Router agregador de la version 1 de la API."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import auditoria, contratistas, nc, supervisores

api_router = APIRouter()
api_router.include_router(nc.router)
api_router.include_router(supervisores.router)
api_router.include_router(contratistas.router)
api_router.include_router(auditoria.router)

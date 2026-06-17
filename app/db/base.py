"""Clase base declarativa de SQLAlchemy.

Todos los modelos ORM heredan de `Base`. Importar los modelos en
`app.db.base_models` para que `Base.metadata.create_all()` los registre.
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

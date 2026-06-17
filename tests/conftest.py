"""Configuración de pruebas: BD aislada y tablas creadas antes de los tests."""
from __future__ import annotations

import os
import tempfile

# Debe definirse ANTES de importar la app (settings se lee al importar).
_TEST_DB = os.path.join(tempfile.gettempdir(), "ncs_test_control.db")
os.environ["LOCAL_DATABASE_URL"] = f"sqlite:///{_TEST_DB}"

from app.db.base import Base  # noqa: E402
from app.db.session import engine, init_db  # noqa: E402
import app.models  # noqa: E402,F401  (registra los modelos)

# Estado limpio en cada corrida.
Base.metadata.drop_all(bind=engine)
init_db()

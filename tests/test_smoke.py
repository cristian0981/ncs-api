"""Pruebas de humo: la app arranca y los endpoints base responden."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.core import sla
from app.core.sla import Semaforo
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_stats_responde():
    r = client.get("/api/nc/stats")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "por_zona" in body and "por_sector" in body and "por_tipo_actividad" in body


def test_filtros_responde():
    r = client.get("/api/nc/filtros")
    assert r.status_code == 200
    body = r.json()
    assert set(["zonas", "sectores", "tipos_actividad"]).issubset(body.keys())


def test_alertas_responde():
    r = client.get("/api/nc/alertas")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_crear_contratista():
    payload = {"nombre": "Contratista Test", "correos": [{"correo": "a@b.com"}]}
    r = client.post("/api/contratistas", json=payload)
    assert r.status_code == 201
    assert r.json()["nombre"] == "Contratista Test"


def test_crear_supervisor_con_zona():
    payload = {"nombre": "Super Test", "correo": "s@b.com", "zonas": ["Tolima Norte"]}
    r = client.post("/api/supervisores", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["nombre"] == "Super Test"
    assert body["zonas"] == ["Tolima Norte"]

    # Asignar otra zona
    sid = body["id"]
    r2 = client.post(f"/api/supervisores/{sid}/zonas", json={"zona": "Valle"})
    assert r2.status_code == 200
    assert sorted(r2.json()["zonas"]) == ["Tolima Norte", "Valle"]


def test_semaforo_notificacion_vencida():
    ejec = date.today() - timedelta(days=20)
    assert sla.semaforo_notificacion(ejec, None) == Semaforo.ROJO


def test_semaforo_notificacion_a_tiempo():
    ejec = date.today() - timedelta(days=2)
    notif = date.today() - timedelta(days=1)
    assert sla.semaforo_notificacion(ejec, notif) == Semaforo.VERDE

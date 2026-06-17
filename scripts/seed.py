"""Carga datos de demostracion para probar la API sin la BD de origen.

Uso:  python -m scripts.seed
"""
from __future__ import annotations

from datetime import date, timedelta

from app.db.session import SessionLocal, init_db
from app.models.contratista import Contratista, CorreoContratista
from app.models.control_nc import ControlNC
from app.models.supervisor import Supervisor, SupervisorZona
from app.services.auditoria_service import AuditoriaService

ZONA_TOLIMA = "Tolima Norte"
ZONA_VALLE = "Valle"
SECTOR_CE = "Control de Energia"
SECTOR_MTO = "Mantenimiento"


def run() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.query(Contratista).count() > 0:
            print("Ya hay datos; no se vuelve a sembrar.")
            return

        # --- Contratistas ---
        oca = Contratista(
            nombre="OCA Global",
            correos=[CorreoContratista(correo="contacto@oca.example", rol="Lectura")],
        )
        proin = Contratista(
            nombre="PROIN",
            correos=[CorreoContratista(correo="ordenes@proin.example", rol="Ordenes")],
        )
        db.add_all([oca, proin])

        # --- Supervisores con su zona asignada ---
        sup_tolima = Supervisor(
            nombre="Andres Gil",
            correo="agil@ises.com.co",
            zonas=[SupervisorZona(zona=ZONA_TOLIMA)],
        )
        sup_valle = Supervisor(
            nombre="Walter Estrada",
            correo="westrada@ises.com.co",
            zonas=[SupervisorZona(zona=ZONA_VALLE)],
        )
        db.add_all([sup_tolima, sup_valle])
        db.flush()

        hoy = date.today()
        ncs = [
            ControlNC(
                numero_orden_interventoria="INT-1001",
                numero_orden_trabajo="OT-5001",
                zona=ZONA_TOLIMA, sector=SECTOR_CE, tipo_actividad="Revision medidor",
                tipificacion="Sin codigo de colores",
                fecha_ejecucion=hoy - timedelta(days=20),
                contratista_id=oca.id,
            ),
            ControlNC(
                numero_orden_interventoria="INT-1002",
                numero_orden_trabajo="OT-5002",
                zona=ZONA_TOLIMA, sector=SECTOR_MTO, tipo_actividad="Poda",
                tipificacion="Fase empalmada expuesta",
                fecha_ejecucion=hoy - timedelta(days=10),
                contratista_id=proin.id,
            ),
            ControlNC(
                numero_orden_interventoria="INT-1003",
                numero_orden_trabajo="OT-5003",
                zona=ZONA_VALLE, sector=SECTOR_CE, tipo_actividad="Revision medidor",
                tipificacion="Falta dispositivo de seguridad",
                fecha_ejecucion=hoy - timedelta(days=1),
                contratista_id=oca.id,
            ),
            ControlNC(
                numero_orden_interventoria="INT-1004",
                numero_orden_trabajo="OT-5004",
                zona=ZONA_VALLE, sector=SECTOR_MTO, tipo_actividad="Inspeccion linea",
                tipificacion="Sello de seguridad",
                fecha_ejecucion=hoy - timedelta(days=5),
                fecha_notificacion=hoy - timedelta(days=4),
                correo_verificado=True, soporte_adjunto_ok=True,
                contratista_id=proin.id,
            ),
        ]
        db.add_all(ncs)
        db.commit()
        print(f"Sembrados 2 contratistas, 2 supervisores y {len(ncs)} NCs.")
    finally:
        db.close()

    # Recalcula semaforos/estados con el servicio de auditoria.
    db = SessionLocal()
    try:
        registro = AuditoriaService(db).ejecutar()
        print(f"Auditoria: {registro.detalle}")
    finally:
        db.close()


if __name__ == "__main__":
    run()

"""Logica de negocio de Supervisores."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.supervisor import Supervisor, SupervisorZona
from app.repositories.supervisor_repository import SupervisorRepository
from app.schemas.supervisor import SupervisorCreate, SupervisorRead, SupervisorUpdate


class SupervisorService:
    def __init__(self, db: Session) -> None:
        self.repo = SupervisorRepository(db)

    @staticmethod
    def _to_read(sup: Supervisor) -> SupervisorRead:
        return SupervisorRead(
            id=sup.id,
            nombre=sup.nombre,
            correo=sup.correo,
            activo=sup.activo,
            zonas=sorted(z.zona for z in sup.zonas),
        )

    def get(self, supervisor_id: int) -> SupervisorRead | None:
        sup = self.repo.get(supervisor_id)
        return self._to_read(sup) if sup else None

    def list(self, *, solo_activos: bool = False) -> list[SupervisorRead]:
        return [self._to_read(s) for s in self.repo.list(solo_activos=solo_activos)]

    def crear(self, data: SupervisorCreate) -> SupervisorRead:
        sup = Supervisor(nombre=data.nombre, correo=data.correo, activo=data.activo)
        for zona in dict.fromkeys(data.zonas):  # sin duplicados, conserva orden
            sup.zonas.append(SupervisorZona(zona=zona))
        self.repo.add(sup)
        self.repo.commit()
        return self._to_read(sup)

    def actualizar(
        self, supervisor_id: int, data: SupervisorUpdate
    ) -> SupervisorRead | None:
        sup = self.repo.get(supervisor_id)
        if sup is None:
            return None
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(sup, campo, valor)
        self.repo.commit()
        return self._to_read(sup)

    def asignar_zona(self, supervisor_id: int, zona: str) -> SupervisorRead | None:
        sup = self.repo.get(supervisor_id)
        if sup is None:
            return None
        # Se agrega a la coleccion ya cargada para que el objeto en memoria
        # quede actualizado (expire_on_commit=False no refresca relaciones).
        if all(z.zona != zona for z in sup.zonas):
            sup.zonas.append(SupervisorZona(zona=zona))
            self.repo.commit()
        return self._to_read(sup)

    def eliminar(self, supervisor_id: int) -> bool:
        sup = self.repo.get(supervisor_id)
        if sup is None:
            return False
        self.repo.delete(sup)
        self.repo.commit()
        return True

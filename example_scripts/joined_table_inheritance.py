from __future__ import annotations
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employee"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    type: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": "employee",
        "polymorphic_on": "type",
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r})"


class Engineer(Employee):
    __tablename__ = "engineer"
    id: Mapped[int] = mapped_column(ForeignKey("employee.id"), primary_key=True)
    engineer_name: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": "engineer",
    }


class Manager(Employee):
    __tablename__ = "manager"
    id: Mapped[int] = mapped_column(ForeignKey("employee.id"), primary_key=True)
    manager_name: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": "manager",
    }

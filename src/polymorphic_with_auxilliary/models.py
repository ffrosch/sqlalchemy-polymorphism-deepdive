from __future__ import annotations

from types import SimpleNamespace
from typing import Literal, Optional, get_args

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    and_,
    func,
    select,
)
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase,
    KeyFuncDict,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.orm.collections import attribute_keyed_dict


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class Report(Base):
    __tablename__ = "report"

    id: Mapped[int] = mapped_column(primary_key=True)
    species: Mapped[str]

    participants: Mapped[list[ReportParticipant]] = relationship(
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, species={self.species!r})"


class ReportParticipant(Base):
    # ! IMPORTANT:
    # ! - participants can only be mapped to one Report
    # ! - registered participants (users) use a "dummy" ID for each report
    # ! - unregistered participants are created on a per-report-basis
    # ! - a participant must have at least one role (separate table)
    __tablename__ = "report_participant"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey(Report.id))
    has_account: Mapped[bool] = mapped_column(nullable=False)

    __mapper_args__ = {
        "polymorphic_on": has_account,
    }

    report: Mapped[Report] = relationship(
        back_populates="participants",
        uselist=False,  # one-to-one relation (one report per participant)
    )
    _roles: Mapped[list[ReportParticipantRole]] = relationship(
        cascade="all, delete-orphan",
        back_populates="participant",
    )
    roles: AssociationProxy[list[Role]] = association_proxy(
        "_roles",
        "role",
        creator=lambda role: ReportParticipantRole(role=role),
    )

    def __init__(self, roles, **kwargs):
        if not roles:
            raise ValueError("At least one role must be provided.")
        self.roles = roles
        super().__init__(**kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}(report_id={self.report_id})"


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    @classmethod
    def initial_data(self):
        roles = ["creator", "reporter", "observer"]
        return roles

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"


class ReportParticipantRole(Base):
    __tablename__ = "report_participant_role"
    __table_args__ = (
        # ! IMPORTANT:
        # ! this COMPOSITE FK guarantees enforcement of the constraint
        # ! "one report per participant", because the participant_id can only be
        # ! used in combination with the report_id it belongs to!
        ForeignKeyConstraint(
            ["report_id", "participant_id"],
            [ReportParticipant.report_id, ReportParticipant.id],
            name="fk_report_participant_role_report_participant",
        ),
        # ! Each report can have each role only once
        UniqueConstraint(
            "role_id", "report_id", name="uq_report_report_participant_role"
        ),
    )

    role_id: Mapped[int] = mapped_column(ForeignKey(Role.id), primary_key=True)
    report_id: Mapped[int] = mapped_column(primary_key=True)  # Composite FK
    participant_id: Mapped[int] = mapped_column()  # Composite FK

    role: Mapped[Role] = relationship(uselist=False)
    participant: Mapped[ReportParticipant] = relationship(uselist=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(report_id={self.report_id!r}, role={self.role!r})"


class ReportParticipantUnregistered(ReportParticipant):
    __tablename__ = "report_participant_unregistered"
    __mapper_args__ = {
        "polymorphic_identity": False,
        "polymorphic_load": "inline",
    }

    id: Mapped[int] = mapped_column(ForeignKey(ReportParticipant.id), primary_key=True)
    name: Mapped[str]

    def __repr__(self) -> str:
        parent_repr = super().__repr__()
        return f"{parent_repr[:-1]}, name={self.name!r})"


class ReportParticipantRegistered(ReportParticipant):
    __tablename__ = "report_participant_registered"
    __mapper_args__ = {
        "polymorphic_identity": True,
        "polymorphic_load": "inline",
    }

    id: Mapped[int] = mapped_column(ForeignKey(ReportParticipant.id), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id), nullable=False)
    user: Mapped[User] = relationship(lazy="selectin")

    @property
    def name(self):
        return self.user.name

    def __repr__(self) -> str:
        parent_repr = super().__repr__()
        return f"{parent_repr[:-1]}, user_id={self.user_id}, name={self.name!r})"

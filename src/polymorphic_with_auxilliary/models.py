from __future__ import annotations

from types import SimpleNamespace
from typing import Optional

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


class Report(Base):
    __tablename__ = "report"

    id: Mapped[int] = mapped_column(primary_key=True)
    species: Mapped[str]

    participant_associations: Mapped[list[ReportParticipantAssociation]] = relationship()

    participants: AssociationProxy[list[ReportParticipantAssociation]] = association_proxy(
        "participant_associations",
        "participant",
        creator=lambda obj: ReportParticipantAssociation(**obj),
    )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, species={self.species!r})"


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


_ROLES: list[str] = ["creator", "reporter", "observer"]


class ReportRole(Base):
    __tablename__ = "report_role"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


_DISCRIMINATOR = SimpleNamespace(unregistered="unregistered", registered="registered")


class ReportParticipant(Base):
    __tablename__ = "report_participant"

    discriminator: Mapped[str] = mapped_column(String(12))

    __mapper_args__ = {
        "polymorphic_on": discriminator,
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    report_association: Mapped[ReportParticipantAssociation] = relationship()
    roles: AssociationProxy[ReportParticipantAssociation] = association_proxy(
        "report_association",
        "roles",
    )


class ReportParticipantAssociation(Base):
    __tablename__ = "report_participant_association"
    __table_args__ = (
        # ! IMPORTANT:
        # ! - participants can only be mapped to one Report
        # ! - registered participants (users) use a "dummy" ID for each report
        # ! - unregistered participants are created on a per-report-basis
        UniqueConstraint("participant_id"),
    )

    report_id: Mapped[int] = mapped_column(ForeignKey(Report.id), primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey(ReportParticipant.id), primary_key=True)

    participant: Mapped[ReportParticipant] = relationship(
        back_populates="report_association",
    )

    role_associations: Mapped[list[ReportParticipantRoleAssociation]] = relationship()
    roles: AssociationProxy[list[ReportParticipantRoleAssociation]] = association_proxy(
        "role_associations",
        "role",
        creator=lambda role: ReportParticipantRoleAssociation(role=ReportRole(name=role)),
    )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.report_id!r}, {self.participant_id!r})"


class ReportParticipantRoleAssociation(Base):
    __tablename__ = "report_participant_role_association"
    __table_args__ = (
        # ! IMPORTANT:
        # ! this COMPOSITE FK guarantees enforcement of the constraint
        # ! "one report per participant", because the participant_id can only be
        # ! used in combination with the report_id it belongs to!
        ForeignKeyConstraint(
            ["report_id", "participant_id"],
            [
                ReportParticipantAssociation.report_id,
                ReportParticipantAssociation.participant_id,
            ],
        ),
        UniqueConstraint("role_id", "report_id")
    )

    role_id: Mapped[int] = mapped_column(ForeignKey(ReportRole.id), primary_key=True)
    report_id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column()

    role: Mapped[ReportRole] = relationship()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(report_id={self.report_id!r}, role={self.role_id!r})"


class ReportParticipantUnregistered(ReportParticipant):
    __tablename__ = "report_participant_unregistered"

    __mapper_args__ = {
        "polymorphic_identity": _DISCRIMINATOR.unregistered,
        "polymorphic_load": "inline",
    }

    id: Mapped[int] = mapped_column(ForeignKey(ReportParticipant.id), primary_key=True)

    name: Mapped[str]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class ReportParticipantRegistered(ReportParticipant):
    __tablename__ = "report_participant_registered"

    __mapper_args__ = {
        "polymorphic_identity": _DISCRIMINATOR.registered,
        "polymorphic_load": "inline",
    }

    id: Mapped[int] = mapped_column(ForeignKey(ReportParticipant.id), primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id), nullable=False)
    user: Mapped[User] = relationship(lazy="selectin")

    @property
    def name(self):
        return self.user.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(user={self.user!r})"

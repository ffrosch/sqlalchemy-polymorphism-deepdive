from __future__ import annotations

import enum
from types import SimpleNamespace

from sqlalchemy import (
    CheckConstraint,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    and_,
    create_engine,
    func,
    select,
)
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import (
    KeyFuncDict,
    Mapped,
    declarative_base,
    mapped_column,
    relationship,
    DeclarativeBase,
)
from sqlalchemy.orm.collections import attribute_keyed_dict


class Base(DeclarativeBase):
    pass


class Report(Base):
    __tablename__ = "report"

    id: Mapped[int] = mapped_column(primary_key=True)
    species: Mapped[str]

    # KeyFuncDict was formerly (in 1.4) `MappedCollection`
    association: Mapped[KeyFuncDict[str, ReportParticipantAssociation]] = relationship(
        back_populates="report",
        collection_class=attribute_keyed_dict(
            "role"
        ),  # formely (in 1.4) `attribute_mapped_collection`
        cascade="all, delete-orphan",
    )

    participants: AssociationProxy[KeyFuncDict[str, ReportParticipant]] = (
        association_proxy(
            "association",
            "participant",
            creator=lambda k, v: ReportParticipantAssociation(role=k, participant=v),
        )
    )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, species={self.species!r})"


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, name={self.name!r})"


class ReportParticipant(Base):
    __tablename__ = "report_participant"

    id: Mapped[int] = mapped_column(primary_key=True)
    _discriminator = SimpleNamespace(
        unregistered="unregistered", registered="registered"
    )
    discriminator: Mapped[str] = mapped_column(String(12))

    __mapper_args__ = {
        "polymorphic_on": discriminator,
    }

    association: Mapped[list[ReportParticipantAssociation]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )

    reports: AssociationProxy[list[Report]] = association_proxy(
        "association",
        "report",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if (
            self.discriminator is not None
            and self.discriminator
            not in self._discriminator.__dict__.values()
        ):
            raise ValueError(f"Invalid discriminator value: {self.discriminator!r}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, discriminator={self.discriminator!r})"


class ReportParticipantUnregistered(ReportParticipant):
    __tablename__ = "report_participant_unregistered"
    id: Mapped[int] = mapped_column(ForeignKey(ReportParticipant.id), primary_key=True)
    name: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": ReportParticipant._discriminator.unregistered,
        "polymorphic_load": "inline",
    }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, email={self.name!r})"


class ReportParticipantRegistered(ReportParticipant):
    """
    A user can be registered as ReportParticipant only once.
    This is enforced by `single_parent=True` on the `user` relationship and by
    the constraint `unique=True` on the `user_id` column.
    """

    __tablename__ = "report_participant_registered"
    id: Mapped[int] = mapped_column(ForeignKey(ReportParticipant.id), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id), unique=True)
    user: Mapped[User] = relationship(
        single_parent=True,
        uselist=False,
        lazy="selectin",
    )

    __mapper_args__ = {
        "polymorphic_identity": ReportParticipant._discriminator.registered,
        "polymorphic_load": "inline",
    }

    @property
    def name(self):
        return self.user.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, name={self.name!r})"


class ReportParticipantAssociation(Base):
    __tablename__ = "report_participant_association"

    _roles: list[str] = ["creator", "reporter", "observer"]

    # Composite Primary Key, each report can have each role only once
    report_id: Mapped[int] = mapped_column(ForeignKey(Report.id), primary_key=True)
    role: Mapped[str] = mapped_column(primary_key=True)

    __table_args__ = (
        CheckConstraint(
            role.in_(_roles),
            name="ck_report_participant_association_valid_role",
        ),
    )

    participant_id: Mapped[int] = mapped_column(ForeignKey(ReportParticipant.id))

    participant: Mapped[ReportParticipant] = relationship(lazy="joined", innerjoin=True)
    report: Mapped[Report] = relationship(
        back_populates="association", lazy="joined", innerjoin=True
    )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(report_id={self.report_id!r}, participant_id={self.participant_id!r})"

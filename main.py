from __future__ import annotations

import os
from types import SimpleNamespace

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    StaticPool,
    String,
    create_engine,
    func,
    join,
    or_,
    select,
    union,
)
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    Mapped,
    as_declarative,
    backref,
    column_property,
    declarative_base,
    joinedload,
    mapped_column,
    relationship,
    remote,
    selectinload,
    sessionmaker,
    subqueryload,
)

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.name}, {self.email})"


class Report(Base):
    __tablename__ = "report"

    id: Mapped[int] = mapped_column(primary_key=True)
    species: Mapped[str] = mapped_column(String)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.species})"

    report_participant_associations: Mapped[list[ReportParticipants]] = relationship(
        back_populates="report",
        # Use `selectin` to avoid the N+1 problem
        # According to the docs `selectin` is usually the best eager-loading choice
        lazy="selectin",
        viewonly=True,
    )

    participants: AssociationProxy[list[Participant]] = association_proxy(
        "report_participant_associations",
        "participant",
    )

    @property
    def participants_count(self):
        return len(self.participants)


class Participant(Base):
    __tablename__ = "participant"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String)

    __mapper_args__ = {
        "polymorphic_on": type,
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.name}, {self.email})"

    # reports_relation: Mapped[list[Report]] = relationship(
    #     primaryjoin=lambda: Participant.id == ReportParticipants.participant_id,
    #     secondaryjoin=lambda: ReportParticipants.report_id == Report.id,
    #     secondary="report_participants",
    #     viewonly=True,
    # )

    participant_report_associations: Mapped[list[ReportParticipants]] = relationship(
        back_populates="participant",
        lazy="selectin",
        viewonly=True,
    )

    reports: AssociationProxy[list[Report]] = association_proxy(
        "participant_report_associations",
        "report",
    )

    @property
    def reports_count(self):
        return len(self.reports)


class UnregisteredParticipant(Participant):
    __tablename__ = "unregistered_participant"
    __mapper_args__ = {
        "polymorphic_identity": "unregistered",
        "polymorphic_load": "inline",
    }

    id: Mapped[int] = mapped_column(ForeignKey(Participant.id), primary_key=True)

    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)


class RegisteredParticipant(Participant):
    __tablename__ = "registered_participant"
    __mapper_args__ = {
        "polymorphic_identity": "registered",
        "polymorphic_load": "inline",
    }

    id: Mapped[int] = mapped_column(ForeignKey(Participant.id), primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey(User.id), unique=True, nullable=True
    )
    user: Mapped[User] = relationship(
        single_parent=True,
        uselist=False,
        lazy="selectin",
    )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.user})"

    @property
    def name(self):
        return self.user.name

    @property
    def email(self):
        return self.user.email


class ReportParticipants(Base):
    __tablename__ = "report_participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String)

    role: Mapped[str] = mapped_column(String)

    __mapper_args__ = {"polymorphic_on": type}

    report_id = Column(Integer, ForeignKey(Report.id))
    report = relationship(
        Report,
        back_populates="report_participant_associations",
        lazy="selectin",
    )

    participant_id = Column(Integer, ForeignKey(Participant.id))
    participant = relationship(
        Participant,
        back_populates="participant_report_associations",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.id}, {self.report.species}, {self.role})"
        )


class ReportParticipantsUnregistered(ReportParticipants):
    __tablename__ = "report_participants_unregistered"
    __mapper_args__ = {
        "polymorphic_identity": "unregistered",
        "polymorphic_load": "inline",
    }

    id: Mapped[int] = mapped_column(ForeignKey(ReportParticipants.id), primary_key=True)


class ReportParticipantsRegistered(ReportParticipants):
    __tablename__ = "report_participants_registered"
    __mapper_args__ = {
        "polymorphic_identity": "registered",
        "polymorphic_load": "inline",
    }

    id: Mapped[int] = mapped_column(ForeignKey(ReportParticipants.id), primary_key=True)


def new_engine(db=":memory:", echo=False):
    if db != ":memory:":
        if os.path.exists(db) and os.path.isfile(db):
            os.remove(db)
    return create_engine(
        f"sqlite:///{db}",
        echo=echo,
        poolclass=StaticPool,  # use the same connection to keep an ':memory:' database
    )


DB = {
    "memory": ":memory:",
    "file": "database.db",
}
DB = SimpleNamespace(**DB)

engine = new_engine(DB.memory, echo=True)
Base.metadata.create_all(engine)

_Session = sessionmaker(bind=engine)


def Session():
    engine.echo = False
    return _Session()


def EchoSession():
    engine.echo = True
    return _Session()


with EchoSession() as session:
    print()
    print("---------------------------------- BEGIN Queries")
    session.query(User).all()


with Session() as session:
    print()
    print("---------------------------------- BEGIN Insert Data")
    users = [
        User(name="John Doe", email="john@doe.com"),
        User(name="Jane Doe", email="jane@doe.com"),
    ]
    registered_participants = [
        RegisteredParticipant(user_id=1),
        RegisteredParticipant(user_id=2),
    ]
    unregistered_participants = [
        UnregisteredParticipant(name="Max Mustermann", email="max@mustermann.com"),
        UnregisteredParticipant(
            name="Marlene Mustermann", email="marlene@mustermann.com"
        ),
    ]
    reports = [
        Report(species="Capercaillie"),
        Report(species="Blue Tit"),
        Report(species="Red Panda"),
    ]
    report_participants = [
        ReportParticipantsRegistered(report_id=1, participant_id=1, role="observer"),
        ReportParticipantsRegistered(report_id=1, participant_id=2, role="reporter"),
        ReportParticipantsUnregistered(report_id=2, participant_id=3, role="reporter"),
        ReportParticipantsUnregistered(report_id=2, participant_id=4, role="observer"),
        ReportParticipantsRegistered(report_id=3, participant_id=1, role="observer"),
    ]

    session.add_all(users)
    session.add_all(registered_participants)
    session.add_all(unregistered_participants)
    session.add_all(reports)
    session.add_all(report_participants)
    session.commit()

    participants = session.query(Participant).all()

    print("#  Users:".ljust(30), users)
    print("#  Registered Participants:".ljust(30), registered_participants)
    print("#  Unregistered Participants:".ljust(30), unregistered_participants)
    print("#  Participants:".ljust(30), participants)
    print("#  Reports:".ljust(30), reports)
    print("#  Report Participants:".ljust(30), report_participants)
    print(
        "#  Report Participants:".ljust(30),
        reports[0].participants_count,
        reports[0].participants,
    )
    print(
        "#  Reports per User:".ljust(30),
        [p.reports_count for p in session.query(Participant)],
    )
    print(
        "#  Reports AssociationProxy:".ljust(30),
        session.query(Participant).first().reports,
    )


with EchoSession() as session:
    """This is important to test to avoid N+1 queries"""

    # Due to eager-loading on the relations and polymorphic associations
    # no N+1 queries are executed

    # Empty the terminal output
    # os.system("clear")

    print("---------------------------------- TEST Report AssociationProxy")

    reports = session.scalars(select(Report)).all()
    print([r.participants for r in reports])

    print()
    print("---------------------------------- TEST Participant AssociationProxy")

    participants = session.scalars(select(Participant)).all()
    print([p.reports for p in participants])

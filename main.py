from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    StaticPool,
    String,
    and_,
    create_engine,
    func,
    join,
    or_,
    select,
    union,
    exists,
    UniqueConstraint,
)
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
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
        # viewonly=True,
    )

    participants: AssociationProxy[list[Participant]] = association_proxy(
        "report_participant_associations",
        "participant",
    )

    @property
    def existing_roles(self):
        participants = self.report_participant_associations
        return [p.role for p in participants]

    @classmethod
    def role_exists(cls, report_id: int, role: str):
        return (
            session.scalars(
                select(ReportParticipants.role).where(
                    and_(
                        ReportParticipants.report_id == report_id,
                        ReportParticipants.role == role,
                    )
                )
            ).one_or_none()
            == role
        )

    @hybrid_property
    def count_participants(self):
        return len(self.participants)

    @count_participants.expression
    def count_participants(cls):
        return (
            select(func.count(ReportParticipants.id))
            .where(ReportParticipants.report_id == cls.id)
            .scalar_subquery()
        )


class Participant(Base):
    __tablename__ = "participant"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String, index=True)

    __mapper_args__ = {
        "polymorphic_on": type,
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.type})"

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

    @hybrid_property
    def count_reports(self):
        return len(self.reports)

    @count_reports.expression
    def count_reports(cls):
        return (
            select(func.count(ReportParticipants.id))
            .where(ReportParticipants.participant_id == cls.id)
            .scalar_subquery()
        )


class UnregisteredParticipant(Participant):
    __tablename__ = "unregistered_participant"
    __mapper_args__ = {
        "polymorphic_identity": "unregistered",
        "polymorphic_load": "inline",
    }

    id: Mapped[int] = mapped_column(ForeignKey(Participant.id), primary_key=True)

    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.name}, {self.email})"


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
    type: Mapped[str] = mapped_column(String, index=True)
    __mapper_args__ = {"polymorphic_on": type}

    role: Mapped[str] = mapped_column(String)

    __table_args__ = (
        CheckConstraint(
            role.in_(["creator", "reporter", "observer"]),
            name="ck_report_participants_valid_role",
        ),
        UniqueConstraint(
            "report_id", "role", name="uq_report_participants_report_role"
        ),
    )

    report_id: Mapped[int] = mapped_column(Integer, ForeignKey(Report.id))
    report: Mapped[Report] = relationship(
        back_populates="report_participant_associations",
        lazy="selectin",
    )

    participant_id = Column(Integer, ForeignKey(Participant.id))
    participant: Mapped[Participant] = relationship(
        back_populates="participant_report_associations",
        lazy="selectin",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.role not in ("creator", "reporter", "observer"):
            raise ValueError(f"Invalid role: {self.role}")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.report_id},  {self.role})"


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
    participants_with_multiple_reports = (
        session.query(Participant).where(Participant.count_reports > 1).all()
    )

    print("#  Users:".ljust(30), users)
    print("#  Registered Participants:".ljust(30), registered_participants)
    print("#  Unregistered Participants:".ljust(30), unregistered_participants)
    print("#  Participants:".ljust(30), participants)
    print("#  Reports:".ljust(30), reports)
    print("#  Report Participants:".ljust(30), report_participants)
    print(
        "#  Report Participants:".ljust(30),
        reports[0].count_participants,
        reports[0].participants,
    )
    print(
        "#  Reports per User:".ljust(30),
        [p.count_reports for p in session.query(Participant)],
    )

    print(
        "#  Participants with more than 1 report:".ljust(30),
        participants_with_multiple_reports,
    )
    print(
        "#  Reports AssociationProxy:".ljust(30),
        session.query(Participant).first().reports,
    )


with Session() as session:
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


with Session() as session:
    print()
    print("---------------------------------- TEST CHECK CONSTRAINTS")

    role = "observer"
    report = Report(species="Capercaillie")

    session.add(report)
    session.commit()

    participant1 = ReportParticipantsUnregistered(
        report=report,
        participant=UnregisteredParticipant(name="Test Role", email="test@role.org"),
        role=role,
    )

    session.add(participant1)
    session.commit()

    participant2 = ReportParticipantsUnregistered(
        report=report,
        participant=UnregisteredParticipant(name="Test Role", email="test@role.org"),
        role=role,
    )
    print(
        f"ROLE '{role}' ALREADY EXISTS on report {report.id}"
        if Report.role_exists(report.id, role)
        else "Role does not exist"
    )
    try:
        session.add(participant2)
        session.commit()
    except Exception as e:
        print(e)


with EchoSession() as session:
    print()
    print("---------------------------------- TEST CHECK CONSTRAINTS AGAIN")

    role = "observer"
    report = Report(
        species="Eichhörnchen",
        report_participant_associations=[
            ReportParticipantsUnregistered(
                role="creator",
                participant=UnregisteredParticipant(
                    name="Peter", email="peter@example.com"
                ),
            )
        ],
    )
    session.add(report)
    session.commit()

    print(report, report.participants)

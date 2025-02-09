from __future__ import annotations
import os
from xml.dom.domreg import registered
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    ForeignKey,
    select,
    func,
    or_,
    union,
    join,
)
from sqlalchemy.orm import (
    declarative_base,
    as_declarative,
    relationship,
    sessionmaker,
    backref,
    column_property,
    remote,
    Mapped,
    mapped_column,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy
from sqlalchemy.ext.hybrid import hybrid_property

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

    participants: Mapped[list[ReportParticipants]] = relationship()

    @property
    def participants_count(self):
        return len(self.participants)


class Participant(Base):
    __tablename__ = "participant"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String)

    __mapper_args__ = {"polymorphic_on": type}

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
    __mapper_args__ = {"polymorphic_identity": "unregistered"}

    id: Mapped[int] = mapped_column(ForeignKey(Participant.id), primary_key=True)

    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)


class RegisteredParticipant(Participant):
    """Uses the parent-table.

    To get an extra table use a tablename and the id column.
    """
    __tablename__ = None
    # __tablename__ = "registered_participant"
    __mapper_args__ = {"polymorphic_identity": "registered"}

    # id: Mapped[int] = mapped_column(ForeignKey(Participant.id), primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey(User.id), unique=True, nullable=True
    )
    user: Mapped[User] = relationship(single_parent=True)

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
    report = relationship(Report)

    participant_id = Column(Integer, ForeignKey(Participant.id))
    participant = relationship(Participant)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.report.species}, {self.role})"


class ReportParticipantsUnregistered(ReportParticipants):
    __tablename__ = "report_participants_unregistered"
    __mapper_args__ = {"polymorphic_identity": "unregistered"}

    id: Mapped[int] = mapped_column(ForeignKey(ReportParticipants.id), primary_key=True)


class ReportParticipantsRegistered(ReportParticipants):
    __tablename__ = "report_participants_registered"
    __mapper_args__ = {"polymorphic_identity": "registered"}

    id: Mapped[int] = mapped_column(ForeignKey(ReportParticipants.id), primary_key=True)


# if os.path.exists("database.db"):
#     os.remove("database.db")
# engine = create_engine("sqlite:///database.db", echo=True)
engine = create_engine("sqlite:///:memory:", echo=True)

Base.metadata.create_all(engine)

engine.echo = False
Session = sessionmaker(bind=engine)
session = Session()

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
    UnregisteredParticipant(name="Marlene Mustermann", email="marlene@mustermann.com"),
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
print("#  Report Participants:".ljust(30), reports[0].participants_count, reports[0].participants)
print("#  Reports per User:".ljust(30), [p.reports_count for p in session.query(Participant)])
print("#  Reports AssociationProxy:".ljust(30), session.query(Participant).first().reports)

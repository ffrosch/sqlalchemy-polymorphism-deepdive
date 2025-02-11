from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
    Base,
    _ROLES,
    Report,
    ReportParticipantAssociation,
    ReportRole,
    User,
    ReportParticipantUnregistered,
    ReportParticipantRegistered,
    ReportParticipantRoleAssociation,
)
import os

db = "database.db"
if os.path.exists(db) and os.path.isfile(db):
    os.remove(db)

engine = create_engine(f"sqlite:///{db}")

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)


def create_roles():
    with Session() as session:
        roles = [ReportRole(name=name) for name in _ROLES]
        session.add_all(roles)
        session.commit()


def create_users():
    with Session() as session:
        users = [User(name=f"User {i}") for i in range(5)]
        session.add_all(users)
        session.commit()


def create_reports():
    with Session() as session:
        reports = [Report(species=f"Species {i}") for i in range(10)]
        session.add_all(reports)
        session.commit()


def create_participants():
    with Session() as session:
        users = session.query(User).all()

        for i in range(5):
            session.add(ReportParticipantRegistered(user=users[i]))
            session.add(ReportParticipantUnregistered(name=f"Unregistered User {i}"))
            session.add(
                ReportParticipantUnregistered(name=f"Unregistered User {i + 6}")
            )
            session.add(
                ReportParticipantAssociation(report_id=i + 1, participant_id=i + 1)
            )
            session.add(
                ReportParticipantRoleAssociation(
                    role_id=1,
                    report_id=i + 1,
                    rpa_participant_id=i + 1,
                    rpa_report_id=i + 1,
                )
            )
            session.add(
                ReportParticipantRoleAssociation(
                    role_id=2,
                    report_id=i + 1,
                    rpa_participant_id=i + 1,
                    rpa_report_id=i + 1,
                )
            )
            session.add(
                ReportParticipantAssociation(report_id=i + 1, participant_id=i + 6)
            )
            session.add(
                ReportParticipantRoleAssociation(
                    role_id=3,
                    report_id=i + 1,
                    rpa_participant_id=i + 6,
                    rpa_report_id=i + 1,
                )
            )

        session.commit()


def create_all():
    create_roles()
    create_users()
    create_reports()
    # create_participants()


if __name__ == "__main__":
    with Session() as session:
        participant = ReportParticipantUnregistered(name="Test Unregistered")
        report = Report(
            species="Test Species",
            participants=[
                {
                    "participant": participant,
                    "roles": ["creator", "reporter"],
                }
            ]
        )
        print(report.participants)
        print(participant.roles)

        session.add(report)
        session.commit()

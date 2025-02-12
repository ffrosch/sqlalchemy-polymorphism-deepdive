from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from polymorphic_with_auxilliary.models import (
    Base,
    Report,
    ReportParticipant,
    ReportParticipantRegistered,
    ReportParticipantRole,
    ReportParticipantUnregistered,
    Role,
    User,
)


def Session(echo=True):
    engine = create_engine(f"sqlite:///:memory:", echo=echo)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def FileSession(echo=True):
    db = "database.db"
    engine = create_engine(f"sqlite:///{db}", echo=echo)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def create_roles(session):
    roles = [Role(name=name) for name in Role.initial_data()]
    session.add_all(roles)
    session.commit()


def create_users(session):
    users = [User(name=f"User {i}") for i in range(5)]
    session.add_all(users)
    session.commit()


def create_reports(session):
    reports = [Report(species=f"Species {i}") for i in range(10)]
    session.add_all(reports)
    session.commit()


def create_all(session):
    create_roles(session)
    create_users(session)
    create_reports(session)


def get_roles(session):
    return session.scalars(select(Role)).all()


def create_report(session, species = "Katze") -> Report:
    report = Report(species=species)
    session.add(report)
    session.commit()
    return report


def create_user(session, name = "Test User") -> User:
    user = User(name=name)
    session.add(user)
    session.commit()
    return user


def create_participant(session, report, user=False, roles=None):
    roles = roles if roles else []
    if user:
        participant = ReportParticipantRegistered(
            user=User(name="Registered User"),
            roles=roles,
        )
        participant.report = report
    else:
        participant = ReportParticipantUnregistered(
            name="Unregistered User",
            roles=roles,
        )
        participant.report = report

    session.add(participant)
    session.commit()

    return participant


if __name__ == "__main__":
    session = Session()
    create_roles(session)
    create_users(session)
    create_reports(session)

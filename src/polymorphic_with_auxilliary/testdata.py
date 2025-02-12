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
    with Session() as session:
        create_roles(session)
    return Session()


def FileSession(echo=True):
    db = "database.db"
    engine = create_engine(f"sqlite:///{db}", echo=echo)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def get_roles(session):
    return session.scalars(select(Role)).all()


def create_report(session, species="Katze") -> Report:
    report = Report(species=species)
    session.add(report)
    session.commit()
    return report


def create_reports(session, n: int = 10):
    reports = [Report(species=f"Species {i}") for i in range(n)]
    session.add_all(reports)
    session.commit()


def create_roles(session):
    roles = [Role(name=name) for name in Role.initial_data()]
    session.add_all(roles)
    session.commit()


def create_user(session, name="Test User") -> User:
    user = User(name=name)
    session.add(user)
    session.commit()
    return user


def create_users(session, n: int = 5):
    users = [User(name=f"User {i}") for i in range(n)]
    session.add_all(users)
    session.commit()


def create_all(session):
    create_roles(session)
    create_users(session)
    create_reports(session)


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


def create_reports_with_participants(session):
    roles = get_roles(session)
    reports = []
    for i in range(5):
        reports.append(
            Report(
                species=f"Species {i}",
                participants=[
                    ReportParticipantUnregistered(
                        name=f"Unregistered Participant {i} {j}",
                        roles=[roles[j]],
                    )
                    for j in range(3)
                ],
            )
        )
        reports.append(
            Report(
                species=f"Species {i}",
                participants=[
                    ReportParticipantRegistered(
                        user=User(name=f"Registered Participant {i} {j}"),
                        roles=[roles[j]],
                    )
                    for j in range(3)
                ],
            )
        )
        # One user with multiple roles in the same report
        users = [User(name=f"User {i}") for i in range(3)]
        for i, user in enumerate(users):
            reports.append(
                Report(
                    species=f"Other Species {i}",
                    participants=[
                        ReportParticipantRegistered(
                            user=user,
                            roles=roles,
                        )
                    ],
                )
            )
        # One user with multiple roles in different reports
        user = User(name=f"User Multireport {i}")
        for j in range(3):
            reports.append(
                Report(
                    species=f"Species Multireport {i}",
                    participants=[
                        ReportParticipantRegistered(
                            user=user,
                            roles=[roles[j]],
                        )
                    ],
                )
            )
    session.add_all(reports)
    session.commit()


if __name__ == "__main__":
    session = Session()
    create_roles(session)
    create_users(session, n=5)
    create_reports(session, n=10)

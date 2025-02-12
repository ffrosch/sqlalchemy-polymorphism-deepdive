from typing import Optional
import pytest  # type: ignore
from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import sessionmaker
import random

from polymorphic_with_auxilliary.models import (
    Base,
    Report,
    ReportParticipantRegistered,
    ReportParticipantRole,
    ReportParticipantUnregistered,
    Role,
    User,
)


@pytest.fixture(scope="session")
def engine():
    """
    Creates an in-memory SQLite engine and sets up the schema.
    The same engine is used for the duration of the test session.
    """
    engine = create_engine("sqlite:///:memory:")

    def _fk_pragma_on_connect(dbapi_con, con_record):
        dbapi_con.execute('pragma foreign_keys=ON')

    from sqlalchemy import event
    event.listen(engine, 'connect', _fk_pragma_on_connect)

    # Create all tables defined in the Base's metadata.
    Base.metadata.create_all(engine)

    yield engine
    # Teardown: drop all tables after the tests complete.
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine):
    """
    Creates a new database session for a test with a nested transaction.
    The transaction is rolled back at the end of the test to ensure isolation.
    """
    # Establish a connection and begin a non-ORM transaction.
    connection = engine.connect()
    transaction = connection.begin()

    # Bind a session to this connection.
    Session = sessionmaker(bind=connection)
    session = Session()

    roles = [Role(name=role) for role in Role.initial_data()]
    session.add_all(roles)

    yield session

    # Cleanup: close the session, roll back the transaction, and close the connection.
    session.close()
    transaction.rollback()
    connection.close()


###############################################################################
# Factory Fixtures for Models
###############################################################################


@pytest.fixture
def user_factory(session):
    """Factory fixture to create and persist a User."""

    def create_user(name: Optional[str] = None) -> User:
        if name is None:
            name = f"User {random.randint(1, 100)}"
        user = User(name=name)
        session.add(user)
        # A commit here is safe because it only commits within the SAVEPOINT.
        session.commit()
        return user

    return create_user


@pytest.fixture
def report_factory(session):
    """Factory fixture to create and persist a Report."""

    def create_report(species: Optional[str] = None) -> Report:
        species = species or f"Species {random.randint(1, 100)}"
        report = Report(species=species)
        session.add(report)
        session.commit()
        return report

    return create_report


@pytest.fixture
def roles(session):
    return session.scalars(select(Role)).all()


@pytest.fixture
def participant_factory(session, roles):
    """Factory fixture to create and persist a ReportParticipant."""

    def create_participant(report, user=False, roles=[roles[0]]):
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

    return create_participant

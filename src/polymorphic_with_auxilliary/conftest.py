from typing import Optional
import pytest  # type: ignore
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random

from polymorphic_with_auxilliary.models import (
    Base,
    Report,
    ReportParticipantAssociation,
    ReportParticipantRegistered,
    ReportParticipantRole,
    ReportParticipantUnregistered,
    User,
)



@pytest.fixture(scope="session")
def engine():
    """
    Creates an in-memory SQLite engine and sets up the schema.
    The same engine is used for the duration of the test session.
    """
    engine = create_engine("sqlite:///:memory:")
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
def users_factory(user_factory):
    """Factory fixture to create and persist multiple Users."""
    def create_users(n: int) -> list[User]:
        return [user_factory() for _ in range(n)]
    return create_users


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
def reports_factory(report_factory):
    """Factory fixture to create and persist multiple Reports."""
    def create_reports(n: int) -> list[Report]:
        return [report_factory() for _ in range(n)]
    return create_reports

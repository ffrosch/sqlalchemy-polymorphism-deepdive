import random
from functools import partial
from typing import Optional

import pytest  # type: ignore
from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import sessionmaker

from polymorphic_with_auxilliary.models import (
    Base,
    Report,
    ReportParticipantRegistered,
    ReportParticipantRole,
    ReportParticipantUnregistered,
    Role,
    User,
)
from polymorphic_with_auxilliary.testdata import (
    create_participant,
    create_report,
    create_user,
    get_roles,
)


@pytest.fixture(scope="session")
def engine():
    """
    Creates an in-memory SQLite engine and sets up the schema.
    The same engine is used for the duration of the test session.
    """
    engine = create_engine("sqlite:///:memory:")

    def _fk_pragma_on_connect(dbapi_con, con_record):
        """Make SQLite respect FK constraints."""
        dbapi_con.execute("pragma foreign_keys=ON")

    from sqlalchemy import event

    event.listen(engine, "connect", _fk_pragma_on_connect)

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
    if transaction.is_active:
        transaction.rollback()
    connection.close()


###############################################################################
# Factory Fixtures for Models
###############################################################################


@pytest.fixture
def user_factory(session):
    """Factory fixture to create and persist a User."""
    return partial(create_user, session)


@pytest.fixture
def report_factory(session):
    """Factory fixture to create and persist a Report."""
    return partial(create_report, session)


@pytest.fixture
def roles(session):
    return get_roles(session)


@pytest.fixture
def participant_factory(session, roles):
    """Factory fixture to create and persist a ReportParticipant."""
    return partial(create_participant, session, roles=[roles[0]])

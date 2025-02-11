from functools import partial
import pytest  # type: ignore
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from polymorphic_with_auxilliary import create
from polymorphic_with_auxilliary.models import Base


@pytest.fixture(scope="module")
def engine():
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="module")
def tables(engine):
    Base.metadata.drop_all(engine)
    yield
    Base.metadata.create_all(engine)


@pytest.fixture()
def session(engine, tables):
    Session = sessionmaker(bind=engine)
    return Session()

"""https://github.com/sqlalchemy/sqlalchemy/discussions/6862


"""

from datetime import datetime
from enum import Enum
import re

import sqlalchemy as sa
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.ext.declarative import declared_attr
import sqlalchemy.orm as orm


class Timestamp(object):

    created = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    updated = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)


@as_declarative()
class Base(Timestamp):
    """SQLAlchemy Base class for all database models."""

    @declared_attr
    def __tablename__(cls) -> str:  # pylint: disable=no-self-argument
        """Define table name for all models as the snake case of the model's name."""
        first_pass = re.sub(
            r"(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__
        )  # pylint: disable=no-member
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first_pass).lower()

    id = sa.Column(sa.Integer, primary_key=True)


class Organization(Base):
    """Represents an Organization entity."""

    name = sa.Column(sa.TEXT)
    short_id = sa.Column(
        sa.Integer, sa.Sequence("organization_short_id_sequence")
    )


class BusinessUnit(Base):
    """Represents a Business Unit entity."""

    name = sa.Column(sa.TEXT)
    short_id = sa.Column(
        sa.Integer, sa.Sequence("business_unit_short_id_sequence")
    )

    business_unit_legacy_datum = sa.orm.relationship(
        "BusinessUnitLegacyDatum",
        back_populates="business_unit",
        uselist=False,
    )

    legacy_datum = sa.orm.relationship(
        "LegacyDatum",
        secondary="entity_legacy_datum",
        back_populates="business_unit",
        uselist=False,
    )

    legacy_datum_proxy = association_proxy(
        "business_unit_legacy_datum",
        "legacy_datum",
        creator=lambda legacy_datum: BusinessUnitLegacyDatum(
            legacy_datum=legacy_datum
        ),
    )


class LegacyDatum(Base):
    """Represents a Legacy Datum entity."""

    foo = sa.Column(sa.INTEGER, nullable=True)

    business_unit_legacy_datum = sa.orm.relationship(
        "BusinessUnitLegacyDatum", back_populates="legacy_datum", uselist=False
    )

    business_unit = sa.orm.relationship(
        "BusinessUnit",
        secondary="entity_legacy_datum",
        back_populates="legacy_datum",
        uselist=False,
        viewonly=True,
    )


class EntityTypes(Enum):
    """Enum values for all polymorphic Entity Types that TEvo supports."""

    ORGANIZATION = Organization.__name__.lower()
    BUSINESS_UNIT = BusinessUnit.__name__.lower()


class EntityLegacyDatum(Base):
    """1 to 1 polymorphic mapping between an EntityType and Legacy Datum."""

    entity_type = sa.Column(
        sa.Enum(EntityTypes, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    legacy_datum_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(f"{LegacyDatum.__tablename__}.id"),
        nullable=False,
    )

    __mapper_args__ = {"polymorphic_on": entity_type}


class BusinessUnitLegacyDatum(EntityLegacyDatum):
    """1 to 1 mapping between a BusinessUnit and Legacy Datum."""

    # single table inheritance
    __tablename__ = None

    entity_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(f"{BusinessUnit.__tablename__}.id"),
        nullable=False,
    )

    business_unit = sa.orm.relationship(
        "BusinessUnit", back_populates="business_unit_legacy_datum"
    )
    legacy_datum = sa.orm.relationship(
        "LegacyDatum", back_populates="business_unit_legacy_datum"
    )

    __mapper_args__ = {
        "polymorphic_identity": EntityTypes(BusinessUnit.__name__.lower())
    }


engine = sa.create_engine("sqlite://", echo=True)
Base.metadata.create_all(engine)

engine.echo = False
session = orm.Session(engine)


# CREATE A RELATIONSHIP BY MODELING THE RELATIONSHIP FIRST AND ASSIGNING EXISTING MODELS
# TESTS READS ON THE ASSOCIATION TABLE
legacy_datum = LegacyDatum(foo=123)
business_unit = BusinessUnit(name="foobar")
business_unit_legacy_datum = BusinessUnitLegacyDatum(
    legacy_datum=legacy_datum, business_unit=business_unit
)
session.add_all([legacy_datum, business_unit, business_unit_legacy_datum])
session.commit()

session.query(BusinessUnit).filter(BusinessUnit.id == business_unit.id)

print("===============================================")
print(
    f"Business unit can read legacy datum with id: {business_unit.legacy_datum.id}"
)

session.query(LegacyDatum).filter(LegacyDatum.id == legacy_datum.id)

print("===============================================")
print(
    f"Legacy Datum can read business unit with id: {legacy_datum.business_unit.id}"
)


# CREATE A RELATIONSHIP BY ADDING AN ASSOCIATED MODEL DIRECTLY
# TESTS WRITES ON THE ASSOCIATION TABLE

legacy_datum_2 = LegacyDatum(foo=321)
business_unit_2 = BusinessUnit(name="barfoo")

session.add_all([legacy_datum_2, business_unit_2])
session.commit()

print("=================================================")
print("Attempting a direct set of the associated record")

# we want the equivalent of this
# session.add(
#    BusinessUnitLegacyDatum(
#        business_unit=business_unit_2, legacy_datum=legacy_datum_2
#    )
# )
business_unit_2.legacy_datum_proxy = legacy_datum_2
# legacy_datum_2.business_unit = business_unit_2
session.commit()

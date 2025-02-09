"""https://github.com/sqlalchemy/sqlalchemy/wiki/PolymorphicOnAnotherTable

This example illustrates some methods of applying polymorphic identity based on
rows in another table. The class being polymorphically persisted and loaded
would normally have a relationship() to this related table.

SQLAlchemy currently does not directly support using a related class as a
target for the polymorphic_on parameter.

However, there are a few ways of achieving equivalent behavior based on
using column attributes.

Another method is to populate mapper.polymorphic_map up front with the integer
primary key value of the related objects, and set polymorphic_on to be against
the primary key of the related table. This requires an initial "load" of the
related table when the mappers are first configured, but once set up the
mappings work more transparently, and the SELECT statement emitted is also
more efficient as there is no correlated subquery involved:
"""

from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import select
from sqlalchemy import String
from sqlalchemy.orm import column_property
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

Base = declarative_base()


class AType(Base):
    __tablename__ = "atype"

    id = Column(Integer, primary_key=True)
    name = Column(String)


class A(Base):
    __tablename__ = 'a'

    id = Column(Integer, primary_key=True)
    data = Column(String)
    type_id = Column(ForeignKey('atype.id'))
    type = relationship(AType)

    __mapper_args__ = {
        "polymorphic_on": type_id,
        "polymorphic_identity": "a"
    }



class ASub(A):
    __tablename__ = "asub"

    id = Column(ForeignKey("a.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": "asub"}


e = create_engine("sqlite://", echo='debug')
Base.metadata.create_all(e)

e.echo = False
sess = Session(e)

a_type, asub_type = AType(name="a"), AType(name="asub")

sess.add_all([a_type, asub_type])
sess.commit()


# assume application starts up, and AType is populated.  we want
# to populate the polymorphic map for "A" with the integer primary key
# values of the AType objects
A.__mapper__.polymorphic_map.update(
    (key, A.__mapper__.polymorphic_map[value])
    for (key, value) in sess.query(AType.id, AType.name)
)


# polymorphic identity will be assigned automatically

sess.add_all(
    [
        A(data="a1"),
        ASub(data="asub1"),
        ASub(data="asub2"),
        A(data="a2"),
    ]
)
sess.commit()

sess = Session(e)
for a in sess.query(A):
    print(a.data, a.type)

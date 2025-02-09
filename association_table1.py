from __future__ import annotations
import os
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
from sqlalchemy.orm import relationship, sessionmaker, backref, column_property, remote
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class Person(Base):
    __tablename__ = "person"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)

    __mapper_args__ = {
        "polymorphic_on": type,
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"


class User(Person):
    __mapper_args__ = {"polymorphic_identity": "user"}

    user_report_assocation = relationship("UserReports", back_populates="user")

    reports = association_proxy(
        "user_report_assocation",
        "report",
        creator=lambda report_obj: UserReports(report=report_obj),
    )


class Anon(Person):
    __mapper_args__ = {"polymorphic_identity": "anon"}

    anon_report_assocation = relationship("AnonReports", back_populates="anon")

    reports = association_proxy(
        "anon_report_assocation",
        "report",
        creator=lambda report_obj: AnonReports(report=report_obj),
    )


# Association tables
class UserReports(Base):
    __tablename__ = "user_reports"
    person_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    report_id = Column(Integer, ForeignKey("report.id"), primary_key=True)

    user = relationship("User", back_populates="user_report_assocation")

    report = relationship("Report")


class AnonReports(Base):
    __tablename__ = "anon_reports"
    person_id = Column(Integer, ForeignKey(Anon.id), primary_key=True)
    report_id = Column(Integer, ForeignKey("report.id"), primary_key=True)

    anon = relationship("Anon", back_populates="anon_report_assocation")

    report = relationship("Report")


# Report model
class Report(Base):
    __tablename__ = "report"
    id = Column(Integer, primary_key=True)

    user_reports = relationship("UserReports", back_populates="report")
    anon_reports = relationship("AnonReports", back_populates="report")

    # Define association proxies
    users = association_proxy("user_reports", "user")
    anons = association_proxy("anon_reports", "anon")

    report_participants_stmt = union(
        select(UserReports.__table__), select(AnonReports.__table__)
    ).subquery()

    participants = relationship(
        "Person",
        secondary=report_participants_stmt,
        primaryjoin=lambda: Report.id == remote(Report.report_participants_stmt.c.report_id),
        secondaryjoin=lambda: Person.id == remote(Report.report_participants_stmt.c.person_id),
        viewonly=True,
    )

    @hybrid_property
    def participants_count(self):
        return len(self.participants)

    @participants_count.expression
    def participants_count(cls):
        return select(func.count(cls.participants))


    def __repr__(self):
        return f"{self.__class__.__name__}({self.id})"


# if os.path.exists("database.db"):
#     os.remove("database.db")
# engine = create_engine("sqlite:///database.db", echo=True)
engine = create_engine("sqlite:///:memory:", echo=True)
Base.metadata.create_all(engine)

engine.echo = False
Session = sessionmaker(bind=engine)
session = Session()

# Add example data
report1 = Report()
report2 = Report()

user = User(name="Johann Experte", reports=[report1, report2])

anon1 = Anon(name="Willy Wilder", reports=[report1])
anon2 = Anon(name="Tom Taugenichts")

session.add_all([user, anon1, anon2])
session.commit()

# Querying both association tables for a specific report
report = session.query(Report).first()
persons = session.query(Person).all()

print("Participants count:", report.participants_count)
print("Users:", report.users)
print("Anons:", report.anons)
print("All persons:", persons)
print(f"Reports by user: {user.name}", user.reports)
print(f"Report Participants for: {report}", report.participants)

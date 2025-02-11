from __future__ import annotations
import pytest  # type: ignore

from polymorphic_with_auxilliary.models import (
    Base,
    Report,
    ReportParticipantAssociation,
    ReportParticipantRegistered,
    ReportParticipantRole,
    ReportParticipantUnregistered,
    User,
)


class TestReport:
    def test_create_and_read_report(self, session, report_factory):
        """
        Test creating and reading a report.
        """
        report = report_factory()
        retrieved = session.get(Report, 1)

        assert retrieved.id == report.id
        assert retrieved.species == report.species

    def test_create_and_read_all_reports(self, session, reports_factory):
        """
        Test creating and reading multiple reports.
        """
        count = 5
        reports = reports_factory(count)
        retrieved_reports = session.query(Report).all()

        assert len(retrieved_reports) == count
        for i in range(count):
            assert retrieved_reports[i].id == reports[i].id
            assert retrieved_reports[i].species == reports[i].species



class TestUser:
    def test_create_and_read_user(self, session, user_factory):
        """
        Test creating and reading a user.
        """
        user = user_factory()
        retrieved = session.get(User, 1)

        assert retrieved.id == user.id
        assert retrieved.name == user.name

    def test_create_and_read_all_users(self, session, users_factory):
        """
        Test creating and reading multiple users.
        """
        count = 5
        users = users_factory(count)
        retrieved_users = session.query(User).all()

        assert len(retrieved_users) == count
        for i in range(count):
            assert retrieved_users[i].id == users[i].id
            assert retrieved_users[i].name == users[i].name

from __future__ import annotations

import pytest  # type: ignore
from sqlalchemy import func, select

from polymorphic_with_auxilliary.models import (
    Report,
    ReportParticipant,
    ReportParticipantRegistered,
    ReportParticipantRole,
    ReportParticipantUnregistered,
    Role,
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

    def test_create_and_read_all_reports(self, session, report_factory):
        """
        Test creating and reading multiple reports.
        """
        count = 5
        reports = [report_factory() for _ in range(count)]
        retrieved_reports = session.query(Report).all()

        assert len(retrieved_reports) == count
        for i in range(count):
            assert retrieved_reports[i].id == reports[i].id
            assert retrieved_reports[i].species == reports[i].species

    def test_delete_report(self, session, report_factory, participant_factory):
        """
        Test deleting a report.
        """
        report = report_factory()
        participant_factory(report)
        session.delete(report)
        session.commit()

        assert session.scalar(select(Report)) is None
        assert session.scalar(select(ReportParticipant)) is None
        assert session.scalar(select(ReportParticipantRole)) is None


class TestReportParticipant:
    def test_create_registered_participant(
        self, session, report_factory, participant_factory
    ):
        """
        Test creating a registered participant.
        """
        participant_factory(report_factory(), user=True)
        assert session.scalars(select(ReportParticipantRegistered)).one()

    def test_create_unregistered_participant(
        self, session, report_factory, participant_factory
    ):
        """
        Test creating an unregistered participant.
        """
        participant_factory(report_factory(), user=False)
        assert session.scalars(select(ReportParticipantUnregistered)).one()

    def test_create_polymorphic_participant(
        self, session, report_factory, participant_factory
    ):
        """
        Test creating a polymorphic participant.
        """
        participant_factory(report_factory(), user=True)
        participant_factory(report_factory(), user=False)
        assert session.scalar(select(func.count(ReportParticipant.id))) == 2
        assert session.scalar(select(func.count(ReportParticipantRegistered.id))) == 1
        assert session.scalar(select(func.count(ReportParticipantUnregistered.id))) == 1

    def test_update_participant_role(
        self, session, roles, report_factory, participant_factory
    ):
        """
        Test updating the role of a participant.
        """
        old_role, new_role = roles[0], roles[1]
        participant = participant_factory(report_factory(), roles=[old_role])
        participant.roles = [new_role]
        session.commit()

        retrieved_association = session.scalars(select(ReportParticipantRole)).one()
        assert retrieved_association.role.name == new_role.name

    def test_delete_participant(self, session, report_factory, participant_factory):
        """
        Test deleting a participant.
        """
        report = report_factory()
        participant_factory(report)
        report.participants = []
        session.commit()

        assert session.scalar(select(ReportParticipant)) is None
        assert session.scalar(select(ReportParticipantRole)) is None


class TestUser:
    def test_create_and_read_user(self, session, user_factory):
        """
        Test creating and reading a user.
        """
        user = user_factory()
        retrieved = session.get(User, 1)

        assert retrieved.id == user.id
        assert retrieved.name == user.name

    def test_create_and_read_all_users(self, session, user_factory):
        """
        Test creating and reading multiple users.
        """
        count = 5
        users = [u for u in map(user_factory, range(count))]
        retrieved_users = session.query(User).all()

        assert len(retrieved_users) == count
        for i in range(count):
            assert retrieved_users[i].id == users[i].id
            assert retrieved_users[i].name == users[i].name

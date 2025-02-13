from __future__ import annotations

import pytest  # type: ignore
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from src.models import (
    Report,
    ReportParticipantAssociation,
    ReportParticipantRegistered,
    ReportParticipantRoleAssociation,
    ReportParticipantUnregistered,
    ReportParticipantRole,
    User,
)


class TestParticipant:
    def test_create_participant_without_role(self, report_factory, participant_factory):
        """
        Test creating a participant that has no role
        """
        with pytest.raises(ValueError):
            report = report_factory()
            participant = participant_factory(report, roles=None)

    def test_assign_participant_with_duplicate_role(
        self, session, report_factory, participant_factory
    ):
        """
        Test that assignment of duplicate roles for same participant fails
        """
        with pytest.raises(IntegrityError):
            role = session.scalar(select(ReportParticipantRole))
            participant = participant_factory(report_factory(), roles=[role, role])

            session.add(participant)
            session.commit()

    def test_assign_duplicate_role(self, session, report_factory, participant_factory):
        """
        Test that assignment of duplicate roles for different participants fails
        """
        with pytest.raises(IntegrityError):
            role = session.scalar(select(ReportParticipantRole))

            report = report_factory()
            report.participants = [
                ReportParticipantUnregistered(name="Participant 1", roles=[role]),
                ReportParticipantUnregistered(name="Participant 2", roles=[role]),
            ]

            session.add(report)
            session.commit()

    def test_participant_must_be_unique(
        self, session, report_factory, participant_factory
    ):
        """
        Test that assignment of a participant to multiple reports fails due to FK constraint
        """
        with pytest.raises(IntegrityError):
            report1 = report_factory()
            report2 = report_factory()

            participant = participant_factory(report1)

            report2.participants.append(participant)
            session.commit()

    def test_sqlite_fk_constraint_set(
        self, session, report_factory, participant_factory
    ):
        """
        If this assignment doesn't fail, the FK constraint is not enforced
        (must be set manually on SQLite)
        """
        with pytest.raises(IntegrityError):
            report1 = report_factory()
            report2 = report_factory()

            participant = participant_factory(report1)

            report2.participants.append(participant)
            session.commit()

            # If the foreign key constraint is not activated in SQLite,
            # the report_id in the association will be set to report2.
            # but the report_id in ReportParticipantRoleAssociation will stay set to report1.
            assoc_report_id = session.scalars(select(ReportParticipantAssociation.report_id)).one()
            role_report_id = session.scalars(
                select(ReportParticipantRoleAssociation.report_id)
            ).one()

            assert assoc_report_id == role_report_id
            assert assoc_report_id == report1.id
            assert role_report_id == report1.id

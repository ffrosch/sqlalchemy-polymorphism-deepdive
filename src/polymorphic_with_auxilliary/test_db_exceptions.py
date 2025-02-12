from __future__ import annotations
from sqlalchemy.exc import IntegrityError, OperationalError

from sqlalchemy import select

import pytest  # type: ignore

from polymorphic_with_auxilliary.models import (
    Report,
    ReportParticipant,
    ReportParticipantRegistered,
    ReportParticipantRole,
    ReportParticipantUnregistered,
    Role,
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

    def test_create_participant_with_duplicate_role(self, session, report_factory, participant_factory):
        """
        Test assigning a participant to a report with the same role twice
        """
        with pytest.raises(IntegrityError):
            role = session.scalar(select(Role))
            participant = participant_factory(report_factory(), roles=[role, role])

            session.add(participant)
            session.commit()

    def test_participant_must_be_unique(self, session, report_factory, participant_factory):
        """
        Test the assignment of a participant to multiple reports
        """
        with pytest.raises(IntegrityError):
            report1 = report_factory()
            report2 = report_factory()

            participant = participant_factory(report1)

            report2.participants.append(participant)
            session.commit()

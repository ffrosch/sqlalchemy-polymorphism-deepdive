from functools import partial
import pytest  # type: ignore
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, InvalidRequestError

from improved import (
    Base,
    Report,
    ReportParticipant,
    ReportParticipantAssociation,
    ReportParticipantRegistered,
    ReportParticipantUnregistered,
    User,
)


@pytest.fixture(scope="module")
def engine():
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="module")
def tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    # yield


@pytest.fixture()
def session(engine, tables):
    Session = sessionmaker(bind=engine)
    return Session()


def test_create_reports_success(session):
    reports = [Report(species=f"Species {i}") for i in range(5)]
    session.add_all(reports)
    session.commit()
    assert session.query(Report).count() == 5


def test_create_users_success(session):
    users = [User(name=f"User {i}") for i in range(5)]
    session.add_all(users)
    session.commit()
    assert session.query(User).count() == 5


def test_create_reportparticipantunregisterds_success(session):
    participants = [
        ReportParticipantUnregistered(name=f"Unregistered {i}") for i in range(5)
    ]
    session.add_all(participants)
    session.commit()
    assert session.query(ReportParticipantUnregistered).count() == 5


def test_create_reportparticipantregisterds_success(session):
    users = [User(name=f"User {i}") for i in range(5)]
    participants = [ReportParticipantRegistered(user=users[i]) for i in range(5)]
    session.add_all(participants)
    session.commit()
    assert session.query(ReportParticipantRegistered).count() == 5


def test_create_reportparticipant_raises_integrityerror_when_empty(session):
    with pytest.raises(IntegrityError):
        participant = ReportParticipant()
        session.add(participant)
        session.commit()


def test_create_reportparticipant_raises_valueerror_when_invalid_discriminator(session):
    with pytest.raises(ValueError):
        participant = ReportParticipant(discriminator="invalid_type")
        session.add(participant)
        session.commit()


def test_create_reportparticipantunregistered_raises_integrity_error_when_empty(
    session,
):
    with pytest.raises(IntegrityError):
        participant = ReportParticipantUnregistered()
        session.add(participant)
        session.commit()
        assert session.query(ReportParticipantUnregistered).count() == 1


def test_create_reportparticipantregistered_raises_integrityerror_when_empty(session):
    with pytest.raises(IntegrityError):
        participant = ReportParticipantRegistered()
        session.add(participant)
        session.commit()


def test_create_reportparticipantassociation_success_when_unregistered(session):
    report = Report(species="Test Species")
    participant = ReportParticipantUnregistered(name="Test Unregistered")

    session.add(
        ReportParticipantAssociation(
            role="creator", report=report, participant=participant
        )
    )
    session.commit()

    assert (
        session.query(ReportParticipantAssociation)
        .filter_by(report_id=report.id, participant_id=participant.id)
        .count()
        == 1
    )


def test_create_reportparticipantassociation_success_when_registered(session):
    user = User(name="Test User")
    report = Report(species="Test Species")
    participant = ReportParticipantRegistered(user=user)

    session.add(
        ReportParticipantAssociation(
            role="creator", report=report, participant=participant
        )
    )
    session.commit()

    assert (
        session.query(ReportParticipantAssociation)
        .filter_by(report_id=report.id, participant_id=participant.id)
        .count()
        == 1
    )


def test_report_participant_association_eager_loading(session):
    report = Report(species="Test Species")
    participant = ReportParticipantUnregistered(name="Test Unregistered")
    session.add(report)
    session.add(participant)
    session.commit()

    association = ReportParticipantAssociation(
        role="creator", report_id=report.id, participant_id=participant.id
    )
    session.add(association)
    session.commit()

    retrieved_association = (
        session.query(ReportParticipantAssociation)
        .filter_by(report_id=report.id, participant_id=participant.id)
        .first()
    )
    assert retrieved_association.report == report
    assert retrieved_association.participant == participant


def test_report_participant_association_delete_cascade(session):
    report = Report(species="Test Species")
    participant = ReportParticipantUnregistered(name="Test Unregistered")
    session.add(report)
    session.add(participant)
    session.commit()

    association = ReportParticipantAssociation(
        role="creator", report_id=report.id, participant_id=participant.id
    )
    session.add(association)
    session.commit()

    session.delete(report)
    session.commit()

    assert (
        session.query(ReportParticipantAssociation)
        .filter_by(report_id=report.id, participant_id=participant.id)
        .count()
        == 0
    )


def test_registeredreportparticipant_create_duplicate_user_raises_integrity_error(
    session,
):
    """Creating two ReportParticipantRegistered objects with the same user raises an InvalidRequestError.

    A user can be registered as ReportParticipant only once.
    The error is caused by the `single_parent=True` on the `user` relationship.
    """
    with pytest.raises(InvalidRequestError):
        user = User(name="Test User")
        ReportParticipantRegistered(user=user)
        ReportParticipantRegistered(user=user)


def test_create_reportparticipantassociation_raisesintegrityerror_when_role_for_report_not_unique(
    session,
):
    with pytest.raises(IntegrityError):
        user = User(name="Test User")
        participant = ReportParticipantRegistered(user=user)
        report = Report(species="Test Species")

        association1 = ReportParticipantAssociation(
            role="creator", participant=participant, report=report
        )
        association2 = ReportParticipantAssociation(
            role="creator", participant=participant, report=report
        )

        session.add_all([association1, association2])
        session.commit()


def test_create_report_participants_via_dictkeyed_success(session):
    user = User(name="Registered User")
    participant = ReportParticipantRegistered(user=user)
    session.add(participant)
    session.commit()

    session.add(
        Report(
            species="Testspecies 1",
            participants={
                "creator": participant,
            },
        )
    )
    session.commit()
    assert (
        session.query(ReportParticipantRegistered)
        .where(ReportParticipantRegistered.user_id == user.id)
        .count()
        == 1
    )


def test_create_reportparticipantassociation_raisesintegrityerror_when_role_is_invalid(
    session,
):
    role = "invalid_role"
    with pytest.raises(IntegrityError):
        session.add(
            ReportParticipantAssociation(
                role=role,
                report=Report(species="Test Species"),
                participant=ReportParticipantUnregistered(name="Test Unregistered"),
            )
        )
        session.commit()


def test_create_reportparticipantassociation_raisesuniqueerror_when_role_reportid_notunique(
    session,
):
    role, report = "observer", Report(species="Test Species")
    with pytest.raises(IntegrityError):
        session.add_all(
            [
                ReportParticipantAssociation(
                    role=role,
                    report=report,
                    participant=ReportParticipantUnregistered(name="Test Unregistered"),
                ),
                ReportParticipantAssociation(
                    role=role,
                    report=report,
                    participant=ReportParticipantUnregistered(name="Test Unregistered"),
                ),
            ]
        )
        session.commit()


def test(session):
    """The same unregistered participant MUST NOT be added to more than one report.

    With the current design this seems to not be possible to prevent.
    """
    report1 = Report(species="Test Species")
    report2 = Report(species="Test Species")
    participant = ReportParticipantUnregistered(name="Test Unregistered Unique")

    session.add_all(
        [
            ReportParticipantAssociation(
                role="creator",
                report=report1,
                participant=participant,
            ),
            ReportParticipantAssociation(
                role="observer",
                report=report1,
                participant=participant,
            ),
        ]
    )
    session.commit()

    with pytest.raises(IntegrityError):
        session.add(
            ReportParticipantAssociation(
                role="creator",
                report=report2,
                participant=participant,
            )
        )
        session.commit()


"""Tests
- delete-orphan: del unregistered from assoc -> unregistered None
- delete-orphan: add user 2x to assoc -> del 1 assoc (registered exists) -> del 1 assoc (registered None)
"""

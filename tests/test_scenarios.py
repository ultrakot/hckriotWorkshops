import json
from unittest.mock import patch, MagicMock

import pytest

from app import create_app
from models import db, Users, Workshop, WorkshopLeader, Registration, UserRole

FAKE_JWT = 'fake.jwt.token'


class TestConfig:
    """Configuration for testing, in-memory SQLite database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # note: can set to True to see SQL queries being executed
    SQLALCHEMY_ECHO = False


@pytest.fixture(scope='module')
def app():
    """Create and configure a new app instance for each test module."""
    app = create_app()
    app.config.from_object(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='module')
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def init_database(app):
    """Set up the database with initial data for each test function."""
    with app.app_context():
        db.create_all()

        # Create Users with different roles
        admin_user = Users(UserId=1, Name='Admin User', Email='admin@test.com', Role=UserRole.ADMIN)
        leader_user = Users(UserId=2, Name='Leader User', Email='leader@test.com', Role=UserRole.WORKSHOP_LEADER)
        participant_user1 = Users(Name='Participant User 1 ', Email='participant1@test.com', Role=UserRole.PARTICIPANT)
        participant_user2 = Users(Name='Participant User 2', Email='participant2@test.com')
        db.session.add_all([admin_user, leader_user, participant_user1, participant_user2])
        db.session.flush()

        # Create Workshops
        workshop1 = Workshop(WorkshopId=1, Title='workshop1 init', Description='A beginner workshop.', MaxCapacity=10,
                             SessionDate='2024-10-26', StartTime='10:00:00', DurationMin=120)
        workshop2 = Workshop(WorkshopId=2, Title='workshop2 init', Description='A deep-dive workshop.', MaxCapacity=5,
                             SessionDate='2024-10-27', StartTime='14:00:00', DurationMin=180)
        db.session.add_all([workshop1, workshop2])

        # Assign leader to first workshop
        leader_assignment = WorkshopLeader(WorkshopId=1, LeaderId=2)
        db.session.add(leader_assignment)

        # Add a registration to the first workshop to test capacity logic
        registration = Registration(WorkshopId=1, UserId=3, Status='Registered')
        db.session.add(registration)

        db.session.commit()
        yield db
        db.session.remove()
        db.drop_all()


def mock_authed_user(mock_get_supabase, user: Users):
    """Helper function to set up the mock for an authenticated user."""
    # mock Supabase `gotrue.models.User` object
    mock_supabase_user = MagicMock()
    mock_supabase_user.email = user.Email
    mock_supabase_user.id = f'fake-supabase-id-for-{user.UserId}'
    mock_supabase_user.user_metadata = {'full_name': user.Name, 'avatar_url': user.AvatarUrl}

    # mock `gotrue.models.UserResponse` object
    mock_user_response = MagicMock()
    mock_user_response.user = mock_supabase_user

    # mock Supabase client object
    mock_supabase_client = MagicMock()
    mock_supabase_client.auth.get_user.return_value = mock_user_response

    # Point our patched `get_supabase` function to our mock client
    mock_get_supabase.return_value = mock_supabase_client
    return mock_supabase_client


class TestEditWorkshop:
    """tests related to editing a workshop."""

    @patch('routes._update_waitlisted_participants')
    @patch('auth.get_supabase')
    def test_workshop_leader_can_edit_own_workshop(self, mock_get_supabase, mock_update_waitlisted, client, init_database):
        """
        GIVEN a workshop leader is authenticated
        WHEN they send a PATCH request to a workshop they lead
        THEN the workshop should be updated successfully.
        """
        # Arrange
        leader_user = db.session.get(Users, 2)
        mock_client = mock_authed_user(mock_get_supabase, leader_user)

        workshop_id = 1
        update_data = {
            'title': 'New Title',
            'description': 'Updated description.',
            'capacity': 15
        }

        # Act
        response = client.patch(
            f'/workshops/{workshop_id}',
            headers={'Authorization': f'Bearer {FAKE_JWT}'},
            data=json.dumps(update_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['message'] == 'Workshop updated successfully.'
        assert 'capacity' in response_data['updated_fields']
        mock_client.auth.get_user.assert_called_once_with(FAKE_JWT)

        updated_workshop = db.session.get(Workshop, workshop_id)
        assert updated_workshop.Title == 'New Title'
        assert updated_workshop.MaxCapacity == 15

        # called because capacity increased
        mock_update_waitlisted.assert_called_once_with(workshop_id)


    @patch('auth.get_supabase')
    def test_workshop_leader_cannot_edit_other_workshop(self, mock_get_supabase, client, init_database):
        """
        GIVEN a workshop leader is authenticated
        WHEN they send a PATCH request to a workshop they DO NOT lead
        THEN they should receive a 403 Forbidden error.
        """
        # Arrange
        leader_user = db.session.get(Users, 2)
        mock_authed_user(mock_get_supabase, leader_user)

        workshop_id_they_dont_lead = 2  # workshop2
        update_data = {'title': 'This Should Not Work'}

        # Act
        response = client.patch(
            f'/workshops/{workshop_id_they_dont_lead}',
            headers={'Authorization': f'Bearer {FAKE_JWT}'},
            data=json.dumps(update_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 403
        assert response.get_json()['error'] == 'Forbidden'
        workshop = Workshop.query.get(workshop_id_they_dont_lead)
        assert workshop.Title == 'workshop2 init'

    @patch('auth.get_supabase')
    def test_admin_can_edit_any_workshop(self, mock_get_supabase, client, init_database):
        """
        GIVEN an admin is authenticated
        WHEN they send a PATCH request to a workshop they do not explicitly lead
        THEN the workshop should be updated successfully.
        """
        # Arrange
        admin_user = Users.query.get(1)
        mock_authed_user(mock_get_supabase, admin_user)

        workshop_id = 2
        update_data = {'title': 'Admin Edit'}

        # Act
        response = client.patch(
            f'/workshops/{workshop_id}',
            headers={'Authorization': f'Bearer {FAKE_JWT}'},
            data=json.dumps(update_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        assert response.get_json()['workshop']['title'] == 'Admin Edit'
        workshop = Workshop.query.get(workshop_id)
        assert workshop.Title == 'Admin Edit'

    @patch('auth.get_supabase')
    def test_participant_cannot_edit_workshop(self, mock_get_supabase, client, init_database):
        """
        GIVEN a regular participant is authenticated
        WHEN they send a PATCH request to any workshop
        THEN they should receive a 403 Forbidden error.
        """
        # Arrange
        participant_user = Users.query.get(3)
        mock_authed_user(mock_get_supabase, participant_user)

        # Act
        response = client.patch(
            '/workshops/1',
            headers={'Authorization': f'Bearer {FAKE_JWT}'},
            data=json.dumps({'title': 'Participant Edit Attempt'}),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 403
        assert response.get_json()['error'] == 'Forbidden'

    @patch('auth.get_supabase')
    def test_edit_workshop_with_invalid_data(self, mock_get_supabase, client, init_database):
        """
        GIVEN a workshop leader is authenticated
        WHEN they send a PATCH request with invalid data
        THEN they should receive a 400 Bad Request error.
        """
        # Arrange
        leader_user = Users.query.get(2)
        mock_authed_user(mock_get_supabase, leader_user)
        workshop_id = 1

        invalid_payloads = [
            ({'title': ''}, 'non-empty string'),
            ({'title': '   '}, 'non-empty string'),
            ({'description': 12345}, 'string'),
            ({'capacity': -1}, 'non-negative integer'),
            ({'capacity': 'ten'}, 'non-negative integer')
        ]

        for payload, error_message in invalid_payloads:
            # Act
            response = client.patch(
                f'/workshops/{workshop_id}',
                headers={'Authorization': f'Bearer {FAKE_JWT}'},
                data=json.dumps(payload),
                content_type='application/json'
            )

            # Assert
            assert response.status_code == 400, f"Failed for payload: {payload}"
            response_data = response.get_json()
            assert error_message in response_data['message'], f"Failed for payload: {payload}"


class TestWorkshopLeadership:
    """Tests the workshop leadership assignment and authorization logic."""

    def test_leader_is_assigned_to_workshop(self, init_database):
        """
        GIVEN a user is assigned as a leader to a workshop
        THEN they should be recognized as the leader and manager for that workshop.
        """
        leader = db.session.get(Users, 2)
        assert leader.is_workshop_leader_for(workshop_id=1)
        assert leader.can_manage_workshop(workshop_id=1)

    def test_leader_is_not_assigned_to_other_workshop(self, init_database):
        """
        GIVEN a user is a leader for one workshop
        THEN they should NOT be recognized as a leader or manager for another.
        """
        leader = db.session.get(Users, 2)
        assert not leader.is_workshop_leader_for(workshop_id=2)
        # They can't manage it because they are not an admin
        assert not leader.can_manage_workshop(workshop_id=2)

    def test_participant_cannot_manage_workshop(self, init_database):
        """
        GIVEN a user is a participant
        THEN they should not be able to manage any workshop.
        """
        participant = Users.query.filter_by(Email='participant1@test.com').one()
        assert not participant.is_workshop_leader_for(workshop_id=1)
        assert not participant.can_manage_workshop(workshop_id=1)

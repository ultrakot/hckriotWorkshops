#!/usr/bin/env python3
"""
Comprehensive API scenario testing for HackerIot Workshop System.
Tests real-world usage patterns and edge cases.
"""

# Fix imports from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest

from app import create_app
from models import db, Users, Workshop, WorkshopLeader, Registration, UserRole, RegistrationStatus, Skill, UserSkill

FAKE_JWT = 'fake.jwt.token'


class TestConfig:
    """Configuration for testing, in-memory SQLite database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # note: can set to True to see SQL queries being executed
    SQLALCHEMY_ECHO = False

    @classmethod
    def get_db_info(cls):
        """
        Provides database info for the test environment, satisfying
        the interface expected by the application.
        """
        return {
            'db_type': 'sqlite_in_memory',
            'database_url': cls.SQLALCHEMY_DATABASE_URI,
            'status': 'configured_for_testing'
        }


@pytest.fixture(scope='module')
def app():
    """Create and configure a new app instance for each test module."""
    app = create_app(config_object=TestConfig)
    return app


@pytest.fixture(scope='module')
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def init_database(app):
    """Set up the database with initial data for each test function."""
    with app.app_context():
        db.create_all()

        # Create sample test data
        print("Creating sample test data...")

        # Create Users with different roles
        admin_user = Users(UserId=1, Name='Admin User', Email='admin@test.com', Role=UserRole.ADMIN)
        leader_user = Users(UserId=2, Name='Leader User', Email='leader@test.com', Role=UserRole.WORKSHOP_LEADER)
        participant_user1 = Users(UserId=3, Name='Participant User 1', Email='participant1@test.com', Role=UserRole.PARTICIPANT)
        participant_user2 = Users(UserId=4, Name='Participant User 2', Email='participant2@test.com', Role=UserRole.PARTICIPANT)
        db.session.add_all([admin_user, leader_user, participant_user1])
        db.session.flush()

        # Create Skills
        skill_py = Skill(Name='python')
        skill_js = Skill(Name='javascript')
        db.session.add(skill_py)
        db.session.add(skill_js)
        db.session.flush()

        # Assign skill to user
        user_skill = UserSkill(UserId=participant_user1.UserId, SkillId=skill_py.SkillId, Grade=1)
        db.session.add(user_skill)

        # Create Workshops

        w1_date = datetime(2025, 9, 10, 9, 0, tzinfo=timezone.utc)
        w2_date = w1_date + timedelta(hours=1)
        w3_date = w1_date + timedelta(hours=3)
        workshop1 = Workshop(WorkshopId=1, Title='workshop1 init', Description='A beginner workshop.', MaxCapacity=10,
                             SessionDateTime=w1_date, DurationMin=90)
        workshop2 = Workshop(WorkshopId=2, Title='workshop2 init', Description='A deep-dive workshop.', MaxCapacity=1,
                             SessionDateTime=w2_date, DurationMin=180)
        workshop3 = Workshop(WorkshopId=3, Title='workshop3 init', Description='workshop3 description.', MaxCapacity=15,
                             SessionDateTime=w3_date, DurationMin=120)
        db.session.add_all([workshop1, workshop2, workshop3])
        db.session.flush()

        # Assign leader to first workshop
        leader_assignment = WorkshopLeader(WorkshopId=workshop1.WorkshopId, LeaderId=leader_user.UserId)
        db.session.add(leader_assignment)

        # Add registrations for the participant
        # participant_user1
        reg1 = Registration(WorkshopId=workshop1.WorkshopId, UserId=participant_user1.UserId,
                            Status=RegistrationStatus.REGISTERED)
        reg2 = Registration(WorkshopId=workshop2.WorkshopId, UserId=participant_user1.UserId,
                            Status=RegistrationStatus.WAITLISTED)
        reg3 = Registration(WorkshopId=workshop3.WorkshopId, UserId=participant_user1.UserId,
                            Status=RegistrationStatus.REGISTERED)
        db.session.add_all([reg1, reg2, reg3])

        db.session.commit()
        yield db

        # clean after each test
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
    def test_workshop_leader_can_edit_own_workshop(self, mock_get_supabase, mock_update_waitlisted, client,
                                                   init_database):
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


class TestCreateWorkshop:
    """Tests for the POST /workshops endpoint."""
    good_workshop_data = {
        "title": "New Advanced Workshop",
        "description": "A new advanced workshop.",
        "session_datetime": "2025-11-15T10:00:00",
        "duration_min": 180,
        "capacity": 20
    }

    @patch('auth.get_supabase')
    def test_admin_can_create_workshop(self, mock_get_supabase, client, init_database):
        """
        GIVEN an admin user is authenticated
        WHEN they send a POST request with valid data
        THEN a new workshop should be created and returned with status 201.
        """
        # Arrange
        admin_user = db.session.get(Users, 1)
        mock_authed_user(mock_get_supabase, admin_user)

        # Act
        response = client.post(
            '/workshops',
            headers={'Authorization': f'Bearer {FAKE_JWT}'},
            data=json.dumps(self.good_workshop_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 201
        response_data = response.get_json()
        assert response_data['message'] == 'Workshop created successfully.'
        assert response_data['workshop']['title'] == "New Advanced Workshop"
        assert response_data['workshop']['capacity'] == 20
        assert response_data['workshop']['session_datetime'] == '2025-11-15T10:00:00'

        # Verify it's in the database
        new_workshop = Workshop.query.get(response_data['workshop']['id'])
        assert new_workshop is not None
        assert new_workshop.Title == "New Advanced Workshop"

        # test /workshops/{id} endpoint
        response = client.get(f'/workshops/{new_workshop.WorkshopId}', headers={'Authorization': f'Bearer {FAKE_JWT}'})
        assert response.status_code == 200
        assert response.get_json()['title'] == "New Advanced Workshop"
        assert response.get_json()['capacity'] == 20
        assert response.get_json()['session_datetime'] == '2025-11-15T10:00:00'

    @patch('auth.get_supabase')
    def test_non_admin_cannot_create_workshop(self, mock_get_supabase, client, init_database):
        """
        GIVEN a non-admin user (leader or participant) is authenticated
        WHEN they attempt to create a workshop
        THEN they should receive a 403 Forbidden error.
        """
        # Arrange
        leader_user = db.session.get(Users, 2)
        participant_user = db.session.get(Users, 3)

        # Act & Assert for Workshop Leader
        mock_authed_user(mock_get_supabase, leader_user)
        response_leader = client.post('/workshops', headers={'Authorization': f'Bearer {FAKE_JWT}'},
                                      data=json.dumps(self.good_workshop_data), content_type='application/json')
        assert response_leader.status_code == 403

        # Act & Assert for Participant
        mock_authed_user(mock_get_supabase, participant_user)
        response_participant = client.post('/workshops', headers={'Authorization': f'Bearer {FAKE_JWT}'},
                                           data=json.dumps(self.good_workshop_data), content_type='application/json')
        assert response_participant.status_code == 403

    @patch('auth.get_supabase')
    def test_create_workshop_with_invalid_data(self, mock_get_supabase, client, init_database):
        """
        GIVEN an admin user is authenticated
        WHEN they send a POST request with invalid or missing data
        THEN they should receive a 400 Bad Request error.
        """
        admin_user = db.session.get(Users, 1)
        mock_authed_user(mock_get_supabase, admin_user)

        invalid_payloads = [
            ({}, "data"),  # Empty payload
            ({"title": "Incomplete"}, "required fields"),  # Missing fields
            ({"title": "", "session_datetime": "2025-11-15T09:00:00",
              "duration_min": 180, "capacity": 20}, "non-empty string"),
            ({"title": "Bad Date", "session_datetime": "15-11-2025T09:00:00", "duration_min": 180,
              "capacity": 20}, "ISO"),
            ({"title": "Bad Duration", "session_datetime": "2025-11-15T09:00:00", "duration_min": -10,
              "capacity": 20}, "positive integer"),
            ({"title": "Bad Capacity", "session_datetime": "2025-11-15T09:00:00", "duration_min": 180,
              "capacity": "twenty"}, "non-negative integer"),
        ]

        for payload, error_message in invalid_payloads:
            response = client.post('/workshops', headers={'Authorization': f'Bearer {FAKE_JWT}'},
                                   data=json.dumps(payload), content_type='application/json')
            assert response.status_code == 400, f"Failed for payload: {payload}"
            assert error_message in response.get_json()['message'], f"Failed for payload: {payload}"


class TestUserProfile:
    """Tests the user profile endpoint."""

    @patch('auth.get_supabase')
    def test_get_user_profile_details(self, mock_get_supabase, client, init_database):
        """
        GIVEN a user is authenticated and has registrations and skills
        WHEN they request their profile
        THEN the profile should contain correct workshop and skill information.
        """
        # Arrange: Authenticate as the participant user
        participant = db.session.get(Users, 3)
        mock_authed_user(mock_get_supabase, participant)

        # Act: Call the user profile endpoint
        response = client.get('/user/profile', headers={'Authorization': f'Bearer {FAKE_JWT}'})

        # Assert
        assert response.status_code == 200
        profile_data = response.get_json()

        # Check basic user info
        assert profile_data['UserId'] == participant.UserId
        assert profile_data['Email'] == 'participant1@test.com'

        # Check workshops
        assert 'workshops' in profile_data
        assert profile_data['workshops']['registered'] == [1, 3]
        assert profile_data['workshops']['waitlisted'] == [2]

        # Check skills
        assert 'skills' in profile_data
        assert len(profile_data['skills']) == 1
        skill_data = profile_data['skills'][0]
        assert skill_data['name'] == 'python'
        assert skill_data['grade'] == 1
        assert isinstance(skill_data['id'], int)


class TestWorkshopRegistration:
    """Tests for user registration logic (signup, cancel, conflicts)."""

    @patch('auth.get_supabase')
    def test_cannot_register_for_overlapping_workshop(self, mock_get_supabase, client, init_database):
        """
        GIVEN a user is registered for a workshop from 09:00-10:30
        WHEN they try to register for another workshop from 10:00-11:00 on the same day
        THEN they should receive a 409 Conflict error.
        """
        # Arrange
        # This user is registered for workshop1 (09:00-10:30 UTC)
        participant = db.session.get(Users, 3)
        mock_authed_user(mock_get_supabase, participant)

        # Create an overlapping workshop in the database
        # workshop1 ends at 10:30. This one starts at 10:00.
        overlapping_datetime = datetime(2025, 9, 10, 10, 0, tzinfo=timezone.utc)
        overlapping_workshop = Workshop(
            Title="Overlapping Workshop",
            SessionDateTime=overlapping_datetime,
            DurationMin=60,  # 10:00 - 11:00
            MaxCapacity=10
        )
        db.session.add(overlapping_workshop)
        db.session.commit()

        # Act
        response = client.post(
            f'/workshops/{overlapping_workshop.WorkshopId}/register',
            headers={'Authorization': f'Bearer {FAKE_JWT}'}
        )

        # Assert
        assert response.status_code == 409
        data = response.get_json()
        assert data['error'] == 'Conflict'
        assert 'overlaps with another registered workshop' in data['message']
        assert data['conflicting_workshop_id'] == 1  # workshop1

    @patch('auth.get_supabase')
    def test_can_register_for_non_overlapping_workshop(self, mock_get_supabase, client, init_database):
        """
        GIVEN a user is registered for a workshop from 09:00-10:30
        WHEN they try to register for another workshop that starts at 10:30 (back-to-back)
        THEN the registration should be successful.
        """
        # Arrange
        participant = db.session.get(Users, 3)
        mock_authed_user(mock_get_supabase, participant)

        # Create a non-overlapping
        workshop3 = db.session.get(Workshop, 3)
        back_to_back_datetime = workshop3.SessionDateTime + timedelta(minutes=workshop3.DurationMin)

        non_overlapping_workshop = Workshop(
            Title="Some Workshop",
            SessionDateTime=back_to_back_datetime,
            DurationMin=60,
            MaxCapacity=10
        )
        db.session.add(non_overlapping_workshop)
        db.session.commit()

        # Act
        response = client.post(
            f'/workshops/{non_overlapping_workshop.WorkshopId}/register',
            headers={'Authorization': f'Bearer {FAKE_JWT}'}
        )

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'Signed up successfully'

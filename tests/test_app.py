import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        # Arrange
        expected_activity_count = 2  # Based on our fixture

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities_data = response.json()
        assert len(activities_data) == expected_activity_count
        assert "Chess Club" in activities_data
        assert "Programming Class" in activities_data

    def test_get_activities_contains_activity_details(self, client):
        # Arrange
        expected_keys = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        assert response.status_code == 200
        chess_club = activities_data.get("Chess Club")
        assert chess_club is not None
        assert set(chess_club.keys()) == expected_keys
        assert chess_club["max_participants"] == 12
        assert len(chess_club["participants"]) == 2

    def test_get_activities_returns_participant_list(self, client):
        # Arrange
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]

        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        assert response.status_code == 200
        assert activities_data["Chess Club"]["participants"] == expected_participants


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "alice@mergington.edu"
        initial_participants = 2

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify participant was added
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert len(participants) == initial_participants + 1
        assert email in participants

    def test_signup_for_nonexistent_activity(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "alice@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_participant_fails(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_multiple_different_participants(self, client):
        # Arrange
        activity_name = "Programming Class"
        new_participants = ["alice@mergington.edu", "bob@mergington.edu", "charlie@mergington.edu"]
        initial_participants = 2

        # Act
        for email in new_participants:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            # Assert each signup succeeds
            assert response.status_code == 200

        # Assert final participant count
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert len(participants) == initial_participants + len(new_participants)
        for email in new_participants:
            assert email in participants


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_remove_participant_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_participants = 2

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert len(participants) == initial_participants - 1
        assert email not in participants

    def test_remove_participant_from_nonexistent_activity(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "alice@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_remove_nonexistent_participant(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_remove_participant_from_activity_with_remaining_participants(self, client):
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email_to_remove}"
        )

        # Assert
        assert response.status_code == 200
        
        # Verify remaining participant is still there
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert len(participants) == 1
        assert email_to_keep in participants
        assert email_to_remove not in participants

    def test_remove_multiple_participants_sequentially(self, client):
        # Arrange
        activity_name = "Chess Club"
        email1 = "michael@mergington.edu"
        email2 = "daniel@mergington.edu"

        # Act - Remove first participant
        response1 = client.delete(
            f"/activities/{activity_name}/participants/{email1}"
        )
        
        # Assert first removal
        assert response1.status_code == 200
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert len(participants) == 1
        
        # Act - Remove second participant
        response2 = client.delete(
            f"/activities/{activity_name}/participants/{email2}"
        )
        
        # Assert second removal
        assert response2.status_code == 200
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert len(participants) == 0

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestGetActivities:
    def test_get_activities_success(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activities_have_required_fields(self, client):
        """Test that activities contain all required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_have_valid_data_types(self, client):
        """Test that activity data has correct types"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0


class TestSignup:
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball%20Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Basketball Team" in data["message"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_email(self, client):
        """Test that student cannot sign up twice for the same activity"""
        email = "duplicate@mergington.edu"
        activity = "Drama%20Club"
        
        # First signup
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_updates_participant_list(self, client):
        """Test that signup adds participant to activity"""
        email = "newparticipant@mergington.edu"
        activity_name = "Science%20Club"
        
        # Get initial count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Science Club"]["participants"])
        
        # Signup
        response_signup = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response_signup.status_code == 200
        
        # Verify participant was added
        response2 = client.get("/activities")
        new_count = len(response2.json()["Science Club"]["participants"])
        assert new_count == initial_count + 1
        assert email in response2.json()["Science Club"]["participants"]

    def test_signup_with_special_characters(self, client):
        """Test signup with email containing special characters"""
        email = "test+special@mergington.edu"
        activity = "Debate%20Club"
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200


class TestRemoveParticipant:
    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        # First add a participant
        email = "removetest@mergington.edu"
        activity_name = "Soccer%20Club"
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Remove participant
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        assert email in data["message"]

    def test_remove_participant_not_found_activity(self, client):
        """Test removal from non-existent activity"""
        response = client.delete(
            "/activities/NonExistent%20Club/participants/test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_remove_participant_not_signed_up(self, client):
        """Test removal of participant who isn't signed up"""
        response = client.delete(
            "/activities/Chess%20Club/participants/notregistered@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_remove_participant_updates_list(self, client):
        """Test that removal updates the participant list"""
        email = "testremove@mergington.edu"
        activity_name = "Art%20Club"
        
        # First ensure someone is signed up to remove
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify they're added
        response1 = client.get("/activities")
        assert email in response1.json()["Art Club"]["participants"]
        
        # Remove
        response_delete = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert response_delete.status_code == 200
        
        # Verify they're removed
        response2 = client.get("/activities")
        assert email not in response2.json()["Art Club"]["participants"]

    def test_remove_participant_twice(self, client):
        """Test that removing same participant twice returns error"""
        email = "doubleremove@mergington.edu"
        activity = "Basketball%20Team"
        
        # Add and remove participant
        client.post(f"/activities/{activity}/signup?email={email}")
        response1 = client.delete(f"/activities/{activity}/participants/{email}")
        assert response1.status_code == 200
        
        # Try to remove again
        response2 = client.delete(f"/activities/{activity}/participants/{email}")
        assert response2.status_code == 404


class TestIntegration:
    def test_full_signup_and_removal_flow(self, client):
        """Test complete flow: get activities, signup, view changes, remove, verify"""
        email = "integration@mergington.edu"
        activity_name = "Programming%20Class"
        
        # Step 1: Get initial state
        response1 = client.get("/activities")
        initial_participants = response1.json()["Programming Class"]["participants"].copy()
        
        # Step 2: Sign up
        response2 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response2.status_code == 200
        
        # Step 3: Verify signup in activities list
        response3 = client.get("/activities")
        assert email in response3.json()["Programming Class"]["participants"]
        assert len(response3.json()["Programming Class"]["participants"]) == len(initial_participants) + 1
        
        # Step 4: Remove participant
        response4 = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert response4.status_code == 200
        
        # Step 5: Verify removal
        response5 = client.get("/activities")
        assert email not in response5.json()["Programming Class"]["participants"]
        assert len(response5.json()["Programming Class"]["participants"]) == len(initial_participants)

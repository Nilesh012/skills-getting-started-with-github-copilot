from copy import deepcopy

from src.app import activities


def test_root_redirects_to_static_application(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_seeded_activities(client):
    # Arrange
    expected_activity_names = {
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Soccer Club",
        "Basketball Club",
        "Art Club",
        "Drama Club",
        "Debate Club",
        "Science Olympiad",
    }
    expected_fields = {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    response_activities = response.json()
    assert set(response_activities) == expected_activity_names
    assert all(
        set(activity) == expected_fields
        for activity in response_activities.values()
    )
    assert response_activities["Chess Club"] == {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": [
            "michael@mergington.edu",
            "daniel@mergington.edu",
        ],
    }


def test_signup_adds_participant_to_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    original_participant_count = len(activities[activity_name]["participants"])

    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert activities_response.status_code == 200
    participants = activities_response.json()[activity_name]["participants"]
    assert len(participants) == original_participant_count + 1
    assert email in participants


def test_signup_rejects_unknown_activity(client):
    # Arrange
    original_activities = deepcopy(activities)

    # Act
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "new.student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities == original_activities


def test_signup_requires_email(client):
    # Arrange
    activity_name = "Chess Club"
    original_activity = deepcopy(activities[activity_name])

    # Act
    response = client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422
    assert activities[activity_name] == original_activity


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    original_activity = deepcopy(activities[activity_name])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activities[activity_name] == original_activity


def test_signup_rejects_full_activity(client):
    # Arrange
    activity_name = "Chess Club"
    activity = activities[activity_name]
    activity["participants"] = [
        f"student{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]
    original_activity = deepcopy(activity)

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "extra.student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}
    assert activities[activity_name] == original_activity

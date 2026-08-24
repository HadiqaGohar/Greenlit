"""
Tests for Version Control API Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestVersionControlEndpoints:
    """Test cases for version control API endpoints"""

    def test_create_version(self):
        """Test creating a new version"""
        response = client.post(
            "/api/versions",
            json={
                "script_id": "test-script-123",
                "content": "INT. OFFICE - DAY\n\nJOHN enters the room.",
                "created_by": "test_user",
                "message": "Test version",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["script_id"] == "test-script-123"
        assert data["version_number"] == 1
        assert data["created_by"] == "test_user"

    def test_get_versions(self):
        """Test getting all versions of a script"""
        # Create a version first
        client.post(
            "/api/versions",
            json={
                "script_id": "test-script-get",
                "content": "Test content",
                "message": "First version",
            },
        )

        response = client.get("/api/versions/test-script-get")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_latest_version(self):
        """Test getting the latest version"""
        # Create multiple versions
        client.post(
            "/api/versions",
            json={
                "script_id": "test-script-latest",
                "content": "First version",
                "message": "v1",
            },
        )
        client.post(
            "/api/versions",
            json={
                "script_id": "test-script-latest",
                "content": "Second version",
                "message": "v2",
            },
        )

        response = client.get("/api/versions/test-script-latest/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["version_number"] == 2
        assert data["content"] == "Second version"

    def test_get_version_stats(self):
        """Test getting version statistics"""
        # Create some versions
        client.post(
            "/api/versions",
            json={
                "script_id": "test-script-stats",
                "content": "Content one",
                "created_by": "user1",
            },
        )
        client.post(
            "/api/versions",
            json={
                "script_id": "test-script-stats",
                "content": "Content two",
                "created_by": "user2",
            },
        )

        response = client.get("/api/versions/test-script-stats/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_versions"] == 2
        assert data["total_edits"] == 1
        assert "user1" in data["contributors"]
        assert "user2" in data["contributors"]

    def test_create_version_invalid_data(self):
        """Test creating version with missing required fields"""
        response = client.post(
            "/api/versions",
            json={
                "content": "Missing script_id",
            },
        )

        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

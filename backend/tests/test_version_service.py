"""
Tests for Version Control Service
"""

import pytest
from app.services.version_service import VersionService, ScriptVersion


class TestVersionService:
    """Test cases for VersionService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = VersionService()
        self.script_id = "test-script-123"

    def test_create_version(self):
        """Test creating a new version"""
        version = self.service.create_version(
            script_id=self.script_id,
            content="INT. OFFICE - DAY\n\nJOHN enters.",
            message="Initial version",
        )

        assert version is not None
        assert version.script_id == self.script_id
        assert version.version_number == 1
        assert version.message == "Initial version"
        assert version.word_count == 6
        assert version.line_count == 3

    def test_create_multiple_versions(self):
        """Test creating multiple versions"""
        self.service.create_version(self.script_id, "Version 1 content", message="v1")
        v2 = self.service.create_version(self.script_id, "Version 2 content", message="v2")
        v3 = self.service.create_version(self.script_id, "Version 3 content", message="v3")

        assert v2.version_number == 2
        assert v3.version_number == 3

        versions = self.service.get_versions(self.script_id)
        assert len(versions) == 3

    def test_get_versions(self):
        """Test getting all versions"""
        self.service.create_version(self.script_id, "Content 1")
        self.service.create_version(self.script_id, "Content 2")

        versions = self.service.get_versions(self.script_id)
        assert len(versions) == 2
        assert versions[0].version_number == 1
        assert versions[1].version_number == 2

    def test_get_latest_version(self):
        """Test getting latest version"""
        self.service.create_version(self.script_id, "First")
        self.service.create_version(self.script_id, "Second")
        latest = self.service.create_version(self.script_id, "Third")

        result = self.service.get_latest_version(self.script_id)
        assert result is not None
        assert result.version_number == 3
        assert result.content == "Third"

    def test_get_nonexistent_version(self):
        """Test getting version that doesn't exist"""
        result = self.service.get_version(self.script_id, "nonexistent-id")
        assert result is None

    def test_rollback_to_version(self):
        """Test rolling back to a previous version"""
        v1 = self.service.create_version(self.script_id, "Original content")
        self.service.create_version(self.script_id, "Modified content")

        rolled_back = self.service.rollback_to_version(self.script_id, v1.id)

        assert rolled_back is not None
        assert rolled_back.version_number == 3
        assert rolled_back.content == "Original content"
        assert "Rollback" in rolled_back.message

    def test_compute_diff(self):
        """Test computing diff between versions"""
        v1 = self.service.create_version(
            self.script_id, "Line 1\nLine 2\nLine 3"
        )
        v2 = self.service.create_version(
            self.script_id, "Line 1\nModified Line 2\nLine 3\nNew Line 4"
        )

        diff_result = self.service.compute_diff(self.script_id, v1.id, v2.id)

        assert "diff" in diff_result
        assert diff_result["added_lines"] >= 1
        assert diff_result["removed_lines"] >= 0
        assert 0 <= diff_result["similarity_percentage"] <= 100

    def test_version_stats(self):
        """Test getting version statistics"""
        self.service.create_version(self.script_id, "Content 1", created_by="user1")
        self.service.create_version(self.script_id, "Content 2", created_by="user2")

        stats = self.service.get_version_stats(self.script_id)

        assert stats["total_versions"] == 2
        assert stats["total_edits"] == 1
        assert "user1" in stats["contributors"]
        assert "user2" in stats["contributors"]
        assert stats["average_word_count"] > 0

    def test_empty_script_stats(self):
        """Test stats for script with no versions"""
        stats = self.service.get_version_stats("nonexistent-script")

        assert stats["total_versions"] == 0
        assert stats["total_edits"] == 0
        assert stats["contributors"] == []


class TestScriptVersion:
    """Test cases for ScriptVersion model"""

    def test_version_creation(self):
        """Test ScriptVersion initialization"""
        version = ScriptVersion(
            script_id="script-123",
            content="Test content here",
            version_number=1,
            created_by="test_user",
            message="Test message",
        )

        assert version.script_id == "script-123"
        assert version.content == "Test content here"
        assert version.version_number == 1
        assert version.created_by == "test_user"
        assert version.message == "Test message"
        assert version.word_count == 3
        assert version.line_count == 1
        assert version.id is not None

    def test_version_word_count(self):
        """Test word count calculation"""
        version = ScriptVersion(
            script_id="script-123",
            content="This is a test with multiple words",
            version_number=1,
        )

        assert version.word_count == 7

    def test_version_line_count(self):
        """Test line count calculation"""
        version = ScriptVersion(
            script_id="script-123",
            content="Line 1\nLine 2\nLine 3",
            version_number=1,
        )

        assert version.line_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

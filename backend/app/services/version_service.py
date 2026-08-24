"""
Version Control Service - Manages script versions and diffs
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4
import difflib

logger = logging.getLogger(__name__)


class ScriptVersion:
    """Represents a single version of a script"""
    
    def __init__(
        self,
        script_id: str,
        content: str,
        version_number: int,
        created_by: str = "user",
        message: str = "",
    ):
        self.id = str(uuid4())
        self.script_id = script_id
        self.content = content
        self.version_number = version_number
        self.created_by = created_by
        self.message = message
        self.created_at = datetime.now(timezone.utc)
        self.word_count = len(content.split())
        self.line_count = len(content.splitlines())


class VersionService:
    """Service for managing script versions"""
    
    def __init__(self):
        # In-memory storage for demo (would be database in production)
        self.versions: Dict[str, List[ScriptVersion]] = {}
    
    def create_version(
        self,
        script_id: str,
        content: str,
        created_by: str = "user",
        message: str = "",
    ) -> ScriptVersion:
        """Create a new version of a script"""
        if script_id not in self.versions:
            self.versions[script_id] = []
        
        version_number = len(self.versions[script_id]) + 1
        
        version = ScriptVersion(
            script_id=script_id,
            content=content,
            version_number=version_number,
            created_by=created_by,
            message=message or f"Version {version_number}",
        )
        
        self.versions[script_id].append(version)
        logger.info(f"Created version {version_number} for script {script_id}")
        
        return version
    
    def get_versions(self, script_id: str) -> List[ScriptVersion]:
        """Get all versions of a script"""
        return self.versions.get(script_id, [])
    
    def get_version(self, script_id: str, version_id: str) -> Optional[ScriptVersion]:
        """Get a specific version"""
        versions = self.versions.get(script_id, [])
        for v in versions:
            if v.id == version_id:
                return v
        return None
    
    def get_latest_version(self, script_id: str) -> Optional[ScriptVersion]:
        """Get the latest version of a script"""
        versions = self.versions.get(script_id, [])
        return versions[-1] if versions else None
    
    def rollback_to_version(
        self, script_id: str, version_id: str
    ) -> Optional[ScriptVersion]:
        """Rollback to a previous version (creates new version with old content)"""
        target_version = self.get_version(script_id, version_id)
        if not target_version:
            return None
        
        # Create new version with the old content
        new_version = self.create_version(
            script_id=script_id,
            content=target_version.content,
            created_by="system",
            message=f"Rollback to version {target_version.version_number}",
        )
        
        logger.info(
            f"Rolled back script {script_id} to version {target_version.version_number}"
        )
        return new_version
    
    def compute_diff(
        self, script_id: str, version_id_1: str, version_id_2: str
    ) -> Dict[str, Any]:
        """Compute diff between two versions"""
        v1 = self.get_version(script_id, version_id_1)
        v2 = self.get_version(script_id, version_id_2)
        
        if not v1 or not v2:
            return {"error": "Version not found"}
        
        # Compute unified diff
        diff = list(
            difflib.unified_diff(
                v1.content.splitlines(keepends=True),
                v2.content.splitlines(keepends=True),
                fromfile=f"Version {v1.version_number}",
                tofile=f"Version {v2.version_number}",
                lineterm="",
            )
        )
        
        # Compute stats
        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
        
        # Compute similarity ratio
        matcher = difflib.SequenceMatcher(None, v1.content, v2.content)
        similarity = matcher.ratio() * 100
        
        return {
            "diff": "\n".join(diff),
            "added_lines": added,
            "removed_lines": removed,
            "similarity_percentage": round(similarity, 1),
            "version_1": {
                "id": v1.id,
                "number": v1.version_number,
                "word_count": v1.word_count,
                "created_at": v1.created_at.isoformat(),
            },
            "version_2": {
                "id": v2.id,
                "number": v2.version_number,
                "word_count": v2.word_count,
                "created_at": v2.created_at.isoformat(),
            },
        }
    
    def get_version_stats(self, script_id: str) -> Dict[str, Any]:
        """Get statistics about script versions"""
        versions = self.versions.get(script_id, [])
        
        if not versions:
            return {
                "total_versions": 0,
                "total_edits": 0,
                "contributors": [],
            }
        
        # Calculate stats
        contributors = list(set(v.created_by for v in versions))
        word_counts = [v.word_count for v in versions]
        
        return {
            "total_versions": len(versions),
            "total_edits": len(versions) - 1,
            "contributors": contributors,
            "first_version": versions[0].created_at.isoformat(),
            "last_version": versions[-1].created_at.isoformat(),
            "average_word_count": round(sum(word_counts) / len(word_counts)) if word_counts else 0,
            "word_count_change": word_counts[-1] - word_counts[0] if len(word_counts) > 1 else 0,
        }


# Global instance
version_service = VersionService()

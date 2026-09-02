"""
Version Control Router - API endpoints for script version management
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from ..services.version_service import version_service

router = APIRouter()


class CreateVersionRequest(BaseModel):
    script_id: str
    content: str
    created_by: str = "user"
    message: str = ""


class VersionResponse(BaseModel):
    id: str
    script_id: str
    version_number: int
    created_by: str
    message: str
    created_at: str
    word_count: int
    line_count: int
    content: Optional[str] = None


class DiffResponse(BaseModel):
    diff: str
    added_lines: int
    removed_lines: int
    similarity_percentage: float
    version_1: dict
    version_2: dict


class VersionStatsResponse(BaseModel):
    total_versions: int
    total_edits: int
    contributors: List[str]
    first_version: Optional[str] = None
    last_version: Optional[str] = None
    average_word_count: int = 0
    word_count_change: int = 0


@router.post("/versions", response_model=VersionResponse)
async def create_version(request: CreateVersionRequest):
    """Create a new version of a script"""
    try:
        version = version_service.create_version(
            script_id=request.script_id,
            content=request.content,
            created_by=request.created_by,
            message=request.message,
        )
        
        return VersionResponse(
            id=version.id,
            script_id=version.script_id,
            version_number=version.version_number,
            created_by=version.created_by,
            message=version.message,
            created_at=version.created_at.isoformat(),
            word_count=version.word_count,
            line_count=version.line_count,
            content=version.content,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")


@router.get("/versions/{script_id}", response_model=List[VersionResponse])
async def get_versions(script_id: str):
    """Get all versions of a script"""
    try:
        versions = version_service.get_versions(script_id)
        
        return [
            VersionResponse(
                id=v.id,
                script_id=v.script_id,
                version_number=v.version_number,
                created_by=v.created_by,
                message=v.message,
                created_at=v.created_at.isoformat(),
                word_count=v.word_count,
                line_count=v.line_count,
                content=v.content,
            )
            for v in versions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")


@router.get("/versions/{script_id}/latest", response_model=VersionResponse)
async def get_latest_version(script_id: str):
    """Get the latest version of a script"""
    try:
        version = version_service.get_latest_version(script_id)
        if not version:
            raise HTTPException(status_code=404, detail="No versions found")
        
        return VersionResponse(
            id=version.id,
            script_id=version.script_id,
            version_number=version.version_number,
            created_by=version.created_by,
            message=version.message,
            created_at=version.created_at.isoformat(),
            word_count=version.word_count,
            line_count=version.line_count,
            content=version.content,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest version: {str(e)}")


@router.get("/versions/{script_id}/diff")
async def get_diff(
    script_id: str,
    version_1: str = Query(..., description="First version ID"),
    version_2: str = Query(..., description="Second version ID"),
):
    """Compute diff between two versions"""
    try:
        diff = version_service.compute_diff(script_id, version_1, version_2)
        
        if "error" in diff:
            raise HTTPException(status_code=404, detail=diff["error"])
        
        return diff
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute diff: {str(e)}")


@router.post("/versions/{script_id}/rollback/{version_id}", response_model=VersionResponse)
async def rollback_version(script_id: str, version_id: str):
    """Rollback to a previous version"""
    try:
        version = version_service.rollback_to_version(script_id, version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return VersionResponse(
            id=version.id,
            script_id=version.script_id,
            version_number=version.version_number,
            created_by=version.created_by,
            message=version.message,
            created_at=version.created_at.isoformat(),
            word_count=version.word_count,
            line_count=version.line_count,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rollback: {str(e)}")


@router.get("/versions/{script_id}/stats", response_model=VersionStatsResponse)
async def get_version_stats(script_id: str):
    """Get version statistics for a script"""
    try:
        stats = version_service.get_version_stats(script_id)
        return VersionStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

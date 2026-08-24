"""
Collaboration API endpoints - WebSocket real-time sync and REST CRUD
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import Comment, TeamMember, ReviewStatus, Notification, Script
from ..models.production_schemas import (
    CommentRequest, TeamInviteRequest, CollaborationResponse,
    Comment as CommentSchema, TeamMember as TeamMemberSchema,
    ReviewStatus as ReviewStatusSchema, ProductionRole
)
from ..services.websocket_manager import connection_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── WebSocket endpoint ───────────────────────────────────────────────────────

@router.websocket("/ws/{script_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    script_id: str,
    user_id: str = Query(...),
    user_name: str = Query(...),
):
    """WebSocket endpoint for real-time collaboration on a script"""
    room_id = f"script:{script_id}"
    await connection_manager.connect(websocket, room_id, user_id, user_name)

    # Notify room about new member
    await connection_manager.broadcast_to_room(
        {
            "type": "user_joined",
            "user_id": user_id,
            "user_name": user_name,
            "members": connection_manager.get_room_members(room_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        room_id,
        exclude_user=user_id,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "comment_added":
                await connection_manager.broadcast_to_room(
                    {
                        "type": "comment_added",
                        "comment": message.get("comment"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    room_id,
                    exclude_user=user_id,
                )

            elif msg_type == "comment_updated":
                await connection_manager.broadcast_to_room(
                    {
                        "type": "comment_updated",
                        "comment": message.get("comment"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    room_id,
                    exclude_user=user_id,
                )

            elif msg_type == "comment_deleted":
                await connection_manager.broadcast_to_room(
                    {
                        "type": "comment_deleted",
                        "comment_id": message.get("comment_id"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    room_id,
                    exclude_user=user_id,
                )

            elif msg_type == "issue_resolved":
                await connection_manager.broadcast_to_room(
                    {
                        "type": "issue_resolved",
                        "comment_id": message.get("comment_id"),
                        "resolved_by": user_name,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    room_id,
                    exclude_user=user_id,
                )

            elif msg_type == "review_status_changed":
                await connection_manager.broadcast_to_room(
                    {
                        "type": "review_status_changed",
                        "review": message.get("review"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    room_id,
                    exclude_user=user_id,
                )

            elif msg_type == "cursor_position":
                await connection_manager.broadcast_to_room(
                    {
                        "type": "cursor_position",
                        "user_id": user_id,
                        "user_name": user_name,
                        "position": message.get("position"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    room_id,
                    exclude_user=user_id,
                )

            elif msg_type == "typing":
                await connection_manager.broadcast_to_room(
                    {
                        "type": "typing",
                        "user_id": user_id,
                        "user_name": user_name,
                        "is_typing": message.get("is_typing", False),
                    },
                    room_id,
                    exclude_user=user_id,
                )

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, room_id, user_id)
        await connection_manager.broadcast_to_room(
            {
                "type": "user_left",
                "user_id": user_id,
                "user_name": user_name,
                "members": connection_manager.get_room_members(room_id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            room_id,
        )
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket, room_id, user_id)


# ─── Comment CRUD endpoints ───────────────────────────────────────────────────

@router.get("/scripts/{script_id}/comments", response_model=List[CommentSchema])
async def get_comments(
    script_id: str,
    claim_id: Optional[str] = Query(None),
    scene_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get all comments for a script, optionally filtered by claim or scene"""
    query = db.query(Comment).filter(Comment.script_id == script_id)
    if claim_id:
        query = query.filter(Comment.claim_id == claim_id)
    if scene_id:
        query = query.filter(Comment.scene_id == scene_id)
    comments = query.order_by(Comment.created_at.asc()).all()
    return [
        CommentSchema(
            id=str(c.id),
            report_id=str(c.script_id),
            claim_id=str(c.claim_id) if c.claim_id else None,
            scene_id=str(c.scene_id) if c.scene_id else None,
            user_id=str(c.user_id),
            user_name=c.user_name,
            user_role=c.user_role,
            content=c.content,
            parent_id=str(c.parent_id) if c.parent_id else None,
            resolved=c.resolved,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in comments
    ]


@router.post("/scripts/{script_id}/comments", response_model=CommentSchema)
async def create_comment(
    script_id: str,
    request: CommentRequest,
    user_id: str = Query(...),
    user_name: str = Query(...),
    user_role: str = Query("researcher"),
    db: Session = Depends(get_db),
):
    """Create a new comment on a script"""
    comment = Comment(
        id=uuid4(),
        script_id=script_id,
        claim_id=request.claim_id,
        scene_id=request.scene_id,
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        content=request.content,
        parent_id=request.parent_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Broadcast via WebSocket
    room_id = f"script:{script_id}"
    comment_data = {
        "id": str(comment.id),
        "report_id": str(comment.script_id),
        "claim_id": str(comment.claim_id) if comment.claim_id else None,
        "scene_id": str(comment.scene_id) if comment.scene_id else None,
        "user_id": str(comment.user_id),
        "user_name": comment.user_name,
        "user_role": comment.user_role,
        "content": comment.content,
        "parent_id": str(comment.parent_id) if comment.parent_id else None,
        "resolved": comment.resolved,
        "created_at": comment.created_at.isoformat(),
        "updated_at": comment.updated_at.isoformat(),
    }
    await connection_manager.broadcast_to_room(
        {"type": "comment_added", "comment": comment_data, "timestamp": datetime.now(timezone.utc).isoformat()},
        room_id,
        exclude_user=user_id,
    )

    # Create notification for other team members
    await _notify_team_members(
        db=db,
        script_id=script_id,
        exclude_user_id=user_id,
        notification_type="comment_added",
        title=f"{user_name} added a comment",
        message=request.content[:100],
        script_id_for_notif=script_id,
    )

    return CommentSchema(
        id=str(comment.id),
        report_id=str(comment.script_id),
        claim_id=str(comment.claim_id) if comment.claim_id else None,
        scene_id=str(comment.scene_id) if comment.scene_id else None,
        user_id=str(comment.user_id),
        user_name=comment.user_name,
        user_role=comment.user_role,
        content=comment.content,
        parent_id=str(comment.parent_id) if comment.parent_id else None,
        resolved=comment.resolved,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.put("/comments/{comment_id}", response_model=CommentSchema)
async def update_comment(
    comment_id: str,
    content: str,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Update an existing comment"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if str(comment.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")

    comment.content = content
    comment.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(comment)

    # Broadcast update
    room_id = f"script:{comment.script_id}"
    comment_data = {
        "id": str(comment.id),
        "report_id": str(comment.script_id),
        "claim_id": str(comment.claim_id) if comment.claim_id else None,
        "scene_id": str(comment.scene_id) if comment.scene_id else None,
        "user_id": str(comment.user_id),
        "user_name": comment.user_name,
        "user_role": comment.user_role,
        "content": comment.content,
        "parent_id": str(comment.parent_id) if comment.parent_id else None,
        "resolved": comment.resolved,
        "created_at": comment.created_at.isoformat(),
        "updated_at": comment.updated_at.isoformat(),
    }
    await connection_manager.broadcast_to_room(
        {"type": "comment_updated", "comment": comment_data, "timestamp": datetime.now(timezone.utc).isoformat()},
        room_id,
    )

    return CommentSchema(
        id=str(comment.id),
        report_id=str(comment.script_id),
        claim_id=str(comment.claim_id) if comment.claim_id else None,
        scene_id=str(comment.scene_id) if comment.scene_id else None,
        user_id=str(comment.user_id),
        user_name=comment.user_name,
        user_role=comment.user_role,
        content=comment.content,
        parent_id=str(comment.parent_id) if comment.parent_id else None,
        resolved=comment.resolved,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Delete a comment"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if str(comment.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    script_id = str(comment.script_id)
    db.delete(comment)
    db.commit()

    # Broadcast deletion
    room_id = f"script:{script_id}"
    await connection_manager.broadcast_to_room(
        {"type": "comment_deleted", "comment_id": comment_id, "timestamp": datetime.now(timezone.utc).isoformat()},
        room_id,
    )

    return {"message": "Comment deleted"}


@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: str,
    user_id: str = Query(...),
    user_name: str = Query(...),
    db: Session = Depends(get_db),
):
    """Mark a comment/issue as resolved"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.resolved = True
    comment.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Broadcast resolution
    room_id = f"script:{comment.script_id}"
    await connection_manager.broadcast_to_room(
        {
            "type": "issue_resolved",
            "comment_id": comment_id,
            "resolved_by": user_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        room_id,
    )

    # Check if all critical issues are resolved -> update script status
    await _check_auto_status_update(db, str(comment.script_id))

    return {"message": "Issue resolved"}


# ─── Team management endpoints ────────────────────────────────────────────────

@router.get("/scripts/{script_id}/team", response_model=List[TeamMemberSchema])
async def get_team_members(
    script_id: str,
    db: Session = Depends(get_db),
):
    """Get all team members for a script"""
    members = db.query(TeamMember).filter(TeamMember.script_id == script_id).all()
    return [
        TeamMemberSchema(
            id=str(m.id),
            user_id=str(m.user_id),
            script_id=str(m.script_id),
            role=m.role,
            permissions=m.permissions or [],
            added_at=m.added_at,
        )
        for m in members
    ]


@router.post("/scripts/{script_id}/team/invite", response_model=TeamMemberSchema)
async def invite_team_member(
    script_id: str,
    request: TeamInviteRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Invite a team member to a script project"""
    # Check if already a member
    existing = (
        db.query(TeamMember)
        .filter(TeamMember.script_id == script_id, TeamMember.user_id == user_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User is already a team member")

    member = TeamMember(
        id=uuid4(),
        user_id=user_id,
        script_id=script_id,
        role=request.role.value,
        permissions=request.permissions,
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    # Broadcast new member
    room_id = f"script:{script_id}"
    await connection_manager.broadcast_to_room(
        {
            "type": "team_member_added",
            "member": {
                "id": str(member.id),
                "user_id": str(member.user_id),
                "role": member.role,
                "permissions": member.permissions,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        room_id,
    )

    return TeamMemberSchema(
        id=str(member.id),
        user_id=str(member.user_id),
        script_id=str(member.script_id),
        role=member.role,
        permissions=member.permissions or [],
        added_at=member.added_at,
    )


@router.delete("/scripts/{script_id}/team/{target_user_id}")
async def remove_team_member(
    script_id: str,
    target_user_id: str,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Remove a team member from a script project"""
    member = (
        db.query(TeamMember)
        .filter(TeamMember.script_id == script_id, TeamMember.user_id == target_user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    db.delete(member)
    db.commit()

    # Broadcast removal
    room_id = f"script:{script_id}"
    await connection_manager.broadcast_to_room(
        {
            "type": "team_member_removed",
            "user_id": target_user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        room_id,
    )

    return {"message": "Team member removed"}


# ─── Review status endpoints ──────────────────────────────────────────────────

@router.get("/scripts/{script_id}/reviews", response_model=List[ReviewStatusSchema])
async def get_reviews(
    script_id: str,
    db: Session = Depends(get_db),
):
    """Get all review statuses for a script"""
    reviews = db.query(ReviewStatus).filter(ReviewStatus.script_id == script_id).all()
    return [
        ReviewStatusSchema(
            id=str(r.id),
            script_id=str(r.script_id),
            reviewer_id=str(r.reviewer_id),
            status=r.status,
            comments=r.comments or "",
            reviewed_at=r.reviewed_at,
        )
        for r in reviews
    ]


@router.post("/scripts/{script_id}/reviews", response_model=ReviewStatusSchema)
async def create_review_request(
    script_id: str,
    reviewer_id: str = Query(...),
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Create a review request for a script"""
    review = ReviewStatus(
        id=uuid4(),
        script_id=script_id,
        reviewer_id=reviewer_id,
        status="pending",
    )
    db.add(review)

    # Update script status to in_review
    script = db.query(Script).filter(Script.id == script_id).first()
    if script:
        script.status = "in_review"

    db.commit()
    db.refresh(review)

    # Broadcast review request
    room_id = f"script:{script_id}"
    await connection_manager.broadcast_to_room(
        {
            "type": "review_requested",
            "review": {
                "id": str(review.id),
                "reviewer_id": str(review.reviewer_id),
                "status": review.status,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        room_id,
    )

    return ReviewStatusSchema(
        id=str(review.id),
        script_id=str(review.script_id),
        reviewer_id=str(review.reviewer_id),
        status=review.status,
        comments=review.comments or "",
        reviewed_at=review.reviewed_at,
    )


@router.put("/reviews/{review_id}", response_model=ReviewStatusSchema)
async def update_review_status(
    review_id: str,
    status: str,
    comments: Optional[str] = None,
    user_id: str = Query(...),
    user_name: str = Query(...),
    db: Session = Depends(get_db),
):
    """Update a review status (approve, reject, needs_changes)"""
    valid_statuses = ["pending", "approved", "rejected", "needs_changes"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    review = db.query(ReviewStatus).filter(ReviewStatus.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.status = status
    review.comments = comments or ""
    review.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(review)

    # Broadcast review update
    room_id = f"script:{review.script_id}"
    await connection_manager.broadcast_to_room(
        {
            "type": "review_status_changed",
            "review": {
                "id": str(review.id),
                "reviewer_id": str(review.reviewer_id),
                "status": review.status,
                "comments": review.comments,
                "reviewed_by": user_name,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        room_id,
    )

    # Check auto status update
    await _check_auto_status_update(db, str(review.script_id))

    return ReviewStatusSchema(
        id=str(review.id),
        script_id=str(review.script_id),
        reviewer_id=str(review.reviewer_id),
        status=review.status,
        comments=review.comments or "",
        reviewed_at=review.reviewed_at,
    )


# ─── Activity feed endpoint ───────────────────────────────────────────────────

@router.get("/scripts/{script_id}/activity")
async def get_activity_feed(
    script_id: str,
    limit: int = Query(20, description="Number of activities to return"),
    db: Session = Depends(get_db),
):
    """Get recent activity feed for a script"""
    activities = []

    # Recent comments
    comments = (
        db.query(Comment)
        .filter(Comment.script_id == script_id)
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .all()
    )
    for c in comments:
        activities.append({
            "type": "comment",
            "user_name": c.user_name,
            "content": c.content[:100],
            "timestamp": c.created_at.isoformat(),
            "resolved": c.resolved,
        })

    # Recent reviews
    reviews = (
        db.query(ReviewStatus)
        .filter(ReviewStatus.script_id == script_id)
        .order_by(ReviewStatus.reviewed_at.desc())
        .limit(limit)
        .all()
    )
    for r in reviews:
        if r.reviewed_at:
            activities.append({
                "type": "review",
                "reviewer_id": str(r.reviewer_id),
                "status": r.status,
                "timestamp": r.reviewed_at.isoformat(),
            })

    # Sort by timestamp descending
    activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"activities": activities[:limit]}


# ─── Online members endpoint ─────────────────────────────────────────────────

@router.get("/scripts/{script_id}/online")
async def get_online_members(script_id: str):
    """Get currently online members in a script's collaboration room"""
    room_id = f"script:{script_id}"
    return {
        "members": connection_manager.get_room_members(room_id),
        "count": connection_manager.get_user_count(room_id),
    }


# ─── Helper functions ─────────────────────────────────────────────────────────

async def _notify_team_members(
    db: Session,
    script_id: str,
    exclude_user_id: str,
    notification_type: str,
    title: str,
    message: str,
    script_id_for_notif: str,
):
    """Create notifications for team members"""
    members = db.query(TeamMember).filter(TeamMember.script_id == script_id).all()
    for member in members:
        if str(member.user_id) == exclude_user_id:
            continue
        notification = Notification(
            id=uuid4(),
            user_id=member.user_id,
            type=notification_type,
            title=title,
            message=message,
            script_id=script_id_for_notif,
        )
        db.add(notification)
    db.commit()


async def _check_auto_status_update(db: Session, script_id: str):
    """Check if all critical issues are resolved and auto-update script status"""
    unresolved_critical = (
        db.query(Comment)
        .filter(
            Comment.script_id == script_id,
            Comment.resolved == False,
        )
        .count()
    )

    if unresolved_critical == 0:
        script = db.query(Script).filter(Script.id == script_id).first()
        if script and script.status != "production_ready":
            script.status = "production_ready"
            db.commit()

            room_id = f"script:{script_id}"
            await connection_manager.broadcast_to_room(
                {
                    "type": "script_status_updated",
                    "status": "production_ready",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                room_id,
            )

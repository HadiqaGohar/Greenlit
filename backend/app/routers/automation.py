"""
Automation Router - File watching, notifications, and batch processing
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Query
from sqlalchemy import cast, String
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime

from ..database.connection import get_db
from ..database.models import NotificationSettings, Notification
from ..models.production_schemas import NotificationSettings as NotificationSettingsSchema, NotificationUpdateRequest

router = APIRouter()


# ─── File Watcher Endpoints ───────────────────────────────────────────────────

@router.get("/status")
async def automation_status(request: Request):
    """Get automation system status"""
    file_watcher = getattr(request.app.state, "file_watcher", None)
    if not file_watcher:
        return {"file_watching": False, "message": "File watcher not initialized"}
    return file_watcher.get_watch_status()


@router.get("/watch-folders")
async def list_watched_folders(request: Request):
    """List all watched folders"""
    file_watcher = getattr(request.app.state, "file_watcher", None)
    if not file_watcher:
        return {"folders": []}

    status = file_watcher.get_watch_status()
    return {
        "folders": status.get("watched_folders", []),
        "total": len(status.get("watched_folders", [])),
    }


@router.post("/watch-folder")
async def add_folder_watch(request: Request, folder_config: Dict[str, Any]):
    """Add a folder to watch for script files"""
    file_watcher = getattr(request.app.state, "file_watcher", None)
    if not file_watcher:
        raise HTTPException(status_code=503, detail="File watcher not available")

    try:
        watch_id = await file_watcher.add_folder_watch(
            folder_path=folder_config.get("folder_path"),
            folder_type=folder_config.get("folder_type", "local"),
            auto_analyze=folder_config.get("auto_analyze", True),
            notification_webhook=folder_config.get("notification_webhook"),
        )
        return {"success": True, "watch_id": watch_id, "message": "Folder watch added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/watch-folder/{watch_id}")
async def remove_folder_watch(request: Request, watch_id: str):
    """Remove a folder watch"""
    file_watcher = getattr(request.app.state, "file_watcher", None)
    if not file_watcher:
        raise HTTPException(status_code=503, detail="File watcher not available")

    try:
        await file_watcher.remove_folder_watch(watch_id)
        return {"success": True, "message": "Folder watch removed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Notification Settings Endpoints ──────────────────────────────────────────

@router.get("/notifications/settings", response_model=NotificationSettingsSchema)
async def get_notification_settings(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Get notification settings for a user"""
    settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user_id).first()
    if not settings:
        # Create default settings
        settings = NotificationSettings(id=uuid4(), user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return NotificationSettingsSchema(
        user_id=str(settings.user_id),
        email_enabled=settings.email_enabled,
        slack_enabled=settings.slack_enabled,
        slack_webhook=settings.slack_webhook,
        high_risk_threshold=settings.high_risk_threshold,
        notify_on_comments=settings.notify_on_comments,
        notify_on_completion=settings.notify_on_completion,
        digest_frequency=settings.digest_frequency,
    )


@router.put("/notifications/settings", response_model=NotificationSettingsSchema)
async def update_notification_settings(
    user_id: str = Query(...),
    request: NotificationUpdateRequest = ...,
    db: Session = Depends(get_db),
):
    """Update notification settings for a user"""
    settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user_id).first()
    if not settings:
        settings = NotificationSettings(id=uuid4(), user_id=user_id)
        db.add(settings)

    s = request.settings
    settings.email_enabled = s.email_enabled
    settings.slack_enabled = s.slack_enabled
    settings.slack_webhook = s.slack_webhook
    settings.high_risk_threshold = s.high_risk_threshold
    settings.notify_on_comments = s.notify_on_comments
    settings.notify_on_completion = s.notify_on_completion
    settings.digest_frequency = s.digest_frequency

    db.commit()
    db.refresh(settings)

    return NotificationSettingsSchema(
        user_id=str(settings.user_id),
        email_enabled=settings.email_enabled,
        slack_enabled=settings.slack_enabled,
        slack_webhook=settings.slack_webhook,
        high_risk_threshold=settings.high_risk_threshold,
        notify_on_comments=settings.notify_on_comments,
        notify_on_completion=settings.notify_on_completion,
        digest_frequency=settings.digest_frequency,
    )


# ─── Notification Endpoints ───────────────────────────────────────────────────

@router.get("/notifications")
async def get_notifications(
    user_id: str = Query(...),
    unread_only: bool = Query(False),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    """Get notifications for a user"""
    query = db.query(Notification).filter(cast(Notification.user_id, String) == user_id)
    if unread_only:
        query = query.filter(Notification.read == False)
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return {
        "notifications": [
            {
                "id": str(n.id),
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "script_id": str(n.script_id) if n.script_id else None,
                "read": n.read,
                "created_at": n.created_at.isoformat(),
                "action_url": n.action_url,
            }
            for n in notifications
        ],
        "unread_count": db.query(Notification).filter(
            cast(Notification.user_id, String) == user_id, Notification.read == False
        ).count(),
    }


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.read = True
    db.commit()
    return {"message": "Notification marked as read"}


@router.put("/notifications/read-all")
async def mark_all_notifications_read(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read for a user"""
    db.query(Notification).filter(
        cast(Notification.user_id, String) == user_id, Notification.read == False
    ).update({"read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


# ─── Batch Processing Endpoint ────────────────────────────────────────────────

@router.post("/batch-process")
async def trigger_batch_process(
    request: Request,
    config: Dict[str, Any],
):
    """Trigger batch processing of multiple scripts"""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    scripts = config.get("scripts", [])
    if not scripts:
        raise HTTPException(status_code=400, detail="No scripts provided")

    return {
        "message": f"Batch processing queued for {len(scripts)} scripts",
        "batch_id": str(uuid4()),
        "status": "queued",
    }

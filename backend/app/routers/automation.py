"""
Automation Router - File watching and batch processing
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

router = APIRouter()


@router.get("/status")
async def automation_status(request: Request):
    """Get automation system status"""
    
    file_watcher = getattr(request.app.state, 'file_watcher', None)
    
    if not file_watcher:
        return {
            "file_watching": False,
            "message": "File watcher not initialized"
        }
    
    return file_watcher.get_watch_status()


@router.post("/watch-folder")
async def add_folder_watch(request: Request, folder_config: Dict[str, Any]):
    """Add a folder to watch for script files"""
    
    file_watcher = getattr(request.app.state, 'file_watcher', None)
    
    if not file_watcher:
        raise HTTPException(status_code=503, detail="File watcher not available")
    
    try:
        watch_id = await file_watcher.add_folder_watch(
            folder_path=folder_config.get("folder_path"),
            folder_type=folder_config.get("folder_type", "local"),
            auto_analyze=folder_config.get("auto_analyze", True),
            notification_webhook=folder_config.get("notification_webhook")
        )
        
        return {
            "success": True,
            "watch_id": watch_id,
            "message": "Folder watch added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
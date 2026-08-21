"""
File Watcher - Monitors Google Drive and local folders for script uploads
Auto-triggers multi-agent analysis when new scripts are detected
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import hashlib
import os
from pathlib import Path

from ..models.agent_schemas import FileWatcherEvent, AgentTask
from ..agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class FileWatcher:
    """
    Automated file monitoring system for script uploads
    Integrates with Google Drive API and local file system
    """
    
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
        self.watched_folders = {}
        self.file_hashes = {}
        self.running = False
        self.check_interval = 30  # seconds
        
    async def start_watching(self):
        """Start the file monitoring loop"""
        
        self.running = True
        logger.info("File watcher started")
        
        while self.running:
            try:
                await self._check_watched_folders()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"File watcher error: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    def stop_watching(self):
        """Stop the file monitoring loop"""
        self.running = False
        logger.info("File watcher stopped")
    
    async def add_folder_watch(
        self, 
        folder_path: str, 
        folder_type: str = "local",
        auto_analyze: bool = True,
        notification_webhook: Optional[str] = None
    ) -> str:
        """
        Add a folder to watch for new script files
        
        Args:
            folder_path: Path to folder (local path or Google Drive folder ID)
            folder_type: "local" or "google_drive"
            auto_analyze: Whether to automatically trigger analysis
            notification_webhook: Optional webhook for notifications
        
        Returns:
            watch_id: Unique identifier for this watch configuration
        """
        
        watch_id = hashlib.md5(f"{folder_path}_{datetime.utcnow()}".encode()).hexdigest()[:12]
        
        watch_config = {
            "watch_id": watch_id,
            "folder_path": folder_path,
            "folder_type": folder_type,
            "auto_analyze": auto_analyze,
            "notification_webhook": notification_webhook,
            "created_at": datetime.utcnow(),
            "last_checked": None,
            "files_processed": 0
        }
        
        self.watched_folders[watch_id] = watch_config
        
        # Initialize file hashes for this folder
        if folder_type == "local":
            await self._initialize_local_folder_hashes(folder_path, watch_id)
        elif folder_type == "google_drive":
            await self._initialize_drive_folder_hashes(folder_path, watch_id)
        
        logger.info(f"Added folder watch: {folder_path} ({folder_type}) -> {watch_id}")
        return watch_id
    
    async def remove_folder_watch(self, watch_id: str) -> bool:
        """Remove a folder from watching"""
        
        if watch_id in self.watched_folders:
            del self.watched_folders[watch_id]
            # Clean up file hashes
            self.file_hashes = {k: v for k, v in self.file_hashes.items() if not k.startswith(watch_id)}
            logger.info(f"Removed folder watch: {watch_id}")
            return True
        
        return False
    
    async def _check_watched_folders(self):
        """Check all watched folders for changes"""
        
        for watch_id, config in self.watched_folders.items():
            try:
                if config["folder_type"] == "local":
                    await self._check_local_folder(watch_id, config)
                elif config["folder_type"] == "google_drive":
                    await self._check_drive_folder(watch_id, config)
                    
                config["last_checked"] = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Error checking folder {watch_id}: {str(e)}")
    
    async def _check_local_folder(self, watch_id: str, config: Dict[str, Any]):
        """Check local folder for new or modified files"""
        
        folder_path = Path(config["folder_path"])
        if not folder_path.exists():
            logger.warning(f"Watched folder does not exist: {folder_path}")
            return
        
        # Supported script file extensions
        script_extensions = {'.txt', '.fountain', '.fdx', '.pdf', '.docx'}
        
        for file_path in folder_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in script_extensions:
                
                file_key = f"{watch_id}_{file_path}"
                current_hash = await self._calculate_file_hash(file_path)
                previous_hash = self.file_hashes.get(file_key)
                
                if previous_hash is None:
                    # New file detected
                    event = FileWatcherEvent(
                        event_type="created",
                        file_path=str(file_path),
                        file_name=file_path.name,
                        file_size=file_path.stat().st_size
                    )
                    
                    await self._handle_file_event(event, config)
                    
                elif current_hash != previous_hash:
                    # Modified file detected
                    event = FileWatcherEvent(
                        event_type="modified",
                        file_path=str(file_path),
                        file_name=file_path.name,
                        file_size=file_path.stat().st_size
                    )
                    
                    await self._handle_file_event(event, config)
                
                # Update hash
                self.file_hashes[file_key] = current_hash
    
    async def _check_drive_folder(self, watch_id: str, config: Dict[str, Any]):
        """Check Google Drive folder for new or modified files"""
        
        # This would integrate with Google Drive API
        # For now, implementing a placeholder that could be connected to Drive API
        
        try:
            # Placeholder for Google Drive API integration
            drive_files = await self._get_drive_files(config["folder_path"])
            
            for drive_file in drive_files:
                file_key = f"{watch_id}_{drive_file['id']}"
                current_hash = drive_file.get('md5Checksum', '')
                previous_hash = self.file_hashes.get(file_key)
                
                if previous_hash is None:
                    # New file in Drive
                    event = FileWatcherEvent(
                        event_type="created",
                        file_path=drive_file['webViewLink'],
                        file_name=drive_file['name'],
                        file_size=int(drive_file.get('size', 0))
                    )
                    
                    await self._handle_file_event(event, config)
                    
                elif current_hash != previous_hash:
                    # Modified file in Drive
                    event = FileWatcherEvent(
                        event_type="modified",
                        file_path=drive_file['webViewLink'],
                        file_name=drive_file['name'],
                        file_size=int(drive_file.get('size', 0))
                    )
                    
                    await self._handle_file_event(event, config)
                
                self.file_hashes[file_key] = current_hash
                
        except Exception as e:
            logger.error(f"Google Drive check failed for {watch_id}: {str(e)}")
    
    async def _handle_file_event(self, event: FileWatcherEvent, config: Dict[str, Any]):
        """Handle a file system event (new/modified file)"""
        
        logger.info(f"File event: {event.event_type} - {event.file_name}")
        
        if not config.get("auto_analyze", True):
            logger.info(f"Auto-analysis disabled for {event.file_name}")
            return
        
        try:
            # Read file content
            script_content = await self._read_file_content(event.file_path)
            
            if not script_content or len(script_content.strip()) < 100:
                logger.warning(f"File too small or empty: {event.file_name}")
                return
            
            # Trigger multi-agent analysis
            logger.info(f"Triggering auto-analysis for: {event.file_name}")
            
            report = await self.orchestrator.analyze_script(
                script_text=script_content,
                options={
                    "priority": "high",  # Auto-triggered files get high priority
                    "context": {
                        "source": "file_watcher",
                        "file_name": event.file_name,
                        "file_path": event.file_path,
                        "event_type": event.event_type,
                        "watch_config": config["watch_id"]
                    }
                }
            )
            
            # Update statistics
            config["files_processed"] = config.get("files_processed", 0) + 1
            
            # Send notification if webhook configured
            if config.get("notification_webhook"):
                await self._send_webhook_notification(
                    webhook_url=config["notification_webhook"],
                    event=event,
                    report=report,
                    config=config
                )
            
            logger.info(f"Auto-analysis completed for {event.file_name}: {report.report_id}")
            
        except Exception as e:
            logger.error(f"Failed to handle file event for {event.file_name}: {str(e)}")
    
    async def _read_file_content(self, file_path: str) -> str:
        """Read content from file (local or Google Drive)"""
        
        if file_path.startswith("http"):
            # Google Drive file - would need to download via Drive API
            return await self._download_drive_file(file_path)
        else:
            # Local file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {str(e)}")
                return ""
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for change detection"""
        
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {str(e)}")
            return ""
    
    async def _initialize_local_folder_hashes(self, folder_path: str, watch_id: str):
        """Initialize file hashes for existing files in local folder"""
        
        folder = Path(folder_path)
        if not folder.exists():
            return
        
        script_extensions = {'.txt', '.fountain', '.fdx', '.pdf', '.docx'}
        
        for file_path in folder.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in script_extensions:
                file_key = f"{watch_id}_{file_path}"
                file_hash = await self._calculate_file_hash(file_path)
                self.file_hashes[file_key] = file_hash
    
    async def _initialize_drive_folder_hashes(self, folder_id: str, watch_id: str):
        """Initialize file hashes for existing files in Google Drive folder"""
        
        try:
            drive_files = await self._get_drive_files(folder_id)
            for drive_file in drive_files:
                file_key = f"{watch_id}_{drive_file['id']}"
                self.file_hashes[file_key] = drive_file.get('md5Checksum', '')
        except Exception as e:
            logger.error(f"Failed to initialize Drive folder hashes: {str(e)}")
    
    async def _get_drive_files(self, folder_id: str) -> List[Dict[str, Any]]:
        """Get files from Google Drive folder"""
        
        # Placeholder for Google Drive API integration
        # This would use the Google Drive API to list files in the specified folder
        
        # For demo purposes, returning empty list
        # In real implementation, this would:
        # 1. Use Google Drive API credentials
        # 2. Query files in the specified folder
        # 3. Filter for script file types
        # 4. Return file metadata including md5Checksum
        
        return []
    
    async def _download_drive_file(self, file_url: str) -> str:
        """Download file content from Google Drive"""
        
        # Placeholder for Google Drive file download
        # This would use Drive API to download file content
        
        return ""
    
    async def _send_webhook_notification(
        self, 
        webhook_url: str, 
        event: FileWatcherEvent, 
        report: Any,
        config: Dict[str, Any]
    ):
        """Send notification webhook about processed file"""
        
        import aiohttp
        
        notification_data = {
            "event_type": "file_processed",
            "file_name": event.file_name,
            "file_event": event.event_type,
            "report_id": report.report_id,
            "risk_score": report.risk_assessment.overall_risk_score,
            "processing_time": report.processing_time,
            "watch_config": config["watch_id"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=notification_data) as response:
                    if response.status == 200:
                        logger.info(f"Webhook notification sent for {event.file_name}")
                    else:
                        logger.warning(f"Webhook failed: {response.status}")
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {str(e)}")
    
    def get_watch_status(self) -> Dict[str, Any]:
        """Get current status of file watching"""
        
        return {
            "running": self.running,
            "watched_folders": len(self.watched_folders),
            "total_files_tracked": len(self.file_hashes),
            "folders": [
                {
                    "watch_id": watch_id,
                    "folder_path": config["folder_path"],
                    "folder_type": config["folder_type"],
                    "files_processed": config.get("files_processed", 0),
                    "last_checked": config.get("last_checked"),
                    "auto_analyze": config.get("auto_analyze", True)
                }
                for watch_id, config in self.watched_folders.items()
            ]
        }
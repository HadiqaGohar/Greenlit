"""
Batch Processor - Handles scene-by-scene script processing
Manages queued analysis and progress tracking
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4

from ..models.agent_schemas import BatchProcessRequest, AgentTask
from ..agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Handles batch processing of script scenes
    Manages queue and progress tracking for multiple scenes
    """
    
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
        self.processing_queue = []
        self.active_jobs = {}
        self.completed_jobs = {}
        
    async def process_batch(self, request: BatchProcessRequest) -> str:
        """
        Process multiple script scenes in batch
        
        Args:
            request: Batch processing request with scenes and options
            
        Returns:
            batch_id: Identifier for tracking batch progress
        """
        
        batch_id = str(uuid4())
        
        batch_job = {
            "batch_id": batch_id,
            "scenes": request.scenes,
            "priority": request.priority,
            "agents_to_run": request.agents_to_run,
            "notification_webhook": request.notification_webhook,
            "auto_export": request.auto_export,
            "created_at": datetime.utcnow(),
            "status": "queued",
            "progress": 0,
            "scene_results": [],
            "total_scenes": len(request.scenes)
        }
        
        self.processing_queue.append(batch_job)
        self.active_jobs[batch_id] = batch_job
        
        # Start processing in background
        asyncio.create_task(self._process_batch_job(batch_job))
        
        logger.info(f"Batch job queued: {batch_id} with {len(request.scenes)} scenes")
        return batch_id
    
    async def _process_batch_job(self, batch_job: Dict[str, Any]):
        """Process a batch job scene by scene"""
        
        batch_id = batch_job["batch_id"]
        scenes = batch_job["scenes"]
        
        try:
            batch_job["status"] = "processing"
            batch_job["started_at"] = datetime.utcnow()
            
            logger.info(f"Starting batch processing: {batch_id}")
            
            for i, scene_text in enumerate(scenes):
                try:
                    # Process individual scene
                    scene_result = await self.orchestrator.analyze_script(
                        script_text=scene_text,
                        options={
                            "priority": batch_job["priority"],
                            "context": {
                                "batch_id": batch_id,
                                "scene_number": i + 1,
                                "total_scenes": len(scenes)
                            }
                        }
                    )
                    
                    batch_job["scene_results"].append({
                        "scene_number": i + 1,
                        "report_id": scene_result.report_id,
                        "risk_score": scene_result.risk_assessment.overall_risk_score,
                        "processing_time": scene_result.processing_time,
                        "status": "completed"
                    })
                    
                    # Update progress
                    batch_job["progress"] = ((i + 1) / len(scenes)) * 100
                    
                    logger.info(f"Scene {i + 1}/{len(scenes)} completed for batch {batch_id}")
                    
                except Exception as e:
                    logger.error(f"Scene {i + 1} failed in batch {batch_id}: {str(e)}")
                    
                    batch_job["scene_results"].append({
                        "scene_number": i + 1,
                        "report_id": None,
                        "error": str(e),
                        "status": "failed"
                    })
            
            # Mark batch as completed
            batch_job["status"] = "completed"
            batch_job["completed_at"] = datetime.utcnow()
            batch_job["progress"] = 100
            
            # Move to completed jobs
            self.completed_jobs[batch_id] = batch_job
            del self.active_jobs[batch_id]
            
            logger.info(f"Batch processing completed: {batch_id}")
            
            # Send notification if configured
            if batch_job.get("notification_webhook"):
                await self._send_batch_completion_notification(batch_job)
                
        except Exception as e:
            logger.error(f"Batch job {batch_id} failed: {str(e)}")
            batch_job["status"] = "failed"
            batch_job["error"] = str(e)
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch job"""
        
        if batch_id in self.active_jobs:
            return self.active_jobs[batch_id]
        elif batch_id in self.completed_jobs:
            return self.completed_jobs[batch_id]
        else:
            # Check processing queue
            for job in self.processing_queue:
                if job["batch_id"] == batch_id:
                    return job
        
        return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        
        return {
            "queued_jobs": len(self.processing_queue),
            "active_jobs": len(self.active_jobs),
            "completed_jobs": len(self.completed_jobs),
            "queue": [
                {
                    "batch_id": job["batch_id"],
                    "scenes": job["total_scenes"],
                    "priority": job["priority"],
                    "status": job["status"],
                    "progress": job.get("progress", 0)
                }
                for job in (list(self.active_jobs.values()) + self.processing_queue)
            ]
        }
    
    async def _send_batch_completion_notification(self, batch_job: Dict[str, Any]):
        """Send notification when batch processing completes"""
        
        try:
            import aiohttp
            
            webhook_url = batch_job["notification_webhook"]
            
            notification_data = {
                "event_type": "batch_completed",
                "batch_id": batch_job["batch_id"],
                "status": batch_job["status"],
                "total_scenes": batch_job["total_scenes"],
                "successful_scenes": len([r for r in batch_job["scene_results"] if r["status"] == "completed"]),
                "failed_scenes": len([r for r in batch_job["scene_results"] if r["status"] == "failed"]),
                "processing_time": (
                    batch_job["completed_at"] - batch_job["started_at"]
                ).total_seconds() if "completed_at" in batch_job else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=notification_data) as response:
                    if response.status == 200:
                        logger.info(f"Batch completion notification sent for {batch_job['batch_id']}")
                    else:
                        logger.warning(f"Batch notification failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send batch completion notification: {str(e)}")
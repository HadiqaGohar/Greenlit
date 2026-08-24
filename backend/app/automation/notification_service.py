"""
Notification Service - Handles automated notifications
Sends alerts via Slack, email, webhooks for high-risk production issues
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import aiohttp

from ..config import settings
from ..models.agent_schemas import NotificationRequest, OrchestratorReport

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Handles automated notifications for production alerts
    Integrates with Slack, email, and custom webhooks
    """
    
    def __init__(self):
        self.slack_webhook = settings.SLACK_WEBHOOK_URL
        self.notifications_enabled = settings.AUTO_NOTIFICATIONS_ENABLED
        
    async def send_high_risk_alert(
        self, 
        report: OrchestratorReport,
        threshold: float = 70.0
    ) -> bool:
        """
        Send alert for high-risk production reports
        
        Args:
            report: Orchestrator report with risk assessment
            threshold: Risk score threshold for alerts
            
        Returns:
            success: Whether notification was sent successfully
        """
        
        if not self.notifications_enabled:
            logger.info("Notifications disabled, skipping alert")
            return False
        
        risk_score = report.risk_assessment.overall_risk_score
        
        if risk_score < threshold:
            logger.debug(f"Risk score {risk_score} below threshold {threshold}")
            return False
        
        try:
            # Prepare alert message
            alert_data = {
                "event_type": "high_risk_production_alert",
                "report_id": report.report_id,
                "risk_score": risk_score,
                "risk_level": report.risk_assessment.risk_level,
                "critical_issues": len(report.risk_assessment.critical_issues),
                "failed_agents": report.failed_agents,
                "timestamp": report.timestamp.isoformat(),
                "urgent": risk_score >= 85.0
            }
            
            # Send Slack notification if configured
            success = False
            if self.slack_webhook:
                success = await self._send_slack_alert(alert_data, report)
            
            # Could add email notifications here
            # success = await self._send_email_alert(alert_data, report) or success
            
            logger.info(f"High-risk alert sent for report {report.report_id}: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to send high-risk alert: {str(e)}")
            return False
    
    async def send_notification(self, request: NotificationRequest) -> bool:
        """
        Send custom notification based on request
        
        Args:
            request: Notification request with details
            
        Returns:
            success: Whether notification was sent
        """
        
        try:
            if request.notification_type == "slack":
                return await self._send_slack_notification(request)
            elif request.notification_type == "email":
                return await self._send_email_notification(request)
            elif request.notification_type == "webhook":
                return await self._send_webhook_notification(request)
            else:
                logger.warning(f"Unknown notification type: {request.notification_type}")
                return False
                
        except Exception as e:
            logger.error(f"Notification failed: {str(e)}")
            return False
    
    async def _send_slack_alert(
        self, 
        alert_data: Dict[str, Any], 
        report: OrchestratorReport
    ) -> bool:
        """Send formatted Slack alert for high-risk reports"""
        
        try:
            # Format Slack message
            risk_emoji = "🚨" if alert_data["urgent"] else "⚠️"
            color = "#ff0000" if alert_data["urgent"] else "#ff9900"
            
            # Build issue summary
            issues_summary = []
            for issue in report.risk_assessment.critical_issues[:3]:  # Top 3 issues
                issues_summary.append(f"• {issue.description}")
            
            slack_payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"{risk_emoji} Production Risk Alert",
                        "fields": [
                            {
                                "title": "Risk Score",
                                "value": f"{alert_data['risk_score']:.1f}/100 ({alert_data['risk_level'].upper()})",
                                "short": True
                            },
                            {
                                "title": "Report ID",
                                "value": alert_data['report_id'][:12] + "...",
                                "short": True
                            },
                            {
                                "title": "Critical Issues",
                                "value": str(alert_data['critical_issues']),
                                "short": True
                            },
                            {
                                "title": "Agent Status",
                                "value": f"✅ {len(report.successful_agents)} / ❌ {len(report.failed_agents)}",
                                "short": True
                            }
                        ],
                        "text": "Top Issues:\n" + "\n".join(issues_summary[:3]) if issues_summary else "Review required",
                        "footer": "Greenlit AI",
                        "ts": int(report.timestamp.timestamp())
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook, json=slack_payload) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Slack alert failed: {str(e)}")
            return False
    
    async def _send_slack_notification(self, request: NotificationRequest) -> bool:
        """Send generic Slack notification"""
        
        if not self.slack_webhook:
            logger.warning("Slack webhook not configured")
            return False
        
        try:
            # Simple Slack message format
            slack_payload = {
                "text": f"🎬 *{request.subject}*\n{request.message}",
                "username": "Greenlit AI"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook, json=slack_payload) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Slack notification failed: {str(e)}")
            return False
    
    async def _send_email_notification(self, request: NotificationRequest) -> bool:
        """Send email notification (placeholder implementation)"""
        
        # This would integrate with an email service (SendGrid, SES, etc.)
        logger.info(f"Email notification: {request.subject} to {request.recipient}")
        
        # For demo purposes, return True (would implement actual email sending)
        return True
    
    async def _send_webhook_notification(self, request: NotificationRequest) -> bool:
        """Send custom webhook notification"""
        
        try:
            webhook_payload = {
                "subject": request.subject,
                "message": request.message,
                "recipient": request.recipient,
                "priority": request.priority,
                "data": request.data or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "greenlit_ai"
            }
            
            # Webhook URL should be in request.recipient for webhook type
            async with aiohttp.ClientSession() as session:
                async with session.post(request.recipient, json=webhook_payload) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Webhook notification failed: {str(e)}")
            return False
    
    async def send_batch_summary(self, batch_results: List[Dict[str, Any]]) -> bool:
        """Send summary notification for batch processing"""
        
        if not self.notifications_enabled or not self.slack_webhook:
            return False
        
        try:
            total_scenes = len(batch_results)
            successful = len([r for r in batch_results if r.get("status") == "completed"])
            failed = total_scenes - successful
            
            avg_risk = sum(r.get("risk_score", 0) for r in batch_results if r.get("risk_score")) / max(total_scenes, 1)
            
            slack_payload = {
                "text": f"📊 *Batch Processing Complete*",
                "attachments": [
                    {
                        "color": "#36a64f" if failed == 0 else "#ff9900",
                        "fields": [
                            {"title": "Total Scenes", "value": str(total_scenes), "short": True},
                            {"title": "Successful", "value": str(successful), "short": True},
                            {"title": "Failed", "value": str(failed), "short": True},
                            {"title": "Avg Risk Score", "value": f"{avg_risk:.1f}", "short": True}
                        ]
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook, json=slack_payload) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Batch summary notification failed: {str(e)}")
            return False


# Singleton instance
_notification_service = None

def get_notification_service() -> NotificationService:
    """Get shared notification service instance"""
    global _notification_service
    
    if _notification_service is None:
        _notification_service = NotificationService()
    
    return _notification_service
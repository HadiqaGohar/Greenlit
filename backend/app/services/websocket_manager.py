"""
WebSocket connection manager for real-time collaboration
"""

import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for room-based real-time collaboration"""

    def __init__(self):
        # room_id -> set of (websocket, user_id, user_name) tuples
        self.active_connections: Dict[str, Set[tuple]] = {}
        # user_id -> websocket (for direct messaging)
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(
        self, websocket: WebSocket, room_id: str, user_id: str, user_name: str
    ):
        """Accept a WebSocket connection and add it to a room"""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add((websocket, user_id, user_name))
        self.user_connections[user_id] = websocket
        logger.info(f"User {user_name} ({user_id}) connected to room {room_id}")

    def disconnect(self, websocket: WebSocket, room_id: str, user_id: str):
        """Remove a WebSocket connection from a room"""
        if room_id in self.active_connections:
            self.active_connections[room_id] = {
                (ws, uid, name)
                for ws, uid, name in self.active_connections[room_id]
                if ws != websocket
            }
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        logger.info(f"User {user_id} disconnected from room {room_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user"""
        websocket = self.user_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception:
                logger.warning(f"Failed to send message to user {user_id}")

    async def broadcast_to_room(self, message: dict, room_id: str, exclude_user: Optional[str] = None):
        """Broadcast a message to all users in a room"""
        if room_id not in self.active_connections:
            return
        disconnected = []
        for websocket, user_id, user_name in self.active_connections[room_id]:
            if user_id == exclude_user:
                continue
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append((websocket, user_id, user_name))
        # Clean up disconnected clients
        for ws, uid, name in disconnected:
            self.disconnect(ws, room_id, uid)

    async def notify_user_in_room(self, room_id: str, user_id: str, message: dict):
        """Send a notification to a specific user in a room"""
        if room_id not in self.active_connections:
            return
        for websocket, uid, user_name in self.active_connections[room_id]:
            if uid == user_id:
                try:
                    await websocket.send_json(message)
                except Exception:
                    pass
                break

    def get_room_members(self, room_id: str) -> list:
        """Get list of members currently in a room"""
        if room_id not in self.active_connections:
            return []
        return [
            {"user_id": uid, "user_name": name}
            for _, uid, name in self.active_connections[room_id]
        ]

    def get_user_count(self, room_id: str) -> int:
        """Get number of users in a room"""
        return len(self.active_connections.get(room_id, set()))

    def is_user_in_room(self, room_id: str, user_id: str) -> bool:
        """Check if a user is currently in a room"""
        if room_id not in self.active_connections:
            return False
        return any(uid == user_id for _, uid, _ in self.active_connections[room_id])


# Global connection manager instance
connection_manager = ConnectionManager()

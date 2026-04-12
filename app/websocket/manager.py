"""
FocuseMate – WebSocket Connection Manager
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections organised by room.
    Handles chat messages, WebRTC signaling, and presence.
    """

    def __init__(self) -> None:
        # room_id -> list of (websocket, user_id) tuples
        self._rooms: Dict[int, List[tuple[WebSocket, int]]] = {}
        # user_id -> set of room_ids (for presence tracking)
        self._user_rooms: Dict[int, Set[int]] = {}

    # ── Connection lifecycle ─────────────────────────────────────

    async def connect(self, websocket: WebSocket, room_id: int, user_id: int) -> None:
        await websocket.accept()
        if room_id not in self._rooms:
            self._rooms[room_id] = []
        self._rooms[room_id].append((websocket, user_id))

        if user_id not in self._user_rooms:
            self._user_rooms[user_id] = set()
        self._user_rooms[user_id].add(room_id)

        logger.info(f"User {user_id} connected to room {room_id}")

        # Notify room about new participant
        await self.broadcast_to_room(
            room_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "room_id": room_id,
            },
            exclude_user=user_id,
        )

    def disconnect(self, websocket: WebSocket, room_id: int, user_id: int) -> None:
        if room_id in self._rooms:
            self._rooms[room_id] = [
                (ws, uid)
                for ws, uid in self._rooms[room_id]
                if ws != websocket
            ]
            if not self._rooms[room_id]:
                del self._rooms[room_id]

        if user_id in self._user_rooms:
            self._user_rooms[user_id].discard(room_id)
            if not self._user_rooms[user_id]:
                del self._user_rooms[user_id]

        logger.info(f"User {user_id} disconnected from room {room_id}")

    # ── Broadcasting ─────────────────────────────────────────────

    async def broadcast_to_room(
        self,
        room_id: int,
        message: dict,
        exclude_user: int | None = None,
    ) -> None:
        """Send a message to all connected users in a room."""
        if room_id not in self._rooms:
            return

        dead_connections = []
        for ws, uid in self._rooms[room_id]:
            if exclude_user and uid == exclude_user:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead_connections.append((ws, uid))

        # Clean up dead connections
        for ws, uid in dead_connections:
            self.disconnect(ws, room_id, uid)

    async def send_to_user(
        self,
        room_id: int,
        target_user_id: int,
        message: dict,
    ) -> None:
        """Send a message to a specific user in a room (used for WebRTC signaling)."""
        if room_id not in self._rooms:
            return

        for ws, uid in self._rooms[room_id]:
            if uid == target_user_id:
                try:
                    await ws.send_json(message)
                except Exception:
                    self.disconnect(ws, room_id, uid)
                return

    # ── Utility ──────────────────────────────────────────────────

    def get_room_users(self, room_id: int) -> list[int]:
        if room_id not in self._rooms:
            return []
        return list({uid for _, uid in self._rooms[room_id]})

    def get_room_count(self, room_id: int) -> int:
        return len(self.get_room_users(room_id))

    def is_user_online(self, user_id: int) -> bool:
        return user_id in self._user_rooms and len(self._user_rooms[user_id]) > 0


# Singleton instance
manager = ConnectionManager()

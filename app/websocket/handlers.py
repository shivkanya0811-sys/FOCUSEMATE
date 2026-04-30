"""
FocuseMate – WebSocket Handlers (Chat + WebRTC Signaling)
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.room_service import get_user_role_in_room

logger = logging.getLogger(__name__)


class RoomConnectionManager:
    def __init__(self):
        # room_id -> {user_id: websocket}
        self.active_connections: dict[int, dict[int, WebSocket]] = defaultdict(dict)
        # room_id -> {user_id: {"user_id": int, "user_name": str}}
        self.participants: dict[int, dict[int, dict]] = defaultdict(dict)

    async def connect(self, websocket: WebSocket, room_id: int, user_id: int, user_name: str):
        await websocket.accept()
        self.active_connections[room_id][user_id] = websocket
        self.participants[room_id][user_id] = {
            "user_id": user_id,
            "user_name": user_name,
        }

    async def disconnect(self, room_id: int, user_id: int):
        self.active_connections.get(room_id, {}).pop(user_id, None)
        self.participants.get(room_id, {}).pop(user_id, None)

        if room_id in self.active_connections and not self.active_connections[room_id]:
            self.active_connections.pop(room_id, None)

        if room_id in self.participants and not self.participants[room_id]:
            self.participants.pop(room_id, None)

    def get_other_participants(self, room_id: int, current_user_id: int) -> list[dict]:
        return [
            info
            for uid, info in self.participants.get(room_id, {}).items()
            if uid != current_user_id
        ]

    async def send_to_user(self, room_id: int, user_id: int, payload: dict):
        ws = self.active_connections.get(room_id, {}).get(user_id)
        if not ws:
            return
        try:
            await ws.send_json(payload)
        except Exception:
            logger.exception("Failed sending WebSocket payload to user %s in room %s", user_id, room_id)

    async def broadcast(self, room_id: int, payload: dict, exclude_user_id: int | None = None):
        room_connections = self.active_connections.get(room_id, {})
        for uid, ws in list(room_connections.items()):
            if exclude_user_id is not None and uid == exclude_user_id:
                continue
            try:
                await ws.send_json(payload)
            except Exception:
                logger.exception("Broadcast failed to user %s in room %s", uid, room_id)


manager = RoomConnectionManager()


async def handle_websocket(websocket: WebSocket, room_id: int, user_id: int, db: AsyncSession):
    # Only room members can connect
    role = await get_user_role_in_room(db, room_id, user_id)
    if not role:
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Join the room first"})
        await websocket.close(code=4003)
        return

    user = await db.get(User, user_id)
    user_name = user.name if user else f"User {user_id}"

    await manager.connect(websocket, room_id, user_id, user_name)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type == "join_webrtc":
                # Tell the new joiner which users are already inside
                await websocket.send_json({
                    "type": "room_users",
                    "participants": manager.get_other_participants(room_id, user_id),
                })

                # Tell existing users someone joined
                await manager.broadcast(
                    room_id,
                    {
                        "type": "participant_joined",
                        "user_id": user_id,
                        "user_name": user_name,
                    },
                    exclude_user_id=user_id,
                )
                continue

            if msg_type == "typing":
                await manager.broadcast(
                    room_id,
                    {
                        "type": "typing",
                        "user_id": user_id,
                        "user_name": user_name,
                        "is_typing": data.get("is_typing", True),
                    },
                    exclude_user_id=user_id,
                )
                continue

            if msg_type == "chat_message":
                payload = {
                    "type": "chat_message",
                    "data": {
                        "id": f"ws-{room_id}-{user_id}",
                        "room_id": room_id,
                        "sender_id": user_id,
                        "sender_name": user_name,
                        "content": data.get("content", ""),
                        "message_type": data.get("message_type", "text"),
                    },
                }
                await manager.broadcast(room_id, payload)
                continue

            if msg_type in {"webrtc_offer", "webrtc_answer", "webrtc_ice"}:
                target_user_id = data.get("target_user_id")
                if not target_user_id:
                    await websocket.send_json({
                        "type": "error",
                        "message": "target_user_id is required",
                    })
                    continue

                relay_payload = {
                    "type": msg_type,
                    "from_user_id": user_id,
                    "from_user_name": user_name,
                }

                if msg_type in {"webrtc_offer", "webrtc_answer"}:
                    relay_payload["sdp"] = data.get("sdp")

                if msg_type == "webrtc_ice":
                    relay_payload["candidate"] = data.get("candidate")

                await manager.send_to_user(room_id, int(target_user_id), relay_payload)
                continue

            await websocket.send_json({
                "type": "error",
                "message": f"Unsupported message type: {msg_type}",
            })

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(room_id, user_id)
        await manager.broadcast(
            room_id,
            {
                "type": "participant_left",
                "user_id": user_id,
                "user_name": user_name,
            },
            exclude_user_id=user_id,
        )

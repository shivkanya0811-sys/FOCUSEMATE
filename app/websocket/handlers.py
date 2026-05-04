"""
FocuseMate – WebSocket Handlers (Chat + WebRTC Signaling)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.message_service import create_message
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


async def handle_websocket(
    websocket: WebSocket,
    room_id: int,
    user_id: int,
    db: AsyncSession,
) -> None:
    """
    Main WebSocket handler. Routes incoming messages to:
    - chat_message  → persist & broadcast
    - webrtc_offer  → forward SDP offer to target
    - webrtc_answer → forward SDP answer to target
    - webrtc_ice    → forward ICE candidate to target
    - typing        → broadcast typing indicator
    - ping          → respond with pong
    """
    await manager.connect(websocket, room_id, user_id)

    # Send current online users to the newly connected client
    online_users = manager.get_room_users(room_id)
    await websocket.send_json({
        "type": "room_state",
        "room_id": room_id,
        "online_users": online_users,
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = data.get("type", "")

            if msg_type == "chat_message":
                await _handle_chat_message(data, room_id, user_id, db)

            elif msg_type == "webrtc_offer":
                await _handle_webrtc_signal(data, room_id, user_id, "webrtc_offer")

            elif msg_type == "webrtc_answer":
                await _handle_webrtc_signal(data, room_id, user_id, "webrtc_answer")

            elif msg_type == "webrtc_ice":
                await _handle_webrtc_signal(data, room_id, user_id, "webrtc_ice")

            elif msg_type == "typing":
                await manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "typing",
                        "user_id": user_id,
                        "is_typing": data.get("is_typing", True),
                    },
                    exclude_user=user_id,
                )

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, user_id)
        await manager.broadcast_to_room(
            room_id,
            {
                "type": "user_left",
                "user_id": user_id,
                "room_id": room_id,
            },
        )
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id} in room {room_id}: {e}")
        manager.disconnect(websocket, room_id, user_id)
        await manager.broadcast_to_room(
            room_id,
            {
                "type": "user_left",
                "user_id": user_id,
                "room_id": room_id,
            },
        )


async def _handle_chat_message(
    data: dict,
    room_id: int,
    user_id: int,
    db: AsyncSession,
) -> None:
    """Persist a chat message and broadcast to room."""
    content = data.get("content", "").strip()
    if not content:
        return
    message_type = data.get("message_type", "text")

    saved = await create_message(
        db=db,
        room_id=room_id,
        sender_id=user_id,
        content=content,
        message_type=message_type,
    )

    broadcast_data = {
        "type": "chat_message",
        "message": {
            "id": saved["id"],
            "room_id": saved["room_id"],
            "sender_id": saved["sender_id"],
            "sender_name": saved["sender_name"],
            "sender_avatar": saved["sender_avatar"],
            "content": saved["content"],
            "message_type": saved["message_type"],
            "created_at": saved["created_at"].isoformat(),
        },
    }
    await manager.broadcast_to_room(room_id, broadcast_data)


async def _handle_webrtc_signal(
    data: dict,
    room_id: int,
    from_user_id: int,
    signal_type: str,
) -> None:
    """Forward WebRTC signaling data to a target user."""
    target_user_id = data.get("target_user_id")
    if not target_user_id:
        return

    payload = {
        "type": signal_type,
        "from_user_id": from_user_id,
        "room_id": room_id,
    }

    if signal_type == "webrtc_offer":
        payload["sdp"] = data.get("sdp")
    elif signal_type == "webrtc_answer":
        payload["sdp"] = data.get("sdp")
    elif signal_type == "webrtc_ice":
        payload["candidate"] = data.get("candidate")

    await manager.send_to_user(room_id, target_user_id, payload)

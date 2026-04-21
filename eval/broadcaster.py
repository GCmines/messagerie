from typing import Literal

import asyncio

from fastapi import WebSocket

Action = Literal["create", "update", "delete"]

class WebSocketBroadcaster:
    """
    registers active websocket connections
    and broadcasts messages to all of them
    """
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    # cannot import Note here, to avoid circular import
    async def broadcast(self, action: Action, note: "Note"):
        payload = { "action": action, "note": dict(note) }
        coros = [ws.send_json(payload) for ws in self.active_connections]
        results = await asyncio.gather(*coros, return_exceptions=True)

        # Clean up any that failed
        for ws, result in zip(self.active_connections.copy(), results):
            if isinstance(result, Exception):
                self.disconnect(ws)
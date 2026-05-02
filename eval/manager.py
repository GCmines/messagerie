# manager.py
# Gestionnaire de connexions WebSocket par room.
# Permet d'envoyer des messages à tous les sockets connectés à une room.

from typing import Dict, Set
from fastapi import WebSocket
import asyncio
import json

class ConnectionManager:
    def __init__(self):
        # mapping room_name -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, room: str, websocket: WebSocket):
        await websocket.accept()
        conns = self.active_connections.setdefault(room, set())
        conns.add(websocket)

    def disconnect(self, room: str, websocket: WebSocket):
        conns = self.active_connections.get(room)
        if conns and websocket in conns:
            conns.remove(websocket)
            if not conns:
                del self.active_connections[room]

    async def broadcast(self, room: str, message: dict):
        conns = list(self.active_connections.get(room, []))
        if not conns:
            return
        data = json.dumps(message, default=str)
        # send concurrently
        await asyncio.gather(*(ws.send_text(data) for ws in conns))

# manager.py
from typing import Dict, Set, List, Tuple
from fastapi import WebSocket
import asyncio
import json

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self.username_map: Dict[str, Set[int]] = {}
        self.ws_meta: Dict[int, Tuple[str, str]] = {}
        self._lock = asyncio.Lock() # Le lock c'est ce dont tu me parlais dans ton mail?
        #Yes c'est ça c'est pour éviter les problèmes de concu quand plusieurs connexions essaient de se connecter ou se déconnecter en même temps.

    async def connect(self, room: str, websocket: WebSocket, username: str):
        await websocket.accept()
        async with self._lock:
            self.rooms.setdefault(room, set()).add(websocket)
            self.username_map.setdefault(username, set()).add(id(websocket))
            self.ws_meta[id(websocket)] = (room, username)

    def disconnect(self, room: str, websocket: WebSocket):
        try:
            if room in self.rooms and websocket in self.rooms[room]:
                self.rooms[room].remove(websocket)
                if not self.rooms[room]:
                    del self.rooms[room]
        except Exception:
            pass
        meta = self.ws_meta.pop(id(websocket), None)
        if meta:
            _, username = meta
            ids = self.username_map.get(username)
            if ids:
                ids.discard(id(websocket))
                if not ids:
                    del self.username_map[username]

    def reserve_username(self, username: str) -> bool:
        """
        Reserve a username for a live connection.
        By default this implementation allows multiple sockets per username.
        If you want to prevent duplicates, change this to return False when
        username_map[username] is non-empty.
        """
        self.username_map.setdefault(username, set())
        return True

    def release_username(self, username: str):
        """
        Release a username reservation if no sockets remain for it.
        Safe to call even if username not present.
        """
        ids = self.username_map.get(username)
        if ids is None or len(ids) == 0:
            self.username_map.pop(username, None)

    def is_username_taken(self, username: str) -> bool:
        return username in self.username_map and len(self.username_map[username]) > 0

    async def broadcast(self, room: str, message: dict):
        conns = list(self.rooms.get(room, []))
        try:
            text = json.dumps(message)
        except Exception:
            text = str(message)
        for ws in conns:
            try:
                await ws.send_text(text)
            except Exception:
                pass

    def get_taken_usernames(self) -> List[str]:
        return [u for u, s in self.username_map.items() if s]

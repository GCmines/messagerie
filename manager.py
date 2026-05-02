# manager.py
# Gestionnaire de connexions WebSocket par room.
# Permet d'envoyer des messages à tous les sockets connectés à une room.
# Ajout : gestion des usernames réservés et libération à la déconnexion.

from typing import Dict, Set, Optional
from fastapi import WebSocket
import asyncio
import json
import threading

class ConnectionManager:
    def __init__(self):
        # mapping room_name -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # mapping websocket -> username (to know which username to release)
        self.ws_to_username: Dict[WebSocket, str] = {}
        # set of usernames currently reserved/taken by active connections
        self.taken_usernames: Set[str] = set()
        # lock to protect taken_usernames and ws_to_username
        self._lock = threading.Lock()

    async def connect(self, room: str, websocket: WebSocket, username: Optional[str] = None):
        """
        Accept websocket and register it in the room.
        Optionally associate a username with this websocket (for release on disconnect).
        """
        await websocket.accept()
        conns = self.active_connections.setdefault(room, set())
        conns.add(websocket)
        if username:
            with self._lock:
                self.ws_to_username[websocket] = username
                self.taken_usernames.add(username)

    def disconnect(self, room: str, websocket: WebSocket):
        """
        Remove websocket from room and cleanup username mapping.
        """
        conns = self.active_connections.get(room)
        if conns and websocket in conns:
            conns.remove(websocket)
            if not conns:
                del self.active_connections[room]
        # cleanup username mapping
        with self._lock:
            username = self.ws_to_username.pop(websocket, None)
            if username and username in self.taken_usernames:
                self.taken_usernames.discard(username)

    async def broadcast(self, room: str, message: dict):
        conns = list(self.active_connections.get(room, []))
        if not conns:
            return
        data = json.dumps(message, default=str)
        # send concurrently
        await asyncio.gather(*(ws.send_text(data) for ws in conns))

    # --- username reservation API (thread-safe) ---
    def reserve_username(self, username: str) -> bool:
        """
        Try to reserve a username. Returns True if reserved, False if already taken.
        """
        with self._lock:
            if username in self.taken_usernames:
                return False
            self.taken_usernames.add(username)
            return True

    def release_username(self, username: str):
        """
        Release a previously reserved username.
        """
        with self._lock:
            self.taken_usernames.discard(username)
            # also remove any websocket mapping that still references it
            to_remove = [ws for ws, u in self.ws_to_username.items() if u == username]
            for ws in to_remove:
                self.ws_to_username.pop(ws, None)

    def get_taken_usernames(self) -> Set[str]:
        with self._lock:
            return set(self.taken_usernames)

    def is_username_taken(self, username: str) -> bool:
        with self._lock:
            return username in self.taken_usernames

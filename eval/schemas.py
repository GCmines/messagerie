# schemas.py
# Pydantic schemas pour validation des requêtes / réponses

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    name: str

class RoomCreate(BaseModel):
    name: str

class SubscriptionAction(BaseModel):
    user_name: str
    room_name: str

class MessageCreate(BaseModel):
    user_name: str
    room_name: str
    content: str

class MessageOut(BaseModel):
    id: int
    user_name: str
    room_name: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True

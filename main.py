# main.py
# Application FastAPI principale : endpoints REST et WebSocket

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models, schemas
from manager import ConnectionManager
from typing import List
from datetime import datetime

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mini WhatsApp - Evaluation project")

# Serve static frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

manager = ConnectionManager()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- REST endpoints for creating users and rooms ---
@app.post("/users", status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.name == user.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    u = models.User(name=user.name)
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": u.id, "name": u.name}

@app.get("/users", response_model=List[schemas.UserCreate])
def list_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [{"name": u.name} for u in users]

@app.post("/rooms", status_code=201)
def create_room(room: schemas.RoomCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Room).filter(models.Room.name == room.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Room already exists")
    r = models.Room(name=room.name)
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "name": r.name}

@app.get("/rooms")
def list_rooms(db: Session = Depends(get_db)):
    rooms = db.query(models.Room).all()
    return [{"name": r.name} for r in rooms]

# --- subscribe / unsubscribe (existing endpoints) ---
@app.post("/subscribe")
def subscribe(action: schemas.SubscriptionAction, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.name == action.user_name).first()
    room = db.query(models.Room).filter(models.Room.name == action.room_name).first()
    if not user or not room:
        raise HTTPException(status_code=404, detail="User or room not found")
    existing = db.query(models.Subscription).filter_by(user_id=user.id, room_id=room.id).first()
    if existing:
        return {"status": "already_subscribed"}
    sub = models.Subscription(user_id=user.id, room_id=room.id)
    db.add(sub)
    db.commit()
    return {"status": "subscribed"}

@app.post("/unsubscribe")
def unsubscribe(action: schemas.SubscriptionAction, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.name == action.user_name).first()
    room = db.query(models.Room).filter(models.Room.name == action.room_name).first()
    if not user or not room:
        raise HTTPException(status_code=404, detail="User or room not found")
    existing = db.query(models.Subscription).filter_by(user_id=user.id, room_id=room.id).first()
    if not existing:
        return {"status": "not_subscribed"}
    db.delete(existing)
    db.commit()
    return {"status": "unsubscribed"}

@app.get("/subscriptions/{user_name}")
def get_subscriptions(user_name: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.name == user_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    subs = db.query(models.Subscription).filter_by(user_id=user.id).all()
    room_names = [db.query(models.Room).get(s.room_id).name for s in subs]
    return {"user": user.name, "rooms": room_names}

# --- messages endpoints ---
@app.post("/messages", status_code=201)
def post_message(msg: schemas.MessageCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.name == msg.user_name).first()
    room = db.query(models.Room).filter(models.Room.name == msg.room_name).first()
    if not user or not room:
        raise HTTPException(status_code=404, detail="User or room not found")
    # check subscription
    sub = db.query(models.Subscription).filter_by(user_id=user.id, room_id=room.id).first()
    if not sub:
        raise HTTPException(status_code=403, detail="User not subscribed to room")
    m = models.Message(user_id=user.id, room_id=room.id, content=msg.content, created_at=datetime.utcnow())
    db.add(m)
    db.commit()
    db.refresh(m)
    out = {
        "id": m.id,
        "user_name": user.name,
        "room_name": room.name,
        "content": m.content,
        "created_at": m.created_at.isoformat()
    }
    # broadcast to connected websockets in the room
    import asyncio
    asyncio.create_task(manager.broadcast(room.name, out))
    return out

@app.get("/rooms/{room_name}/messages")
def get_room_messages(room_name: str, db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.name == room_name).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    msgs = db.query(models.Message).filter_by(room_id=room.id).order_by(models.Message.created_at).all()
    out = []
    for m in msgs:
        user = db.query(models.User).get(m.user_id)
        out.append({
            "id": m.id,
            "user_name": user.name if user else "unknown",
            "room_name": room.name,
            "content": m.content,
            "created_at": m.created_at.isoformat()
        })
    return out

# --- New endpoints for username reservation and join/leave flow ---
@app.get("/available_usernames")
def available_usernames(db: Session = Depends(get_db)):
    """
    Return list of usernames present in DB but not currently taken by an active websocket.
    """
    users = db.query(models.User).all()
    all_names = [u.name for u in users]
    taken = manager.get_taken_usernames()
    available = [n for n in all_names if n not in taken]
    return {"available_usernames": available}

class JoinRequest(schemas.SubscriptionAction):
    pass

@app.post("/join")
def join_room(action: JoinRequest, db: Session = Depends(get_db)):
    """
    Reserve a username for a live connection and subscribe the user to the room.
    This endpoint atomically:
      - checks user and room exist
      - checks username not already taken (in-memory)
      - creates subscription if missing
      - marks username as taken
    """
    user = db.query(models.User).filter(models.User.name == action.user_name).first()
    room = db.query(models.Room).filter(models.Room.name == action.room_name).first()
    if not user or not room:
        raise HTTPException(status_code=404, detail="User or room not found")

    # attempt to reserve username in manager
    reserved = manager.reserve_username(action.user_name)
    if not reserved:
        raise HTTPException(status_code=409, detail="username already taken")

    # ensure subscription exists
    existing = db.query(models.Subscription).filter_by(user_id=user.id, room_id=room.id).first()
    if not existing:
        sub = models.Subscription(user_id=user.id, room_id=room.id)
        db.add(sub)
        db.commit()

    return {"status": "ok", "room": room.name, "username": user.name}

@app.post("/leave")
def leave_room(action: schemas.SubscriptionAction, db: Session = Depends(get_db)):
    """
    Release a username and optionally unsubscribe from a room.
    """
    username = action.user_name
    room_name = action.room_name

    # release in-memory reservation
    manager.release_username(username)

    # optionally remove subscription if present
    user = db.query(models.User).filter(models.User.name == username).first()
    room = db.query(models.Room).filter(models.Room.name == room_name).first()
    if user and room:
        existing = db.query(models.Subscription).filter_by(user_id=user.id, room_id=room.id).first()
        if existing:
            db.delete(existing)
            db.commit()
    return {"status": "ok"}

# --- WebSocket endpoint ---
@app.websocket("/ws/{user_name}/{room_name}")
async def websocket_endpoint(websocket: WebSocket, user_name: str, room_name: str, db: Session = Depends(get_db)):
    # Validate user and subscription
    user = db.query(models.User).filter(models.User.name == user_name).first()
    room = db.query(models.Room).filter(models.Room.name == room_name).first()
    if not user or not room:
        await websocket.accept()
        await websocket.send_text('{"error":"user_or_room_not_found"}')
        await websocket.close()
        return
    sub = db.query(models.Subscription).filter_by(user_id=user.id, room_id=room.id).first()
    if not sub:
        await websocket.accept()
        await websocket.send_text('{"error":"not_subscribed"}')
        await websocket.close()
        return

    # Ensure username is reserved (defensive)
    if not manager.is_username_taken(user_name):
        # If username wasn't reserved via /join, reserve it now to avoid duplicates
        manager.reserve_username(user_name)

    await manager.connect(room_name, websocket, user_name)
    try:
        # send a welcome / recent messages
        await websocket.send_text('{"info":"connected","room":"%s"}' % room_name)
        while True:
            data = await websocket.receive_text()
            # Expect JSON with {"content":"..."} or plain text
            import json
            try:
                payload = json.loads(data)
                content = payload.get("content")
            except Exception:
                content = data
            if not content:
                continue
            # persist message
            m = models.Message(user_id=user.id, room_id=room.id, content=content, created_at=datetime.utcnow())
            db.add(m)
            db.commit()
            db.refresh(m)
            out = {
                "id": m.id,
                "user_name": user.name,
                "room_name": room.name,
                "content": m.content,
                "created_at": m.created_at.isoformat()
            }
            await manager.broadcast(room_name, out)
    except WebSocketDisconnect:
        # cleanup on disconnect
        manager.disconnect(room_name, websocket)
        manager.release_username(user_name)
    except Exception:
        manager.disconnect(room_name, websocket)
        manager.release_username(user_name)
        try:
            await websocket.close()
        except:
            pass

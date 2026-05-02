from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models, schemas
from manager import ConnectionManager
from typing import List
from datetime import datetime, timezone

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mini WhatsApp - Evaluation project")
app.mount("/static", StaticFiles(directory="static"), name="static")

manager = ConnectionManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

@app.post("/messages", status_code=201)
def post_message(msg: schemas.MessageCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.name == msg.user_name).first()
    room = db.query(models.Room).filter(models.Room.name == msg.room_name).first()
    if not user or not room:
        raise HTTPException(status_code=404, detail="User or room not found")
    sub = db.query(models.Subscription).filter_by(user_id=user.id, room_id=room.id).first()
    if not sub:
        raise HTTPException(status_code=403, detail="User not subscribed to room")
    m = models.Message(user_id=user.id, room_id=room.id, content=msg.content, created_at=datetime.utcnow())
    db.add(m)
    db.commit()
    db.refresh(m)
    created_utc = m.created_at
    if created_utc.tzinfo is None:
        created_utc = created_utc.replace(tzinfo=timezone.utc)
    created_iso = created_utc.isoformat().replace('+00:00', 'Z')
    out = {
        "id": m.id,
        "user_name": user.name,
        "room_name": room.name,
        "content": m.content,
        "created_at": created_iso
    }
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
        created_utc = m.created_at
        if created_utc.tzinfo is None:
            created_utc = created_utc.replace(tzinfo=timezone.utc)
        created_iso = created_utc.isoformat().replace('+00:00', 'Z')
        out.append({
            "id": m.id,
            "user_name": user.name if user else "unknown",
            "room_name": room.name,
            "content": m.content,
            "created_at": created_iso
        })
    return out

@app.get("/available_usernames")
def available_usernames(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    all_names = [u.name for u in users]
    taken = manager.get_taken_usernames()
    available = [n for n in all_names if n not in taken]
    return {"available_usernames": available}

class JoinRequest(schemas.SubscriptionAction):
    pass

@app.post("/join")
def join_room(action: JoinRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.name == action.user_name).first()
    room = db.query(models.Room).filter(models.Room.name == action.room_name).first()
    if not user or not room:
        raise HTTPException(status_code=404, detail="User or room not found")

    reserved = manager.reserve_username(action.user_name)
    if not reserved:
        raise HTTPException(status_code=409, detail="username already taken")

    existing = db.query(models.Subscription).filter_by(user_id=user.id, room_id=room.id).first()
    if not existing:
        sub = models.Subscription(user_id=user.id, room_id=room.id)
        db.add(sub)
        db.commit()

    return {"status": "ok", "room": room.name, "username": user.name}

@app.post("/leave")
def leave_room(action: schemas.SubscriptionAction, db: Session = Depends(get_db)):
    username = action.user_name
    room_name = action.room_name

    manager.release_username(username)

    user = db.query(models.User).filter(models.User.name == username).first()
    room = db.query(models.Room).filter(models.Room.name == room_name).first()
    if user and room:
        existing = db.query(models.Subscription).filter_by(user_id=user.id, room_id=room.id).first()
        if existing:
            db.delete(existing)
            db.commit()
    return {"status": "ok"}

@app.websocket("/ws/{user_name}/{room_name}")
async def websocket_endpoint(websocket: WebSocket, user_name: str, room_name: str, db: Session = Depends(get_db)):
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
    await manager.connect(room_name, websocket, user_name)
    try:
        await websocket.send_text('{"info":"connected","room":"%s"}' % room_name)
        while True:
            data = await websocket.receive_text()
            import json
            try:
                payload = json.loads(data)
                content = payload.get("content")
            except Exception:
                content = data
            if not content:
                continue
            m = models.Message(user_id=user.id, room_id=room.id, content=content, created_at=datetime.utcnow())
            db.add(m)
            db.commit()
            db.refresh(m)
            created_utc = m.created_at
            if created_utc.tzinfo is None:
                created_utc = created_utc.replace(tzinfo=timezone.utc)
            created_iso = created_utc.isoformat().replace('+00:00', 'Z')
            out = {
                "id": m.id,
                "user_name": user.name,
                "room_name": room.name,
                "content": m.content,
                "created_at": created_iso
            }
            await manager.broadcast(room_name, out)
    except WebSocketDisconnect:
        manager.disconnect(room_name, websocket)
        manager.release_username(user_name)
    except Exception:
        manager.disconnect(room_name, websocket)
        manager.release_username(user_name)
        try:
            await websocket.close()
        except:
            pass

VERSION = "13e"

from contextlib import asynccontextmanager
from typing import Annotated

import requests

from fastapi import FastAPI
from fastapi import Depends
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import WebSocket, WebSocketDisconnect

from sqlmodel import SQLModel, create_engine
from sqlmodel import Session
from sqlmodel import Field
from sqlmodel import select

from broadcaster import WebSocketBroadcaster

# create a singleton object
websocket_broadcaster = WebSocketBroadcaster()


SQLITE_URL = f"sqlite:///notes.db"
engine = create_engine(SQLITE_URL)

# this is how we control what is done at startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic comes here
    # Create the database and tables if they don't exist
    SQLModel.metadata.create_all(engine)

    yield
    # shutdown logic comes here
    # none so far


# create a so-called "dependency" to get the database session
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


# in this version we define several models for a note
# that describe which fields exactly we want to support / expose
# in each operation of the API
class NoteCreate(SQLModel):
    title: str | None = Field(default=None, description="le titre de la note")
    description: str | None = Field(default=None, description="Le texte de la note")

class NoteUpdate(NoteCreate):
    done: bool = Field(default=False, description="La tâche est-elle terminée ?")

class Note(NoteUpdate, table=True):
    id: int | None = Field(default=None, primary_key=True)


# Create the FastAPI app with the lifespan context manager
app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return RedirectResponse(url="/front/notes")

"""
http :8000/api/notes title="Devoirs" description="TP Backend"
http :8000/api/notes title="Papiers" description="Nouveau Passeport"
http :8000/api/notes title="Dentiste" description="ouille !"
"""
@app.post("/api/notes")
async def create_note(note: NoteCreate, session: SessionDep) -> Note:
    db_note = Note.model_validate(note)
    session.add(db_note)
    session.commit()
    session.refresh(db_note)
    await websocket_broadcaster.broadcast(action="create", note=db_note)
    return db_note

"""
http :8000/api/notes
"""
@app.get("/api/notes")
def get_notes(session: SessionDep) -> list[Note]:
    notes = session.exec(select(Note)).all()
    return notes

"""
http :8000/api/notes/1
"""
@app.get("/api/notes/{note_id}")
def get_note(note_id: int, session: SessionDep) -> Note | None:
    note = session.get(Note, note_id)
    return note

"""
http :8000/static/css/style.css
"""
app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")

"""
http :8000/front/notes
"""
@app.get("/front/notes", response_class=HTMLResponse)
def notes_page(request: Request, session: SessionDep):
    # get the notes through the API, not directly from the database
    url = request.url_for("get_notes")
    response = requests.get(url)
    if not (200 <= response.status_code < 300):
        raise Exception(f"Error {response.status_code} while getting notes")
    notes = response.json()
    return templates.TemplateResponse(
        request=request,
        name="notes.html.j2",
        context={"version": VERSION, "notes": notes})


"""
http PATCH :8000/api/notes/1 done:=true
http PATCH :8000/api/notes/1 description="TP Backend FastAPI"
"""
@app.patch("/api/notes/{note_id}", response_model=Note)
async def update_note(
    note_id: int,
    session: SessionDep,
    payload: NoteUpdate,
):
    db_note = session.get(Note, note_id)
    if not db_note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")
    # a class-independant way to do the update
    db_note.sqlmodel_update(payload.model_dump(exclude_unset=True))
    # commit the changes to the database
    session.add(db_note)
    session.commit()
    session.refresh(db_note)
    await websocket_broadcaster.broadcast(action="update", note=db_note)
    # return the updated note
    return db_note


"""
http DELETE :8000/api/notes/3
"""
@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: int, session: SessionDep):
    db_note = session.get(Note, note_id)
    if not db_note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")
    # delete the note
    session.delete(db_note)
    session.commit()
    await websocket_broadcaster.broadcast(action="delete", note=db_note)
    return db_note


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_broadcaster.connect(websocket)
    try:
        while True:
            # Optional: handle incoming messages if you want, or just keep alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_broadcaster.disconnect(websocket)
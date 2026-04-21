function createNoteElement(note) {
    const elt = document.createElement("li");
    elt.classList.add("note");
    elt.id = `note-${note.id}`;
    const html = `
    <div class="title">${note.title}
        <button class="delete-button" onclick="note_delete(this, ${note.id})">🗑</button>
    </div>
    <div class="line">
        <span>${note.description}</span>
        <input type="checkbox" ${note.done ? "checked" : ""}
        onchange="note_done_changed(this, ${note.id})" />
    </div>
`
    elt.innerHTML = html;
    document.querySelector("ul.notes").appendChild(elt);
}

function updateNoteElement(note) {
    const id = note.id;
    const elt = document.querySelector(`#note-${id}`);
    if (!elt) {
        console.warn("Note element not found for ID:", id);
        return;
    }
    elt.querySelector(".title").textContent = note.title;
    elt.querySelector("span").textContent = note.description;
    elt.querySelector("input[type='checkbox']").checked = note.done ? "checked" : "";
}

function deleteNoteElement(noteId) {
    const elt = document.querySelector(`#note-${noteId}`);
    if (elt) {
        elt.remove();
    } else {
        console.warn("Note element not found for ID:", noteId);
    }
}
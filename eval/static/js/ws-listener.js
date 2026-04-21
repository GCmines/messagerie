document.addEventListener("DOMContentLoaded",
    // connect to the WebSocket server on page load
    () => {
        const ws = new WebSocket(`ws://${window.location.host}/ws`);

        ws.onopen = () => {
            console.log("WebSocket connection opened");
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("Received data:", data);
            // Handle the received data as needed
            const { action, note } = data;
            switch (action) {
                case "create":
                    createNoteElement(note);
                    break;
                case "update":
                    updateNoteElement(note);
                    break;
                case "delete":
                    deleteNoteElement(note.id);
                    break;
                default:
                    console.warn("Unknown action:", action);
            }
        };

        ws.onclose = () => {
            console.log("WebSocket connection closed");
        };

        ws.onerror = (error) => {
            console.error("WebSocket error:", error);
        };
    }
)
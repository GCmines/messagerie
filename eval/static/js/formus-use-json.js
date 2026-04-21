// reprogram all forms to send their fields as JSON

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('form').forEach((form) => {
        const formToJSON = form => Object.fromEntries(new FormData(form))
        form.addEventListener("submit", async (event) => {
          event.preventDefault()

          // use the action= attribute of the <form>
          //  to determine where to send the data
          const action = form.action
          const json = formToJSON(form)
          const response = await fetch(action, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(json),
          })
          if (!response.ok) {
            console.error(`Error submitting form at ${action} : `, response.statusText)
            return
          }
          const decoded = await response.json()
          console.log("response", decoded)
        })
      })
    })
const form = document.getElementById("issueForm");
const statusMsg = document.getElementById("statusMsg");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusMsg.textContent = "Submitting...";

  const payload = Object.fromEntries(new FormData(form).entries());

  try {
    const response = await fetch("/api/issues", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Submit failed");
    }

    statusMsg.textContent = `Issue submitted. Ticket ID: ${data.id}`;
    form.reset();
  } catch (error) {
    statusMsg.textContent = `Error: ${error.message}`;
  }
});

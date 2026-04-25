const list = document.getElementById("issueList");
const refreshBtn = document.getElementById("refreshBtn");

async function loadIssues() {
  list.textContent = "Loading...";
  try {
    const response = await fetch("/api/issues");
    const issues = await response.json();

    if (!response.ok) {
      throw new Error("Could not load issues");
    }

    if (!issues.length) {
      list.textContent = "No issues yet.";
      return;
    }

    list.innerHTML = "";
    for (const issue of issues) {
      const card = document.createElement("article");
      card.className = "issue";
      card.innerHTML = `
        <h3>#${issue.id} - ${issue.category}</h3>
        <p><strong>Name:</strong> ${issue.name} (${issue.email})</p>
        <p><strong>Location:</strong> ${issue.location}</p>
        <p><strong>Description:</strong> ${issue.description}</p>
        <p><strong>Created:</strong> ${issue.created_at}</p>
      `;

      const label = document.createElement("label");
      label.textContent = "Status:";
      const select = document.createElement("select");

      ["Open", "In Progress", "Resolved"].forEach((status) => {
        const option = document.createElement("option");
        option.value = status;
        option.textContent = status;
        option.selected = issue.status === status;
        select.appendChild(option);
      });

      select.addEventListener("change", () => updateStatus(issue.id, select.value));
      label.appendChild(select);
      card.appendChild(label);
      list.appendChild(card);
    }
  } catch (error) {
    list.textContent = `Error: ${error.message}`;
  }
}

async function updateStatus(issueId, status) {
  const response = await fetch(`/api/issues/${issueId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status })
  });

  if (!response.ok) {
    const data = await response.json();
    alert(data.error || "Status update failed");
  }
}

refreshBtn.addEventListener("click", loadIssues);
loadIssues();
setInterval(loadIssues, 10000);

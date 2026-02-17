const assets = [
  { name: "Subestación Norte", status: "Operativa", load: "72%", incidents: 0 },
  { name: "Subestación Central", status: "Atención", load: "89%", incidents: 1 },
  { name: "Nodo Sur", status: "Operativa", load: "65%", incidents: 0 },
  { name: "Planta Costera", status: "Crítica", load: "96%", incidents: 2 },
];

function statusClass(status) {
  if (status === "Operativa") return "status-ok";
  if (status === "Atención") return "status-warn";
  return "status-alert";
}

function renderCards() {
  const grid = document.getElementById("status-grid");
  grid.innerHTML = assets
    .map(
      (asset) => `
      <article class="card">
        <h3>${asset.name}</h3>
        <p><span class="status-pill ${statusClass(asset.status)}">${asset.status}</span></p>
        <p>Carga actual: <strong>${asset.load}</strong></p>
        <p>Incidentes activos: <strong>${asset.incidents}</strong></p>
      </article>`
    )
    .join("");
}

function setupForm() {
  const form = document.getElementById("pilot-form");
  const feedback = document.getElementById("form-feedback");

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const company = data.get("company");
    const email = data.get("email");
    const priority = data.get("priority");

    feedback.textContent = `Solicitud enviada para ${company} (${email}) con prioridad ${priority}.`;
    form.reset();
  });
}

function setBuildDate() {
  const dateNode = document.getElementById("build-date");
  dateNode.textContent = `Actualizado: ${new Date().toLocaleDateString("es-CL")}`;
}

renderCards();
setupForm();
setBuildDate();

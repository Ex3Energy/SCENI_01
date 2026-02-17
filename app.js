const assets = [
  { name: "Subestación Norte", status: "Operativa", load: "72%", incidents: 0 },
  { name: "Subestación Central", status: "Atención", load: "89%", incidents: 1 },
  { name: "Nodo Sur", status: "Operativa", load: "65%", incidents: 0 },
  { name: "Planta Costera", status: "Crítica", load: "96%", incidents: 2 },
];

const regionFactors = {
  "houston-gulf": { capex: 1.12, timeline: 1.08, risk: "Medio", note: "Alta exposición climática, buena logística portuaria." },
  "dallas-fortworth": { capex: 1.05, timeline: 1.0, risk: "Medio-bajo", note: "Cadena de suministro sólida y acceso laboral." },
  "west-texas": { capex: 0.95, timeline: 1.12, risk: "Medio", note: "Costo de suelo competitivo, mayor distancia a nodos." },
  "austin-sanantonio": { capex: 1.08, timeline: 1.04, risk: "Bajo", note: "Entorno tecnológico favorable y demanda creciente." },
};

const projectBaseMusdPerMw = {
  substation: 1.6,
  "hybrid-plant": 1.35,
  microgrid: 1.95,
};

const resilienceFactor = {
  standard: 1.0,
  high: 1.12,
  "mission-critical": 1.27,
};

function statusClass(status) {
  if (status === "Operativa") return "status-ok";
  if (status === "Atención") return "status-warn";
  return "status-alert";
}

function formatMusd(value) {
  return `${value.toFixed(1)} MUSD`;
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

function buildEstimate(data) {
  const region = regionFactors[data.region];
  const base = projectBaseMusdPerMw[data.projectType];
  const resilience = resilienceFactor[data.resilience];

  const storageAdder = data.storageHours * 0.055;
  const interconnectionAdder = data.distanceKm * 0.045;
  const rawCapex = data.capacityMw * base;
  const capex = (rawCapex + rawCapex * storageAdder + interconnectionAdder) * region.capex * resilience;

  const scheduleBaseMonths = 12 + data.capacityMw / 25;
  const scheduleMonths = scheduleBaseMonths * region.timeline * resilience;

  const recommendation =
    data.distanceKm > 45
      ? "Reubicar más cerca de nodo ERCOT o evaluar subestación dedicada para bajar CAPEX de interconexión."
      : "Ubicación técnicamente viable para fase de prefactibilidad; avanzar con estudios de terreno y permisos.";

  return {
    capex,
    scheduleMonths,
    risk: region.risk,
    note: region.note,
    recommendation,
  };
}

function renderEstimate(result) {
  const output = document.getElementById("estimate-output");
  output.innerHTML = `
    <p><strong>CAPEX estimado:</strong> ${formatMusd(result.capex)}</p>
    <p><strong>Cronograma estimado:</strong> ${result.scheduleMonths.toFixed(1)} meses</p>
    <p><strong>Riesgo regional:</strong> ${result.risk}</p>
    <p><strong>Contexto:</strong> ${result.note}</p>
    <p><strong>Recomendación:</strong> ${result.recommendation}</p>
  `;
}

function setupEstimator() {
  const form = document.getElementById("estimate-form");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const normalized = {
      region: data.get("region"),
      projectType: data.get("projectType"),
      capacityMw: Number(data.get("capacityMw")),
      storageHours: Number(data.get("storageHours")),
      distanceKm: Number(data.get("distanceKm")),
      resilience: data.get("resilience"),
    };

    const result = buildEstimate(normalized);
    renderEstimate(result);
  });
}

function setupPilotForm() {
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
setupEstimator();
setupPilotForm();
setBuildDate();

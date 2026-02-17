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


function getDefaultApiBaseUrl() {
  if (window.location.hostname.includes("github.io")) {
    return "";
  }
  return "http://localhost:8000";
}

async function checkBackendConnection(baseUrl) {
  const normalized = String(baseUrl || "").trim().replace(/\/$/, "");
  if (!normalized) {
    throw new Error("Define una URL de backend (ej: https://tu-backend.onrender.com)");
  }
  const response = await fetch(`${normalized}/health`);
  if (!response.ok) {
    throw new Error(`Backend responde ${response.status}`);
  }
  return normalized;
}

function formatMusd(value) {
  return `${value.toFixed(1)} MUSD`;
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
      : "Ubicación técnicamente viable para prefactibilidad; avanzar con estudios de terreno y permisos.";

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

    renderEstimate(buildEstimate(normalized));
  });
}

function renderDesignTable(designs) {
  const tbody = document.querySelector("#designs-table tbody");
  if (!designs.length) {
    tbody.innerHTML = '<tr><td colspan="6">Sin datos aún.</td></tr>';
    return;
  }

  tbody.innerHTML = designs
    .slice(0, 8)
    .map(
      (d) => `
      <tr>
        <td>${d.rank}</td>
        <td>${d.firm_energy_pct.toFixed(2)}</td>
        <td>${d.unserved_mwh.toFixed(2)}</td>
        <td>${d.irr_pct.toFixed(2)}</td>
        <td>${d.total_score.toFixed(2)}</td>
        <td><code>${d.snapshot_id.slice(0, 8)}</code></td>
      </tr>`
    )
    .join("");
}

function renderDashboardSummary(simulation, market) {
  const output = document.getElementById("dashboard-output");
  const top = simulation.recommended_design;
  output.innerHTML = `
    <p><strong>Candidatos evaluados:</strong> ${simulation.candidate_count}</p>
    <p><strong>Diseño recomendado (Rank #1):</strong> Firm Energy ${top.firm_energy_pct.toFixed(2)}%</p>
    <p><strong>Unserved:</strong> ${top.unserved_mwh.toFixed(2)} MWh | <strong>IRR:</strong> ${top.irr_pct.toFixed(2)}%</p>
    <p><strong>Nodo ERCOT:</strong> ${market.node} | Avg Price: ${market.avg_price_usd_mwh} USD/MWh</p>
    <p><strong>Volatilidad:</strong> ${market.volatility_pct}% | Peak: ${market.peak_price_usd_mwh} USD/MWh</p>
  `;
}

async function setupDashboard() {
  const form = document.getElementById("opportunity-form");
  const feedback = document.getElementById("dashboard-feedback");
  const checkButton = document.getElementById("check-backend");
  const apiInput = form.querySelector('input[name="apiBaseUrl"]');
  apiInput.value = getDefaultApiBaseUrl();

  checkButton.addEventListener("click", async () => {
    try {
      const base = await checkBackendConnection(apiInput.value);
      feedback.textContent = `Conexión OK con backend en ${base}.`;
    } catch (error) {
      feedback.textContent = `Sin conexión backend: ${error.message}`;
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    feedback.textContent = "Ejecutando simulación...";

    const data = new FormData(form);
    const baseUrl = String(data.get("apiBaseUrl")).replace(/\/$/, "");
    const payload = {
      name: data.get("name"),
      ercot_node: data.get("ercotNode"),
      demand_mw: Number(data.get("demandMw")),
      poi_limit_mw: Number(data.get("poiLimitMw")),
      horizon_hours: Number(data.get("horizonHours")),
    };

    try {
      await checkBackendConnection(baseUrl);

      const createRes = await fetch(`${baseUrl}/api/v1/opportunities`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!createRes.ok) throw new Error("No se pudo crear la oportunidad.");
      const opp = await createRes.json();

      const simulateRes = await fetch(`${baseUrl}/api/v1/opportunities/${opp.id}/simulate`, {
        method: "POST",
      });
      if (!simulateRes.ok) throw new Error("No se pudo ejecutar la simulación.");
      const simulation = await simulateRes.json();

      const marketRes = await fetch(`${baseUrl}/api/v1/market/ercot/${encodeURIComponent(opp.ercot_node)}`);
      if (!marketRes.ok) throw new Error("No se pudo obtener data ERCOT.");
      const market = await marketRes.json();

      renderDesignTable(simulation.designs);
      renderDashboardSummary(simulation, market);
      feedback.textContent = `Simulación lista para ${opp.name}.`; 
    } catch (error) {
      feedback.textContent = `Error: ${error.message}. Si usas GitHub Pages, localhost no funciona en la nube; ejecuta backend local o usa una URL pública.`;
    }
  });
}

function setBuildDate() {
  const dateNode = document.getElementById("build-date");
  dateNode.textContent = `Actualizado: ${new Date().toLocaleDateString("es-CL")}`;
}

setupDashboard();
setupEstimator();
setBuildDate();

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


const DEMO_CLOUD_BACKEND = "https://sceni-backend.onrender.com";

function getApiBaseFromQuery() {
  const params = new URLSearchParams(window.location.search);
  return params.get("api_base") || "";
}

function getInitialApiBaseUrl() {
  const queryValue = getApiBaseFromQuery();
  const savedValue = localStorage.getItem("sceni_api_base_url") || "";

  if (queryValue) {
    return queryValue;
  }

  if (savedValue) {
    return savedValue;
  }

  if (window.location.hostname.includes("github.io")) {
    return DEMO_CLOUD_BACKEND;
  }

  return "http://localhost:8000";
}

function isLocalHost(hostname) {
  return hostname === "localhost" || hostname === "127.0.0.1";
}

function normalizeApiBaseUrl(baseUrl) {
  const raw = String(baseUrl || "").trim();
  if (!raw) {
    throw new Error("Define una URL de backend (ej: https://tu-backend.onrender.com)");
  }

  const frontendHost = window.location.hostname;
  const frontendProtocol = window.location.protocol;
  const frontendIsHosted = !isLocalHost(frontendHost);

  let candidate = raw;
  if (!/^https?:\/\//i.test(candidate)) {
    candidate = `${frontendIsHosted ? "https:" : frontendProtocol}//${candidate}`;
  }

  let url;
  try {
    url = new URL(candidate);
  } catch {
    throw new Error("URL de backend inválida. Ejemplo: https://tu-backend.onrender.com");
  }

  const backendIsLocal = isLocalHost(url.hostname);

  if (frontendIsHosted && backendIsLocal) {
    // auto-corrige a backend cloud por defecto en entorno publicado
    url = new URL(DEMO_CLOUD_BACKEND);
  }

  if (frontendProtocol === "https:" && url.protocol === "http:" && !backendIsLocal) {
    url.protocol = "https:";
  }

  url.pathname = url.pathname.replace(/\/$/, "");
  return url.toString().replace(/\/$/, "");
}


async function fetchWithTimeout(url, timeoutMs = 20000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { method: "GET", signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function probeBackendHealth(baseUrl) {
  const healthUrl = `${baseUrl}/health`;
  const rootUrl = `${baseUrl}/`;

  let lastError = null;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const healthResp = await fetchWithTimeout(healthUrl, 25000);
      if (healthResp.ok) return baseUrl;
      lastError = new Error(`Backend responde ${healthResp.status} en /health`);
    } catch (error) {
      lastError = error;
    }

    try {
      const rootResp = await fetchWithTimeout(rootUrl, 25000);
      if (rootResp.ok) return baseUrl;
      lastError = new Error(`Backend responde ${rootResp.status} en /`);
    } catch (error) {
      lastError = error;
    }

    await new Promise((resolve) => setTimeout(resolve, 1500 * attempt));
  }

  throw lastError || new Error("No fue posible contactar backend");
}

function buildFetchErrorMessage(error, normalizedBaseUrl) {
  const isHttpsPage = window.location.protocol === "https:";
  const isHttpBackend = /^http:\/\//i.test(normalizedBaseUrl);

  if (error?.name === "AbortError") {
    return "Timeout conectando al backend. Revisa que el servicio esté levantado y accesible.";
  }

  if (isHttpsPage && isHttpBackend) {
    return "Bloqueo por contenido mixto (HTTPS→HTTP). Usa backend con HTTPS.";
  }

  if (String(error?.message || "").includes("Failed to fetch")) {
    return "Failed to fetch: backend caído, URL incorrecta o CORS/bloqueo de red. Si usas Render free, espera 30-60s por cold start y reintenta.";
  }

  return error?.message || "No se pudo conectar al backend (red/CORS/URL).";
}

async function checkBackendConnection(baseUrl) {
  const normalized = normalizeApiBaseUrl(baseUrl);

  try {
    return await probeBackendHealth(normalized);
  } catch (error) {
    throw new Error(buildFetchErrorMessage(error, normalized));
  }
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


function buildLocalMarket(node) {
  const seed = String(node || "HB_HOUSTON").toUpperCase().split("").reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  const base = 42 + (seed % 18);
  return {
    node: String(node || "HB_HOUSTON").toUpperCase(),
    avg_price_usd_mwh: Number(base.toFixed(2)),
    volatility_pct: Number((18 + (seed % 14)).toFixed(2)),
    peak_price_usd_mwh: Number((base * 1.85).toFixed(2)),
  };
}

function buildLocalSimulation(payload) {
  const demand = Number(payload.demand_mw);
  const horizon = Number(payload.horizon_hours);
  const poi = Number(payload.poi_limit_mw);

  const gridShares = [0.35, 0.5, 0.7];
  const solarRatios = [0.5, 0.8, 1.1];
  const gasRatios = [0.15, 0.3];

  const designs = [];
  let rank = 0;

  for (const g of gridShares) {
    for (const s of solarRatios) {
      for (const gas of gasRatios) {
        const gridMw = Math.min(poi, demand * g);
        const solarMw = demand * s;
        const gasMw = demand * gas;
        const bessMwh = demand * 0.35 * 4;

        const demandMwh = demand * horizon;
        const served = Math.min(
          demandMwh,
          gridMw * horizon + solarMw * 0.28 * horizon + gasMw * horizon * 0.5 + bessMwh * 0.92
        );

        const unserved = Math.max(0, demandMwh - served);
        const firm = (served / demandMwh) * 100;
        const irr = Math.max(-4, Math.min(26, firm / 6.5 + (gasMw / Math.max(demand, 1)) * 6 - (solarMw / 120) * 0.5));
        const score = firm * 0.45 + (100 - (unserved / demandMwh) * 180) * 0.3 + (irr + 5) * 0.44 + 5;

        designs.push({
          snapshot_id: crypto.randomUUID(),
          candidate_id: crypto.randomUUID(),
          firm_energy_pct: Number(firm.toFixed(2)),
          unserved_mwh: Number(unserved.toFixed(2)),
          irr_pct: Number(irr.toFixed(2)),
          diversity_score: 100,
          total_score: Number(score.toFixed(2)),
          rank: 0,
        });
      }
    }
  }

  designs.sort((a, b) => b.total_score - a.total_score).forEach((d) => {
    rank += 1;
    d.rank = rank;
  });

  return {
    opportunity: {
      id: crypto.randomUUID(),
      name: payload.name,
      ercot_node: payload.ercot_node,
      horizon_hours: horizon,
      demand_mw: demand,
      poi_limit_mw: poi,
    },
    candidate_count: designs.length,
    recommended_design: designs[0],
    designs,
  };
}

async function setupDashboard() {
  const form = document.getElementById("opportunity-form");
  const feedback = document.getElementById("dashboard-feedback");
  const checkButton = document.getElementById("check-backend");
  const useCloudButton = document.getElementById("use-cloud-backend");
  const apiInput = form.querySelector('input[name="apiBaseUrl"]');
  apiInput.value = getInitialApiBaseUrl();

  apiInput.addEventListener("change", () => {
    localStorage.setItem("sceni_api_base_url", apiInput.value.trim());
  });

  useCloudButton.addEventListener("click", () => {
    apiInput.value = DEMO_CLOUD_BACKEND;
    localStorage.setItem("sceni_api_base_url", apiInput.value);
    feedback.textContent = `Backend configurado a ${DEMO_CLOUD_BACKEND}`;
  });

  checkButton.addEventListener("click", async () => {
    feedback.textContent = "Validando conexión con backend (puede tardar por cold start)...";
    try {
      const previousValue = apiInput.value;
      const base = await checkBackendConnection(previousValue);
      apiInput.value = base;
      localStorage.setItem("sceni_api_base_url", base);
      let autoCorrected = false;
      try {
        autoCorrected = normalizeApiBaseUrl(previousValue) !== base;
      } catch {
        autoCorrected = false;
      }
      feedback.textContent = `Conexión OK con backend en ${base}.` + (autoCorrected ? " (URL corregida automáticamente)" : "");
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
      const normalizedBaseUrl = await checkBackendConnection(baseUrl);
      localStorage.setItem("sceni_api_base_url", normalizedBaseUrl);

      const createRes = await fetch(`${normalizedBaseUrl}/api/v1/opportunities`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!createRes.ok) throw new Error("No se pudo crear la oportunidad.");
      const opp = await createRes.json();

      const simulateRes = await fetch(`${normalizedBaseUrl}/api/v1/opportunities/${opp.id}/simulate`, {
        method: "POST",
      });
      if (!simulateRes.ok) throw new Error("No se pudo ejecutar la simulación.");
      const simulation = await simulateRes.json();

      const marketRes = await fetch(`${normalizedBaseUrl}/api/v1/market/ercot/${encodeURIComponent(opp.ercot_node)}`);
      if (!marketRes.ok) throw new Error("No se pudo obtener data ERCOT.");
      const market = await marketRes.json();

      renderDesignTable(simulation.designs);
      renderDashboardSummary(simulation, market);
      feedback.textContent = `Simulación lista para ${opp.name}.`; 
    } catch (error) {
      const simulation = buildLocalSimulation(payload);
      const market = buildLocalMarket(payload.ercot_node);
      renderDesignTable(simulation.designs);
      renderDashboardSummary(simulation, market);
      feedback.textContent = `Backend no disponible (${error.message}). Ejecutado en modo local de contingencia.`;
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

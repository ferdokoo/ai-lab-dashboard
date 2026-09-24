function setIndicator(card, state, { latency = null, message = "" } = {}) {
  const statusEl = card.querySelector('[data-role="status"]');
  const latencyEl = card.querySelector('[data-role="latency"]');
  const errorEl = card.querySelector('[data-role="error"]');

  statusEl.className = `status ${state}`;
  errorEl.textContent = message;
  latencyEl.textContent = state === "ok" && latency != null ? `${latency} ms` : "";
}

document.querySelectorAll(".card").forEach((card) => {
  const provider = card.dataset.provider;
  const button = card.querySelector('[data-role="check"]');

  button.addEventListener("click", async () => {
    setIndicator(card, "loading");

    try {
      const response = await fetch(`/api/${provider}/health`);
      if (response.status === 404) {
        setIndicator(card, "error", { message: "Unknown provider" });
        return;
      }

      const data = await response.json();
      switch (data.status) {
        case "ok":
          setIndicator(card, "ok", { latency: data.latency_ms });
          break;
        case "missing_key":
          setIndicator(card, "missing_key", { message: data.error || "No API key configured" });
          break;
        case "timeout":
          setIndicator(card, "timeout", { message: data.error || "Request timed out" });
          break;
        default:
          setIndicator(card, "error", { message: data.error || "Check failed" });
      }
    } catch (err) {
      setIndicator(card, "error", { message: "Network error" });
    }
  });
});

const catalog = {
  provider: null,
  models: [],
  sortKey: "id",
  sortDir: "asc",
};

const catalogSelect = document.getElementById("provider-select");
const catalogTbody = document.getElementById("catalog-tbody");
const catalogStatus = document.getElementById("catalog-status");
const catalogRefresh = document.getElementById("catalog-refresh");
const catalogToggle = document.getElementById("catalog-toggle");

function populateProviders() {
  const providers = [...document.querySelectorAll(".card")]
    .filter((card) => card.dataset.catalog !== "false")
    .map((card) => card.dataset.provider)
    .filter(Boolean);

  providers.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name[0].toUpperCase() + name.slice(1);
    catalogSelect.appendChild(option);
  });

  catalog.provider = catalogSelect.value;
}

function setCatalogStatus(message, isError = false) {
  catalogStatus.textContent = message;
  catalogStatus.className = `catalog-status${isError ? " error" : ""}`;
}

function formatContextWindow(value) {
  if (value == null) return "—";
  return Number(value).toLocaleString();
}

function formatPrice(value) {
  if (value == null) return "—";
  return `$${value.toFixed(2)}`;
}

function sortedModels() {
  const { sortKey, sortDir, models } = catalog;
  const dir = sortDir === "asc" ? 1 : -1;

  return [...models].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];

    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;

    if (typeof av === "number" && typeof bv === "number") {
      return (av - bv) * dir;
    }
    return String(av).localeCompare(String(bv)) * dir;
  });
}

function renderCatalog() {
  catalogTbody.innerHTML = "";

  const models = sortedModels();
  if (models.length === 0) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 4;
    td.className = "catalog-empty";
    td.textContent = "No models available for this provider.";
    tr.appendChild(td);
    catalogTbody.appendChild(tr);

    document.querySelectorAll("#catalog-table th").forEach((th) => {
      th.removeAttribute("data-dir");
    });
    return;
  }

  models.forEach((model) => {
    const tr = document.createElement("tr");

    const idCell = document.createElement("td");
    idCell.textContent = model.id;

    const ctxCell = document.createElement("td");
    ctxCell.textContent = formatContextWindow(model.context_window);
    if (model.context_window == null) ctxCell.className = "blank";

    const inCell = document.createElement("td");
    inCell.textContent = formatPrice(model.input_price_per_million);
    if (model.input_price_per_million == null) inCell.className = "blank";

    const outCell = document.createElement("td");
    outCell.textContent = formatPrice(model.output_price_per_million);
    if (model.output_price_per_million == null) outCell.className = "blank";

    tr.append(idCell, ctxCell, inCell, outCell);
    catalogTbody.appendChild(tr);
  });

  document.querySelectorAll("#catalog-table th").forEach((th) => {
    th.dataset.dir = th.dataset.key === catalog.sortKey ? catalog.sortDir : "";
  });
}

async function loadModels(refresh) {
  if (!catalog.provider) return;

  setCatalogStatus("Loading…");
  const url = `/api/${catalog.provider}/models${refresh ? "?refresh=true" : ""}`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      let message = `HTTP ${response.status}`;
      try {
        const payload = await response.json();
        message = payload.detail || message;
      } catch (_) {}
      throw new Error(message);
    }

    const data = await response.json();
    catalog.models = data.models || [];
    renderCatalog();
    setCatalogStatus(data.cached ? "Served from cache" : "Fetched live");
  } catch (err) {
    catalog.models = [];
    renderCatalog();
    setCatalogStatus(err.message || "Failed to load models", true);
  }
}

catalogSelect.addEventListener("change", () => {
  catalog.provider = catalogSelect.value;
  loadModels(false);
});

catalogRefresh.addEventListener("click", () => {
  loadModels(true);
});

catalogToggle.addEventListener("click", () => {
  const body = document.getElementById("catalog-body");
  const hidden = body.classList.toggle("hidden");
  catalogToggle.textContent = hidden ? "Show" : "Hide";
  catalogToggle.setAttribute("aria-expanded", String(!hidden));
});

document.querySelectorAll("#catalog-table th.sortable").forEach((th) => {
  th.addEventListener("click", () => {
    const key = th.dataset.key;
    if (catalog.sortKey === key) {
      catalog.sortDir = catalog.sortDir === "asc" ? "desc" : "asc";
    } else {
      catalog.sortKey = key;
      catalog.sortDir = "asc";
    }
    renderCatalog();
  });
});

populateProviders();
loadModels(false);
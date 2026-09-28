const THEME_KEY = "theme";

function showToast(message, isError = false) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "toast" + (isError ? " error" : "");
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function setButtonLoading(button, loading) {
  if (loading) {
    button.disabled = true;
    button.dataset.original = button.textContent;
    button.textContent = "";
    const spinner = document.createElement("span");
    spinner.className = "spinner";
    button.appendChild(spinner);
  } else {
    button.disabled = false;
    if (button.dataset.original != null) {
      button.textContent = button.dataset.original;
    }
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const toggle = document.getElementById("theme-toggle");
  toggle.textContent = theme === "dark" ? "Light mode" : "Dark mode";
}

function navigate() {
  const pageId = (location.hash || "#home").slice(1) || "home";
  const target =
    document.getElementById("page-" + pageId) || document.getElementById("page-home");

  document.querySelectorAll(".page").forEach((page) => page.classList.add("hidden"));
  target.classList.remove("hidden");

  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.toggle("active", link.dataset.page === target.id.replace("page-", ""));
  });
}

window.addEventListener("hashchange", navigate);

applyTheme(localStorage.getItem(THEME_KEY) || "light");

document.getElementById("theme-toggle").addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
  localStorage.setItem(THEME_KEY, next);
});

navigate();

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
    setButtonLoading(button, true);

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
      showToast(`${provider} health check failed: network error`, true);
    } finally {
      setButtonLoading(button, false);
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

const runner = {
  provider: null,
  models: [],
  model: null,
};

const runnerProvider = document.getElementById("runner-provider");
const runnerModel = document.getElementById("runner-model");
const runnerModelLabel = document.getElementById("runner-model-label");
const runnerRefresh = document.getElementById("runner-models-refresh");
const runnerPrompt = document.getElementById("runner-prompt");
const runnerRun = document.getElementById("runner-run");
const runnerStatus = document.getElementById("runner-status");
const runnerOutput = document.getElementById("runner-output");
const runnerText = document.getElementById("runner-text");
const runnerCopy = document.getElementById("runner-copy");
const runnerClear = document.getElementById("runner-clear");
const runnerStream = document.getElementById("runner-stream");
const runnerRateLimit = document.getElementById("runner-rate-limit");
const runnerRateLimitBody = document.getElementById("runner-rate-limit-body");
const runnerRateLimitToggle = document.getElementById("runner-rate-limit-toggle");

function populateRunnerProviders() {
  const names = [...document.querySelectorAll(".card")]
    .map((card) => card.dataset.provider)
    .filter(Boolean);

  names.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name[0].toUpperCase() + name.slice(1);
    runnerProvider.appendChild(option);
  });

  runner.provider = runnerProvider.value;
}

function syncRunnerMode() {
  const isSearch = runner.provider === "tavily";
  runnerModel.style.display = isSearch ? "none" : "";
  runnerModelLabel.style.display = isSearch ? "none" : "";
  runnerRefresh.style.display = isSearch ? "none" : "";
  runnerPrompt.placeholder = isSearch ? "Enter a search query…" : "Enter a prompt…";
}

function setRunnerModelOptions(models) {
  runnerModel.innerHTML = "";
  models.forEach((model) => {
    const option = document.createElement("option");
    option.value = model.id;
    option.textContent = model.id;
    runnerModel.appendChild(option);
  });
  runner.model = runnerModel.value;
}

async function loadRunnerModels(refresh) {
  if (!runner.provider || runner.provider === "tavily") return;

  setRunnerStatus("Loading models…");
  const url = `/api/${runner.provider}/models${refresh ? "?refresh=true" : ""}`;

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
    runner.models = data.models || [];
    setRunnerModelOptions(runner.models);
    setRunnerStatus("");
  } catch (err) {
    runner.models = [];
    setRunnerModelOptions([]);
    setRunnerStatus(err.message || "Failed to load models", true);
  }
}

function setRunnerStatus(message, isError = false) {
  runnerStatus.textContent = message;
  runnerStatus.className = `runner-status${isError ? " error" : ""}`;
}

function formatMetric(value) {
  if (value == null) return "—";
  return value.toLocaleString();
}

function renderRunnerResult(data) {
  runnerText.textContent = data.text || "";
  document.querySelector('[data-metric="prompt_tokens"]').textContent =
    formatMetric(data.prompt_tokens);
  document.querySelector('[data-metric="completion_tokens"]').textContent =
    formatMetric(data.completion_tokens);
  document.querySelector('[data-metric="latency_ms"]').textContent =
    formatMetric(data.latency_ms);
  runnerOutput.classList.remove("hidden");
  renderRateLimits(data.rate_limit);
}

function renderRateLimits(rateLimit) {
  if (!rateLimit || Object.keys(rateLimit).length === 0) {
    runnerRateLimit.classList.add("hidden");
    return;
  }

  runnerRateLimitBody.innerHTML = "";
  Object.entries(rateLimit).forEach(([key, value]) => {
    const field = document.createElement("div");
    field.className = "runner-rate-limit-field";

    const label = document.createElement("span");
    label.className = "key";
    label.textContent = key;

    const val = document.createElement("span");
    val.className = "value";
    val.textContent = value;

    field.append(label, val);
    runnerRateLimitBody.appendChild(field);
  });
  runnerRateLimit.classList.remove("hidden");
  runnerRateLimitBody.classList.remove("hidden");
  runnerRateLimitToggle.textContent = "Hide";
}

async function runRequest() {
  const isSearch = runner.provider === "tavily";
  const value = runnerPrompt.value.trim();

  if (!value) {
    setRunnerStatus(isSearch ? "Query cannot be empty" : "Prompt cannot be empty", true);
    return;
  }
  if (!isSearch && !runner.model) {
    setRunnerStatus("Select a model", true);
    return;
  }

  setRunnerStatus("Running…");
  runnerOutput.classList.remove("hidden");
  runnerText.textContent = "";
  runnerRateLimit.classList.add("hidden");
  setMetric("prompt_tokens", "—");
  setMetric("completion_tokens", "—");
  setMetric("latency_ms", "—");
  setButtonLoading(runnerRun, true);

  try {
    const route = isSearch
      ? `/api/${runner.provider}/search`
      : `/api/${runner.provider}/request`;
    const body = isSearch
      ? { query: value }
      : { model: runner.model, prompt: value };

    if (!isSearch && runnerStream.checked) {
      await streamRequest(route + "/stream", body);
    } else {
      await plainRequest(route, body);
    }
    setRunnerStatus("");
  } catch (err) {
    setRunnerStatus(err.message || "Request failed", true);
    showToast(err.message || "Request failed", true);
  } finally {
    setButtonLoading(runnerRun, false);
  }
}

async function plainRequest(route, body) {
  const response = await fetch(route, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch (_) {}
    throw new Error(message);
  }

  const data = await response.json();
  renderRunnerResult(data);
}

async function streamRequest(route, body) {
  const response = await fetch(route, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch (_) {}
    throw new Error(message);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const line = frame.split("\n").find((l) => l.startsWith("data: "));
      if (!line) continue;

      let payload;
      try {
        payload = JSON.parse(line.slice(6));
      } catch (_) {
        continue;
      }

      if (payload.event === "delta") {
        runnerText.textContent += payload.content || "";
      } else if (payload.event === "done") {
        setMetric("prompt_tokens", formatMetric(payload.prompt_tokens));
        setMetric("completion_tokens", formatMetric(payload.completion_tokens));
        setMetric("latency_ms", formatMetric(payload.latency_ms));
      } else if (payload.event === "error") {
        setRunnerStatus(payload.content || "Stream failed", true);
      }
    }
  }
}

runnerProvider.addEventListener("change", () => {
  runner.provider = runnerProvider.value;
  runner.model = null;
  runner.models = [];
  setRunnerModelOptions([]);
  runnerOutput.classList.add("hidden");
  syncRunnerMode();
  loadRunnerModels(false);
});

runnerModel.addEventListener("change", () => {
  runner.model = runnerModel.value;
});

runnerRefresh.addEventListener("click", () => {
  loadRunnerModels(true);
});

runnerRun.addEventListener("click", runRequest);

runnerRateLimitToggle.addEventListener("click", () => {
  const hidden = runnerRateLimitBody.classList.toggle("hidden");
  runnerRateLimitToggle.textContent = hidden ? "Show" : "Hide";
});

runnerPrompt.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    runRequest();
  }
});

function setMetric(key, value) {
  document.querySelector(`[data-metric="${key}"]`).textContent = value;
}

runnerCopy.addEventListener("click", async () => {
  const text = runnerText.textContent;
  if (!text) return;

  try {
    await navigator.clipboard.writeText(text);
    setRunnerStatus("Copied to clipboard");
  } catch (err) {
    setRunnerStatus("Copy failed", true);
  }
});

runnerClear.addEventListener("click", () => {
  runnerText.textContent = "";
  setMetric("prompt_tokens", "—");
  setMetric("completion_tokens", "—");
  setMetric("latency_ms", "—");
  runnerOutput.classList.add("hidden");
  setRunnerStatus("");
});

populateRunnerProviders();
syncRunnerMode();
loadRunnerModels(false);

const balanceGrid = document.getElementById("balance-grid");
const balanceRefreshAll = document.getElementById("balance-refresh");

const balanceProviders = [...document.querySelectorAll(".card")]
  .filter((card) => card.dataset.balance !== "false")
  .map((card) => card.dataset.provider)
  .filter(Boolean);

function humanizeKey(key) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatBalanceValue(value) {
  if (value == null) return "—";
  if (typeof value === "number") {
    return value.toLocaleString(undefined, {
      maximumFractionDigits: 6,
    });
  }
  return String(value);
}

function buildBalanceCard(provider) {
  const card = document.createElement("article");
  card.className = "balance-card";
  card.dataset.provider = provider;

  const name = provider[0].toUpperCase() + provider.slice(1);

  const top = document.createElement("div");
  top.className = "balance-card-top";

  const title = document.createElement("h3");
  title.textContent = name;
  top.appendChild(title);

  const button = document.createElement("button");
  button.type = "button";
  button.textContent = "Refresh";
  button.addEventListener("click", () => loadBalance(provider, card));
  top.appendChild(button);

  const body = document.createElement("div");
  body.className = "balance-body";

  card.append(top, body);
  return card;
}

function renderBalanceCard(card, data) {
  const body = card.querySelector(".balance-body");
  body.innerHTML = "";

  if (data.supported) {
    const fields = document.createElement("div");
    fields.className = "balance-fields";
    Object.entries(data.fields || {}).forEach(([key, value]) => {
      const row = document.createElement("div");
      row.className = "balance-field";

      const label = document.createElement("span");
      label.className = "key";
      label.textContent = humanizeKey(key);

      const val = document.createElement("span");
      val.className = "value";
      val.textContent = formatBalanceValue(value);

      row.append(label, val);
      fields.appendChild(row);
    });
    body.appendChild(fields);

    if (data.raw) {
      const details = document.createElement("details");
      details.className = "balance-raw";
      const summary = document.createElement("summary");
      summary.textContent = "Raw response";
      const pre = document.createElement("pre");
      pre.textContent = JSON.stringify(data.raw, null, 2);
      details.append(summary, pre);
      body.appendChild(details);
    }
    return;
  }

  const message = document.createElement("p");
  message.className = "balance-message";
  message.textContent = data.message || "Not available";
  body.appendChild(message);

  if (data.billing_url) {
    const link = document.createElement("a");
    link.className = "balance-link";
    link.href = data.billing_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "View billing page";
    body.appendChild(link);
  }
}

async function loadBalance(provider, card) {
  const body = card.querySelector(".balance-body");
  body.innerHTML = "";
  const loading = document.createElement("p");
  loading.className = "balance-message";
  loading.textContent = "Loading…";
  body.appendChild(loading);

  try {
    const response = await fetch(`/api/${provider}/balance`);

    let data;
    try {
      data = await response.json();
    } catch (_) {
      throw new Error(`HTTP ${response.status}`);
    }

    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }

    renderBalanceCard(card, data);
  } catch (err) {
    body.innerHTML = "";
    const message = document.createElement("p");
    message.className = "balance-message error";
    message.textContent = err.message || "Failed to load balance";
    body.appendChild(message);
  }
}

balanceProviders.forEach((provider) => {
  const card = buildBalanceCard(provider);
  balanceGrid.appendChild(card);
  loadBalance(provider, card);
});

balanceRefreshAll.addEventListener("click", () => {
  balanceGrid.querySelectorAll(".balance-card").forEach((card) => {
    loadBalance(card.dataset.provider, card);
  });
});

const history = {
  provider: "",
  model: "",
  start: "",
  end: "",
  limit: 50,
  offset: 0,
  total: 0,
  items: [],
  sortKey: "timestamp",
  sortDir: "desc",
};

const historyProvider = document.getElementById("history-provider");
const historyModel = document.getElementById("history-model");
const historyStart = document.getElementById("history-start");
const historyEnd = document.getElementById("history-end");
const historyRefresh = document.getElementById("history-refresh");
const historyExport = document.getElementById("history-export");
const historyTbody = document.getElementById("history-tbody");
const historyStatus = document.getElementById("history-status");
const historyPrev = document.getElementById("history-prev");
const historyNext = document.getElementById("history-next");
const historyPageInfo = document.getElementById("history-page-info");

function populateHistoryProviders() {
  const providers = [...document.querySelectorAll(".card")]
    .map((card) => card.dataset.provider)
    .filter(Boolean);

  providers.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name[0].toUpperCase() + name.slice(1);
    historyProvider.appendChild(option);
  });
}

function setHistoryStatus(message, isError = false) {
  historyStatus.textContent = message;
  historyStatus.className = `history-status${isError ? " error" : ""}`;
}

function historyFilters() {
  const params = new URLSearchParams();
  if (history.provider) params.set("provider", history.provider);
  if (history.model) params.set("model", history.model);
  if (history.start) params.set("start", history.start);
  if (history.end) params.set("end", history.end);
  return params;
}

function formatCount(value) {
  if (value == null) return "—";
  return value.toLocaleString();
}

function formatCost(value) {
  if (value == null) return "—";
  return "$" + value.toLocaleString(undefined, { maximumFractionDigits: 8 });
}

function formatLatency(value) {
  if (value == null) return "—";
  return `${value.toLocaleString()} ms`;
}

function formatTimestamp(value) {
  if (value == null) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function sortedHistory() {
  const { sortKey, sortDir, items } = history;
  const dir = sortDir === "asc" ? 1 : -1;

  return [...items].sort((a, b) => {
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

function renderHistory() {
  historyTbody.innerHTML = "";

  const items = sortedHistory();
  if (items.length === 0) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 7;
    td.className = "catalog-empty";
    td.textContent = "No requests recorded yet.";
    tr.appendChild(td);
    historyTbody.appendChild(tr);
    updateHistoryPagination();
    return;
  }

  items.forEach((row) => {
    const tr = document.createElement("tr");

    const ts = document.createElement("td");
    ts.textContent = formatTimestamp(row.timestamp);

    const provider = document.createElement("td");
    provider.textContent = row.provider;

    const model = document.createElement("td");
    model.textContent = row.model || "—";
    if (!row.model) model.className = "blank";

    const pt = document.createElement("td");
    pt.textContent = formatCount(row.prompt_tokens);
    if (row.prompt_tokens == null) pt.className = "blank";

    const ct = document.createElement("td");
    ct.textContent = formatCount(row.completion_tokens);
    if (row.completion_tokens == null) ct.className = "blank";

    const cost = document.createElement("td");
    cost.textContent = formatCost(row.estimated_cost_usd);
    if (row.estimated_cost_usd == null) cost.className = "blank";

    const latency = document.createElement("td");
    latency.textContent = formatLatency(row.latency_ms);
    if (row.latency_ms == null) latency.className = "blank";

    tr.append(ts, provider, model, pt, ct, cost, latency);
    historyTbody.appendChild(tr);
  });

  updateHistoryPagination();
  document.querySelectorAll("#history-table th.sortable").forEach((th) => {
    th.dataset.dir = th.dataset.key === history.sortKey ? history.sortDir : "";
  });
}

function updateHistoryPagination() {
  const { total, offset, limit, items } = history;
  const shown = items.length;
  const from = total === 0 ? 0 : offset + 1;
  const to = total === 0 ? 0 : offset + shown;

  historyPageInfo.textContent = total === 0 ? "No results" : `${from}–${to} of ${total}`;
  historyPrev.disabled = offset === 0;
  historyNext.disabled = offset + limit >= total;
}

async function loadHistory() {
  setHistoryStatus("Loading…");
  const params = historyFilters();
  params.set("limit", history.limit);
  params.set("offset", history.offset);

  try {
    const response = await fetch(`/api/history?${params.toString()}`);
    let data;
    try {
      data = await response.json();
    } catch (_) {
      throw new Error(`HTTP ${response.status}`);
    }
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);

    history.items = data.items || [];
    history.total = data.total || 0;
    renderHistory();
    setHistoryStatus("");
  } catch (err) {
    history.items = [];
    history.total = 0;
    renderHistory();
    setHistoryStatus(err.message || "Failed to load history", true);
  }
}

function resetHistoryPage() {
  history.offset = 0;
  loadHistory();
}

historyProvider.addEventListener("change", () => {
  history.provider = historyProvider.value;
  resetHistoryPage();
});

historyModel.addEventListener("change", () => {
  history.model = historyModel.value.trim();
  resetHistoryPage();
});

historyStart.addEventListener("change", () => {
  history.start = historyStart.value;
  resetHistoryPage();
});

historyEnd.addEventListener("change", () => {
  history.end = historyEnd.value;
  resetHistoryPage();
});

historyRefresh.addEventListener("click", resetHistoryPage);

historyPrev.addEventListener("click", () => {
  history.offset = Math.max(0, history.offset - history.limit);
  loadHistory();
});

historyNext.addEventListener("click", () => {
  history.offset += history.limit;
  loadHistory();
});

historyExport.addEventListener("click", () => {
  const params = historyFilters();
  window.location.href = `/api/history/export${params.toString() ? "?" + params.toString() : ""}`;
});

document.querySelectorAll("#history-table th.sortable").forEach((th) => {
  th.addEventListener("click", () => {
    const key = th.dataset.key;
    if (history.sortKey === key) {
      history.sortDir = history.sortDir === "asc" ? "desc" : "asc";
    } else {
      history.sortKey = key;
      history.sortDir = key === "timestamp" ? "desc" : "asc";
    }
    renderHistory();
  });
});

populateHistoryProviders();
loadHistory();

const costCalc = {
  provider: null,
  models: [],
  model: null,
};

const costProvider = document.getElementById("cost-provider");
const costModel = document.getElementById("cost-model");
const costPromptTokens = document.getElementById("cost-prompt-tokens");
const costCompletionTokens = document.getElementById("cost-completion-tokens");
const costCalculate = document.getElementById("cost-calculate");
const costStatus = document.getElementById("cost-status");
const costEstimate = document.getElementById("cost-estimate");
const costDetail = document.getElementById("cost-detail");

function populateCostProviders() {
  const providers = [...document.querySelectorAll(".card")]
    .filter((card) => card.dataset.catalog !== "false")
    .map((card) => card.dataset.provider)
    .filter(Boolean);

  providers.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name[0].toUpperCase() + name.slice(1);
    costProvider.appendChild(option);
  });

  costCalc.provider = costProvider.value;
}

function setCostModelOptions(models) {
  costModel.innerHTML = "";
  models.forEach((model) => {
    const option = document.createElement("option");
    option.value = model.id;
    option.textContent = model.id;
    costModel.appendChild(option);
  });
  costCalc.model = costModel.value;
}

async function loadCostModels() {
  if (!costCalc.provider) return;

  setCostModelOptions([]);
  const url = `/api/${costCalc.provider}/models`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    costCalc.models = data.models || [];
    setCostModelOptions(costCalc.models);
  } catch (err) {
    costCalc.models = [];
    setCostModelOptions([]);
  }
}

function setCostStatus(message, isError = false) {
  costStatus.textContent = message;
  costStatus.className = `cost-status${isError ? " error" : ""}`;
}

function renderCostResult(data) {
  if (data.estimated_cost_usd == null) {
    costEstimate.textContent = "Unknown";
    costDetail.textContent = data.pricing_source
      ? "No cached price for this model — refresh the catalog and try again."
      : "No cached pricing available for this model.";
    costEstimate.className = "cost-estimate blank";
    return;
  }

  costEstimate.className = "cost-estimate";
  costEstimate.textContent =
    "$" + data.estimated_cost_usd.toLocaleString(undefined, { maximumFractionDigits: 8 });

  const parts = [];
  if (data.input_price_per_million != null) {
    parts.push(`in $${data.input_price_per_million.toFixed(2)}/1M`);
  }
  if (data.output_price_per_million != null) {
    parts.push(`out $${data.output_price_per_million.toFixed(2)}/1M`);
  }
  if (data.pricing_source) {
    parts.push(`source: ${data.pricing_source}`);
  }
  costDetail.textContent = parts.join(" · ");
}

async function calculateCost() {
  if (!costCalc.provider || !costCalc.model) {
    setCostStatus("Select a provider and model", true);
    return;
  }

  const promptTokens = Number(costPromptTokens.value);
  const completionTokens = Number(costCompletionTokens.value);
  const valid =
    Number.isFinite(promptTokens) && promptTokens >= 0 &&
    Number.isFinite(completionTokens) && completionTokens >= 0;
  if (!valid) {
    setCostStatus("Enter non-negative token counts", true);
    return;
  }

  setCostStatus("Estimating…");
  const params = new URLSearchParams({
    provider: costCalc.provider,
    model: costCalc.model,
    prompt_tokens: String(promptTokens),
    completion_tokens: String(completionTokens),
  });

  try {
    const response = await fetch(`/api/cost?${params.toString()}`);
    let data;
    try {
      data = await response.json();
    } catch (_) {
      throw new Error(`HTTP ${response.status}`);
    }
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);

    renderCostResult(data);
    setCostStatus("");
  } catch (err) {
    setCostStatus(err.message || "Estimate failed", true);
  }
}

costProvider.addEventListener("change", () => {
  costCalc.provider = costProvider.value;
  costCalc.model = null;
  setCostModelOptions([]);
  loadCostModels();
});

costModel.addEventListener("change", () => {
  costCalc.model = costModel.value;
});

costCalculate.addEventListener("click", calculateCost);

populateCostProviders();
loadCostModels();

const compareProviders = [...document.querySelectorAll(".card")]
  .map((card) => card.dataset.provider)
  .filter(Boolean)
  .filter((name) => name !== "tavily");

const compareTargets = document.getElementById("compare-targets");
const compareAddTarget = document.getElementById("compare-add-target");
const comparePrompt = document.getElementById("compare-prompt");
const compareRun = document.getElementById("compare-run");
const compareStatus = document.getElementById("compare-status");
const compareResults = document.getElementById("compare-results");

function setCompareStatus(message, isError = false) {
  compareStatus.textContent = message;
  compareStatus.className = `compare-status${isError ? " error" : ""}`;
}

async function loadTargetModels(provider, modelSelect) {
  modelSelect.innerHTML = "";
  modelSelect.disabled = true;
  const placeholder = document.createElement("option");
  placeholder.textContent = "Loading…";
  modelSelect.appendChild(placeholder);

  try {
    const response = await fetch(`/api/${provider}/models`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const models = data.models || [];

    modelSelect.innerHTML = "";
    models.forEach((model) => {
      const option = document.createElement("option");
      option.value = model.id;
      option.textContent = model.id;
      modelSelect.appendChild(option);
    });
    modelSelect.disabled = false;
  } catch (_) {
    modelSelect.innerHTML = "";
    const option = document.createElement("option");
    option.textContent = "Failed to load";
    modelSelect.appendChild(option);
  }
}

function createTargetRow() {
  const row = document.createElement("div");
  row.className = "compare-target-row";

  const providerLabel = document.createElement("label");
  providerLabel.textContent = "Provider";
  const providerSelect = document.createElement("select");
  compareProviders.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name[0].toUpperCase() + name.slice(1);
    providerSelect.appendChild(option);
  });

  const modelLabel = document.createElement("label");
  modelLabel.textContent = "Model";
  const modelSelect = document.createElement("select");
  modelSelect.disabled = true;

  const removeButton = document.createElement("button");
  removeButton.type = "button";
  removeButton.textContent = "Remove";
  removeButton.addEventListener("click", () => row.remove());

  row.append(providerLabel, providerSelect, modelLabel, modelSelect, removeButton);

  providerSelect.addEventListener("change", () => {
    loadTargetModels(providerSelect.value, modelSelect);
  });

  loadTargetModels(providerSelect.value, modelSelect);

  compareTargets.appendChild(row);
  return row;
}

function collectTargets() {
  const targets = [];
  compareTargets.querySelectorAll(".compare-target-row").forEach((row) => {
    const [providerSelect, modelSelect] = row.querySelectorAll("select");
    const provider = providerSelect.value;
    const model = modelSelect.value;
    if (provider && model && !modelSelect.disabled) {
      targets.push({ provider, model });
    }
  });
  return targets;
}

function compareBadge(label, value) {
  const span = document.createElement("span");
  const strong = document.createElement("b");
  strong.textContent = value;
  span.append(`${label}: `, strong);
  return span;
}

function renderCompareResults(results) {
  compareResults.innerHTML = "";

  results.forEach((result) => {
    const card = document.createElement("article");
    card.className = "compare-card";

    const title = document.createElement("h3");
    title.textContent = result.provider.charAt(0).toUpperCase() + result.provider.slice(1);

    const model = document.createElement("div");
    model.className = "compare-card-model";
    model.textContent = result.model || "—";

    card.append(title, model);

    if (result.error) {
      card.classList.add("error-card");
      const error = document.createElement("p");
      error.className = "compare-card-error";
      error.textContent = result.error;
      card.appendChild(error);
      compareResults.appendChild(card);
      return;
    }

    const badges = document.createElement("div");
    badges.className = "compare-badges";
    badges.append(
      compareBadge("latency", result.latency_ms != null ? `${result.latency_ms.toLocaleString()} ms` : "—"),
      compareBadge("in", result.prompt_tokens != null ? result.prompt_tokens.toLocaleString() : "—"),
      compareBadge("out", result.completion_tokens != null ? result.completion_tokens.toLocaleString() : "—"),
      compareBadge("cost", result.estimated_cost_usd != null
        ? "$" + result.estimated_cost_usd.toLocaleString(undefined, { maximumFractionDigits: 8 })
        : "—")
    );

    const pre = document.createElement("pre");
    pre.textContent = result.text || "";

    card.append(badges, pre);
    compareResults.appendChild(card);
  });
}

async function runComparison() {
  const prompt = comparePrompt.value.trim();
  if (!prompt) {
    setCompareStatus("Prompt cannot be empty", true);
    return;
  }

  const targets = collectTargets();
  if (targets.length === 0) {
    setCompareStatus("Select at least one model", true);
    return;
  }

  setCompareStatus("Running…");
  setButtonLoading(compareRun, true);
  compareResults.innerHTML = "";

  try {
    const response = await fetch("/api/broadcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, targets }),
    });
    let data;
    try {
      data = await response.json();
    } catch (_) {
      throw new Error(`HTTP ${response.status}`);
    }
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);

    renderCompareResults(data.results || []);
    setCompareStatus("");
  } catch (err) {
    setCompareStatus(err.message || "Comparison failed", true);
    showToast(err.message || "Comparison failed", true);
  } finally {
    setButtonLoading(compareRun, false);
  }
}

compareAddTarget.addEventListener("click", createTargetRow);
compareRun.addEventListener("click", runComparison);

createTargetRow();

const keysGrid = document.getElementById("keys-grid");
const keysRefresh = document.getElementById("keys-refresh");

function buildKeysCard(entry) {
  const card = document.createElement("article");
  card.className = "keys-card";

  const title = document.createElement("h3");
  title.textContent = entry.provider[0].toUpperCase() + entry.provider.slice(1);
  card.appendChild(title);

  const value = document.createElement("span");
  value.className = "key-value";

  if (entry.note) {
    value.classList.add("missing");
    value.textContent = entry.note;
  } else if (entry.configured) {
    value.textContent = entry.masked;
  } else {
    value.classList.add("missing");
    value.textContent = "Not configured";
  }

  card.appendChild(value);
  return card;
}

async function loadKeys() {
  keysGrid.innerHTML = "";
  try {
    const response = await fetch("/api/keys");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    (data.keys || []).forEach((entry) => keysGrid.appendChild(buildKeysCard(entry)));
  } catch (err) {
    showToast("Failed to load keys", true);
  }
}

keysRefresh.addEventListener("click", loadKeys);
loadKeys();

const usageGroup = document.getElementById("usage-group");
const usageChartCanvas = document.getElementById("usage-chart");
const usageEmpty = document.getElementById("usage-empty");

let usageChart = null;

function chartColors() {
  const styles = getComputedStyle(document.documentElement);
  return {
    text: styles.getPropertyValue("--text").trim() || "#1b2430",
    muted: styles.getPropertyValue("--muted").trim() || "#63707f",
  };
}

function renderUsageChart(points) {
  if (usageChart) {
    usageChart.destroy();
    usageChart = null;
  }

  if (points.length === 0) {
    usageEmpty.textContent = "No usage recorded yet — run a request to see the chart.";
    usageEmpty.classList.remove("hidden");
    usageChartCanvas.style.display = "none";
    return;
  }

  if (typeof Chart === "undefined") {
    usageEmpty.textContent = "Chart library not loaded — usage data unavailable.";
    usageEmpty.classList.remove("hidden");
    usageChartCanvas.style.display = "none";
    return;
  }

  usageEmpty.classList.add("hidden");
  usageChartCanvas.style.display = "";
  const colors = chartColors();

  usageChart = new Chart(usageChartCanvas, {
    type: "line",
    data: {
      labels: points.map((p) => p.bucket),
      datasets: [
        {
          label: "Tokens",
          data: points.map((p) => p.tokens),
          yAxisID: "y",
          borderColor: "#2563eb",
          backgroundColor: "rgba(37, 99, 235, 0.15)",
          fill: true,
          tension: 0.3,
        },
        {
          label: "Spend ($)",
          data: points.map((p) => p.cost),
          yAxisID: "y1",
          borderColor: "#22c55e",
          backgroundColor: "rgba(34, 197, 94, 0.15)",
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: "Tokens", color: colors.muted },
          ticks: { color: colors.muted },
          grid: { color: "rgba(128, 128, 128, 0.15)" },
        },
        y1: {
          beginAtZero: true,
          position: "right",
          title: { display: true, text: "Spend ($)", color: colors.muted },
          ticks: { color: colors.muted },
          grid: { drawOnChartArea: false },
        },
        x: {
          ticks: { color: colors.muted },
          grid: { color: "rgba(128, 128, 128, 0.15)" },
        },
      },
      plugins: {
        legend: { labels: { color: colors.text } },
      },
    },
  });
}

async function loadUsage() {
  try {
    const response = await fetch(`/api/history/usage?group=${usageGroup.value}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    renderUsageChart(data.points || []);
  } catch (err) {
    showToast("Failed to load usage", true);
  }
}

usageGroup.addEventListener("change", loadUsage);
loadUsage();
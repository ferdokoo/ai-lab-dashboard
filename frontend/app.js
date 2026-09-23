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
(function () {
  function parseChartConfig(node) {
    const raw = node.getAttribute("data-chart");
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch (error) {
      return null;
    }
  }

  function renderCharts() {
    const nodes = document.querySelectorAll("[data-chart]");
    if (!nodes.length || typeof Chart === "undefined") return;

    nodes.forEach((node) => {
      const config = parseChartConfig(node);
      if (!config) return;
      const context = node.getContext("2d");
      new Chart(context, {
        type: config.type || "line",
        data: {
          labels: config.labels || [],
          datasets: config.datasets || [],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "bottom" },
          },
          scales: {
            y: { beginAtZero: true },
          },
        },
      });
    });
  }

  function wireModeToggles() {
    const forms = document.querySelectorAll("[data-scenario-form]");
    forms.forEach((form) => {
      const radios = form.querySelectorAll("[data-mode-toggle]");
      const arrivals = form.querySelectorAll('textarea[name$="arrivals_text"]');

      function syncVisibility() {
        const selected = form.querySelector("[data-mode-toggle]:checked");
        const fixed = selected && selected.value === "fixed";
        arrivals.forEach((field) => {
          field.style.opacity = fixed ? "1" : "0.7";
        });
      }

      radios.forEach((radio) => radio.addEventListener("change", syncVisibility));
      syncVisibility();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    wireModeToggles();
    renderCharts();
  });
})();

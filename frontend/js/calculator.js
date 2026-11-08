(() => {
  const API_BASE = window.MEBEL_API_BASE || "/api/v1";

  const state = {
    step: 1,
    furniture_type: null,
    dimensions: { width: 1800, height: 2400, depth: 600 },
    material_grade: "стандарт",
    hardware_brand: "базовая",
    extra_options: [],
    result: null,
  };

  const els = {
    stepPanels: [...document.querySelectorAll("[data-step-panel]")],
    stepPills: [...document.querySelectorAll("[data-step-pill]")],
    typeCards: [...document.querySelectorAll("[data-furniture-type]")],
    width: document.getElementById("dim-width"),
    height: document.getElementById("dim-height"),
    depth: document.getElementById("dim-depth"),
    widthVal: document.getElementById("dim-width-val"),
    heightVal: document.getElementById("dim-height-val"),
    depthVal: document.getElementById("dim-depth-val"),
    material: document.getElementById("material-grade"),
    hardware: document.getElementById("hardware-brand"),
    extras: [...document.querySelectorAll("[data-extra]")],
    priceRange: document.getElementById("price-range"),
    priceBreakdown: document.getElementById("price-breakdown"),
    priceSummary: document.getElementById("price-summary"),
    clientName: document.getElementById("client-name"),
    clientPhone: document.getElementById("client-phone"),
    btnPrev: document.getElementById("btn-prev"),
    btnNext: document.getElementById("btn-next"),
    btnSubmit: document.getElementById("btn-submit-lead"),
  };

  function toast(message, type = "info") {
    const stack = document.getElementById("toast-stack");
    if (!stack) return;
    const node = document.createElement("div");
    node.className = `toast ${type}`;
    node.textContent = message;
    stack.appendChild(node);
    setTimeout(() => node.remove(), 4200);
  }

  window.mebelToast = toast;

  function formatKzt(value) {
    return new Intl.NumberFormat("ru-KZ").format(Math.round(value)) + " ₸";
  }

  function syncDimsUi() {
    els.width.value = state.dimensions.width;
    els.height.value = state.dimensions.height;
    els.depth.value = state.dimensions.depth;
    els.widthVal.textContent = `${state.dimensions.width} мм`;
    els.heightVal.textContent = `${state.dimensions.height} мм`;
    els.depthVal.textContent = `${state.dimensions.depth} мм`;
  }

  function renderSteps() {
    els.stepPanels.forEach((panel) => {
      const step = Number(panel.dataset.stepPanel);
      panel.classList.toggle("hidden", step !== state.step);
    });
    els.stepPills.forEach((pill) => {
      const step = Number(pill.dataset.stepPill);
      pill.classList.toggle("active", step === state.step);
      pill.classList.toggle("done", step < state.step);
    });
    els.btnPrev.disabled = state.step === 1;
    els.btnNext.classList.toggle("hidden", state.step === 4);
    els.btnSubmit.classList.toggle("hidden", state.step !== 4);
  }

  async function recalculate() {
    if (!state.furniture_type) return;
    try {
      const response = await fetch(`${API_BASE}/calculator/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          furniture_type: state.furniture_type,
          dimensions: state.dimensions,
          material_grade: state.material_grade,
          hardware_brand: state.hardware_brand,
          extra_options: state.extra_options,
        }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Ошибка расчёта");
      }
      state.result = await response.json();
      els.priceRange.textContent = `${formatKzt(state.result.price_min)} – ${formatKzt(state.result.price_max)}`;
      const b = state.result.breakdown;
      els.priceBreakdown.innerHTML = `
        <div>Материал: ${formatKzt(b.material_cost)}</div>
        <div>Фурнитура: ${formatKzt(b.hardware_cost)}</div>
        <div>Сборка: ${formatKzt(b.assembly_cost)}</div>
        <div>Опции: ${formatKzt(b.extras_cost)}</div>
      `;
      els.priceSummary.textContent = state.result.summary;
    } catch (error) {
      toast(error.message || "Сеть недоступна. Попробуйте ещё раз.", "error");
    }
  }

  function collectExtras() {
    state.extra_options = els.extras
      .filter((el) => el.checked)
      .map((el) => el.value);
  }

  els.typeCards.forEach((card) => {
    card.addEventListener("click", () => {
      state.furniture_type = card.dataset.furnitureType;
      els.typeCards.forEach((c) => c.classList.toggle("selected", c === card));
    });
  });

  ["width", "height", "depth"].forEach((key) => {
    els[key].addEventListener("input", () => {
      state.dimensions[key] = Number(els[key].value);
      syncDimsUi();
    });
  });

  els.material.addEventListener("change", () => {
    state.material_grade = els.material.value;
  });
  els.hardware.addEventListener("change", () => {
    state.hardware_brand = els.hardware.value;
  });
  els.extras.forEach((el) => {
    el.addEventListener("change", collectExtras);
  });

  els.btnPrev.addEventListener("click", () => {
    if (state.step > 1) {
      state.step -= 1;
      renderSteps();
    }
  });

  els.btnNext.addEventListener("click", async () => {
    if (state.step === 1 && !state.furniture_type) {
      toast("Выберите тип мебели", "error");
      return;
    }
    if (state.step < 4) {
      state.step += 1;
      renderSteps();
      if (state.step === 4) {
        collectExtras();
        await recalculate();
      }
    }
  });

  els.btnSubmit.addEventListener("click", async () => {
    const client_name = els.clientName.value.trim();
    const phone = els.clientPhone.value.trim();
    if (!client_name || client_name.length < 2) {
      toast("Укажите имя", "error");
      return;
    }
    if (!/^(\+77|87)\d{9}$/.test(phone.replace(/[\s-]/g, ""))) {
      toast("Телефон: +77XXXXXXXXX или 87XXXXXXXXX", "error");
      return;
    }
    if (!state.result) {
      await recalculate();
    }
    if (!state.result) return;

    els.btnSubmit.disabled = true;
    try {
      const response = await fetch(`${API_BASE}/leads/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_name,
          phone,
          furniture_type: state.furniture_type,
          estimated_price_min: state.result.price_min,
          estimated_price_max: state.result.price_max,
        }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        const detail = Array.isArray(err.detail)
          ? err.detail.map((d) => d.msg || d).join("; ")
          : err.detail || "Не удалось отправить заявку";
        throw new Error(detail);
      }
      toast("Заявка отправлена! Мы свяжемся с вами.", "success");
      els.clientName.value = "";
      els.clientPhone.value = "";
    } catch (error) {
      toast(error.message || "Ошибка сети", "error");
    } finally {
      els.btnSubmit.disabled = false;
    }
  });

  function clampDim(key, value) {
    const bounds = { width: [300, 6000], height: [300, 3500], depth: [200, 2500] };
    const [min, max] = bounds[key];
    return Math.max(min, Math.min(max, Number(value)));
  }

  window.mebelApplyVisionEstimate = async (estimate) => {
    if (estimate.furniture_type) {
      state.furniture_type = estimate.furniture_type;
      els.typeCards.forEach((c) => {
        c.classList.toggle("selected", c.dataset.furnitureType === estimate.furniture_type);
      });
    }
    if (estimate.width) state.dimensions.width = clampDim("width", estimate.width);
    if (estimate.height) state.dimensions.height = clampDim("height", estimate.height);
    if (estimate.depth) state.dimensions.depth = clampDim("depth", estimate.depth);
    if (estimate.material_grade) {
      state.material_grade = estimate.material_grade;
      els.material.value = estimate.material_grade;
    }
    syncDimsUi();
    state.step = 4;
    renderSteps();
    await recalculate();
    document.getElementById("calculator").scrollIntoView({ behavior: "smooth" });
  };

  syncDimsUi();
  renderSteps();
})();

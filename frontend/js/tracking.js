(() => {
  const API_BASE = window.MEBEL_API_BASE || "/api/v1";
  const form = document.getElementById("tracking-form");
  const input = document.getElementById("order-number");
  const result = document.getElementById("tracking-result");
  const meta = document.getElementById("tracking-meta");
  const stagesEl = document.getElementById("tracking-stages");
  const photoWrap = document.getElementById("tracking-photo");
  const photoImg = document.getElementById("tracking-photo-img");

  function toast(message, type = "info") {
    const stack = document.getElementById("toast-stack");
    if (!stack) return;
    const node = document.createElement("div");
    node.className = `toast ${type}`;
    node.textContent = message;
    stack.appendChild(node);
    setTimeout(() => node.remove(), 4200);
  }

  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const orderNumber = input.value.trim();
    if (!orderNumber) {
      toast("Введите номер заказа", "error");
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE}/tracking/${encodeURIComponent(orderNumber)}`
      );
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Заказ не найден");
      }
      const data = await response.json();
      result.classList.remove("hidden");
      meta.textContent = `Заказ ${data.order_number} · ${data.client_name}`;
      stagesEl.innerHTML = data.stages
        .map((stage) => {
          const cls = stage.completed
            ? "completed"
            : stage.current
              ? "current"
              : "";
          return `<div class="progress-step ${cls}">${stage.label}</div>`;
        })
        .join("");

      if (data.stage_photo_url) {
        photoWrap.classList.remove("hidden");
        photoImg.src = data.stage_photo_url;
        photoImg.alt = `Фото этапа: ${data.current_stage}`;
      } else {
        photoWrap.classList.add("hidden");
        photoImg.removeAttribute("src");
      }
    } catch (error) {
      result.classList.add("hidden");
      toast(error.message || "Ошибка сети", "error");
    }
  });

  const params = new URLSearchParams(window.location.search);
  const preset = params.get("order");
  if (preset) {
    input.value = preset;
    form.requestSubmit();
  }
})();

(() => {
  const API_BASE = window.MEBEL_API_BASE || "/api/v1";
  const zone = document.getElementById("upload-zone");
  const input = document.getElementById("sketch-input");
  const button = document.getElementById("btn-vision");
  const fileLabel = document.getElementById("upload-filename");

  if (!zone || !input || !button) return;

  let selectedFile = null;

  function toast(message, type = "info") {
    if (window.mebelToast) window.mebelToast(message, type);
  }

  function setFile(file) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      toast("Нужен файл изображения", "error");
      return;
    }
    selectedFile = file;
    fileLabel.textContent = file.name;
  }

  zone.addEventListener("dragover", (event) => {
    event.preventDefault();
    zone.classList.add("dragover");
  });

  zone.addEventListener("dragleave", () => {
    zone.classList.remove("dragover");
  });

  zone.addEventListener("drop", (event) => {
    event.preventDefault();
    zone.classList.remove("dragover");
    const file = event.dataTransfer.files?.[0];
    setFile(file);
  });

  zone.addEventListener("click", (event) => {
    if (event.target === button) return;
    input.click();
  });

  input.addEventListener("change", () => {
    setFile(input.files?.[0] || null);
  });

  button.addEventListener("click", async (event) => {
    event.stopPropagation();
    if (!selectedFile) {
      toast("Сначала загрузите эскиз или фото", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    button.disabled = true;
    button.textContent = "Распознаём…";
    try {
      const response = await fetch(`${API_BASE}/vision/estimate-sketch`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Не удалось распознать эскиз");
      }
      const estimate = await response.json();
      toast(
        estimate.source === "openai"
          ? "Эскиз распознан — калькулятор заполнен"
          : "Типовые размеры подставлены (проверьте вручную)",
        "success"
      );
      if (typeof window.mebelApplyVisionEstimate === "function") {
        await window.mebelApplyVisionEstimate(estimate);
      }
    } catch (error) {
      toast(error.message || "Ошибка сети", "error");
    } finally {
      button.disabled = false;
      button.textContent = "Распознать и посчитать";
    }
  });
})();

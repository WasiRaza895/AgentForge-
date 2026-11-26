"use strict";

(() => {
  const form = byId("model-form");
  const input = byId("model-key");
  const button = byId("model-save");
  const status = byId("model-status");
  const indicator = byId("model-indicator");

  function update(configured) {
    indicator.textContent = configured ? "Gemini key saved" : "Key needed for AI tasks";
    indicator.classList.toggle("run-completed", configured);
    byId("task-mode").textContent = configured ? "Google Gemini" : "Direct mode";
    if (configured) input.placeholder = "Paste a new Gemini key to replace it";
  }

  fetch("/api/model").then(async (response) => {
    if (!response.ok) throw new Error();
    update((await response.json()).configured === true);
  }).catch(() => {
    indicator.textContent = "Could not check vault";
    byId("task-mode").textContent = "Model status unavailable";
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (button.disabled) return;
    button.disabled = true;
    input.readOnly = true;
    status.className = "task-status";
    status.textContent = "Checking the key with Google Gemini…";
    try {
      const response = await fetch("/api/model", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential: input.value }),
      });
      const result = await response.json();
      if (!response.ok || !result.success) throw new Error(result.error || "Could not connect to Gemini.");
      input.value = "";
      update(true);
      status.classList.add("success");
      status.textContent = "Gemini accepted the key. You can run a task now.";
      const link = make("a", "", "Go to tasks");
      link.href = "#tasks";
      status.append(link);
    } catch (error) {
      status.classList.add("error");
      status.textContent = error.message;
    } finally {
      button.disabled = false;
      input.readOnly = false;
    }
  });
})();

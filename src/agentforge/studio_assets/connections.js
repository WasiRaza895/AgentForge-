"use strict";

(() => {
  const providers = {
    github: {
      name: "GitHub", credential: "GitHub access token", action: "Create a GitHub issue",
      hint: "Use a token with Issues write permission for the repository.",
      guide: "https://docs.github.com/en/rest/issues/issues#create-an-issue",
    },
    slack: {
      name: "Slack", credential: "Slack incoming webhook URL", action: "Send a Slack message",
      hint: "Use the incoming webhook URL for the channel where messages should go.",
      guide: "https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/",
    },
    exa: {
      name: "Exa", credential: "Exa API key",
      hint: "Optional. Studio uses this key for Exa web search when it is available.",
      guide: "https://docs.exa.ai/reference/search",
    },
  };

  const providerSelect = byId("connection-provider");
  const secretInput = byId("connection-secret");
  const connectionSave = byId("connection-save");
  const connectionMessage = byId("connection-status");
  const actionDialog = byId("action-dialog");
  const actionForm = byId("action-form");
  const actionStatus = byId("action-status");
  const actionSubmit = byId("action-submit");
  const actionClose = byId("close-action");
  let connections = null;
  let actionProvider = "";
  let actionDraft = null;
  let waitingAction = null;

  function notice(element, text, state = "") {
    element.textContent = text;
    element.className = `task-status ${state}`.trim();
  }

  function renderConnection() {
    const id = providerSelect.value;
    const provider = providers[id];
    byId("credential-label").textContent = provider.credential;
    byId("credential-help").textContent = provider.hint;
    byId("credential-guide").href = provider.guide;
    const indicator = byId("connection-indicator");
    indicator.textContent = connections === null ? "Vault status unavailable" : connections[id] ? "Stored locally" : "Needs setup";
    indicator.classList.toggle("run-completed", Boolean(connections?.[id]));
    secretInput.placeholder = connections?.[id] ? "Enter a new credential to replace it" : "Paste credential";
  }

  async function refreshConnections() {
    try {
      const response = await fetch("/api/connections");
      if (!response.ok) throw new Error();
      connections = (await response.json()).connections;
    } catch {
      connections = null;
    }
    renderConnection();
  }

  async function post(path, payload) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return response.json();
  }

  function switchProvider(id) {
    providerSelect.value = id;
    secretInput.value = "";
    notice(connectionMessage, "");
    renderConnection();
  }

  providerSelect.addEventListener("change", () => switchProvider(providerSelect.value));
  byId("connection-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (connectionSave.disabled) return;
    const id = providerSelect.value;
    connectionSave.disabled = true;
    providerSelect.disabled = true;
    secretInput.readOnly = true;
    notice(connectionMessage, "Saving to the local vault…");
    try {
      const result = await post("/api/connections", { provider: id, credential: secretInput.value });
      if (!result.success) throw new Error(result.error || "Could not save the credential.");
      secretInput.value = "";
      connections = result.connections;
      renderConnection();
      notice(connectionMessage, `${providers[id].name} credential saved locally.`, "success");
      if (waitingAction?.id === id) {
        const { draft } = waitingAction;
        waitingAction = null;
        showAction(id, draft);
      }
    } catch (error) {
      notice(connectionMessage, error.message, "error");
    } finally {
      connectionSave.disabled = false;
      providerSelect.disabled = false;
      secretInput.readOnly = false;
    }
  });

  function showMissingConnection(id) {
    byId("action-setup-message").textContent = `Add a ${providers[id].credential} in Service Connections to continue.`;
    byId("action-setup").hidden = false;
    actionForm.hidden = true;
  }

  function showAction(id, draft = null) {
    const github = id === "github";
    actionProvider = id;
    actionDraft = draft;
    actionForm.reset();
    if (draft) {
      byId("action-repo").value = draft.repo;
      byId("action-issue-title").value = draft.title;
      byId("action-content").value = draft.content;
    }
    byId("action-title").textContent = providers[id].action;
    byId("repo-field").hidden = !github;
    byId("title-field").hidden = !github;
    byId("action-repo").required = github;
    byId("action-issue-title").required = github;
    byId("action-content").required = !github;
    byId("action-content-label").textContent = github ? "Issue description (optional)" : "Message";
    byId("action-destination").textContent = github
      ? "This creates a real issue in the GitHub repository you enter."
      : "This posts to the Slack channel associated with your saved webhook.";
    actionSubmit.textContent = github ? "Create issue" : "Send message";
    notice(actionStatus, "");
    byId("action-setup").hidden = true;
    actionForm.hidden = false;
    if (!connections?.[id]) showMissingConnection(id);
    if (!actionDialog.open) actionDialog.showModal();
  }

  document.addEventListener("agentforge:review-draft", async (event) => {
    await refreshConnections();
    const draft = event.detail;
    showAction(draft.provider, draft);
  });

  for (const button of document.querySelectorAll("[data-action-provider]")) {
    button.addEventListener("click", async () => {
      await refreshConnections();
      showAction(button.dataset.actionProvider);
    });
  }

  byId("configure-action").addEventListener("click", () => {
    waitingAction = { id: actionProvider, draft: actionDraft };
    actionDialog.close();
    switchProvider(actionProvider);
    location.hash = "connections";
    secretInput.focus({ preventScroll: true });
  });

  actionDialog.addEventListener("cancel", (event) => {
    if (actionClose.disabled) event.preventDefault();
  });

  actionForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (actionSubmit.disabled) return;
    actionSubmit.disabled = true;
    actionClose.disabled = true;
    const payload = Object.fromEntries(new FormData(actionForm));
    payload.provider = actionProvider;
    payload.confirmed = byId("action-confirm").checked;
    notice(actionStatus, "Waiting for the service to confirm…");
    try {
      const result = await post("/api/actions", payload);
      if (result.connection) {
        actionDraft = payload;
        showMissingConnection(result.connection);
        notice(actionStatus, "");
        return;
      }
      if (!result.success) throw new Error(result.error || "The service did not confirm the action.");
      actionForm.reset();
      actionForm.hidden = true;
      notice(actionStatus, result.message, "success");
      if (result.url) actionStatus.append(resultLink(result.url, "View issue"));
    } catch (error) {
      notice(actionStatus, error.message, "error");
    } finally {
      byId("action-confirm").checked = false;
      actionSubmit.disabled = false;
      actionClose.disabled = false;
    }
  });

  refreshConnections();
})();

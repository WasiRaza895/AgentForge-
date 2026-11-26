"use strict";

const sourcePath = "src/agentforge/studio_assets/feed.xml";
const feedStep = { name: "Read the release feed", target: sourcePath, key: "feed", limit: 3 };
const workflows = {
  briefing: {
    name: "Release briefing",
    steps: [feedStep, { name: "Follow the related feed", target: "{feed.metadata.link}", key: "related", limit: 2 }],
  },
  scan: { name: "Release feed scan", steps: [feedStep] },
};

const byId = (id) => document.getElementById(id);
const choiceButtons = Array.from(document.querySelectorAll("[data-workflow]"));
const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
const runButtons = [byId("hero-run"), byId("inspector-run")];
const latestRuns = new Map();
const runs = [];
const scrollBehavior = matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
let selected = "briefing";
let running = false;
let shownRun = null;

function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function workflowYaml(workflow) {
  const steps = workflow.steps.map(({ name, target, limit, key }) => [
    `  - name: ${name}`,
    "    platform: rss",
    "    action: read",
    "    params:",
    `      target: ${target.startsWith("{") ? JSON.stringify(target) : target}`,
    `      limit: ${limit}`,
    `    output_var: ${key}`,
  ].join("\n"));
  return [`name: ${workflow.name}`, "steps:", ...steps].join("\n") + "\n";
}

function showTab(id, focus = false) {
  for (const tab of tabs) {
    const active = tab.id === `${id}-tab`;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
    byId(tab.getAttribute("aria-controls")).hidden = !active;
    if (active && focus) tab.focus();
  }
}

function setStatus(text, state = "") {
  const status = byId("run-status");
  status.textContent = text;
  status.className = `inspector-status ${state}`.trim();
}

function showRun(run) {
  shownRun = run;
  const output = byId("run-results");
  output.replaceChildren();
  byId("copy-output").hidden = !run;
  if (!run) {
    output.append(make("p", "", "Run the workflow to view the results."));
    setStatus("Ready to run");
    return;
  }
  if (!run.result.success) {
    const failedStep = run.result.log?.find((step) => !step.success);
    output.append(make("p", "", run.result.error || failedStep?.error || failedStep?.result?.error || "A workflow step failed."));
    setStatus("Workflow failed", "error");
    return;
  }

  let total = 0;
  const list = make("ul", "result-list");
  for (const step of run.result.log) {
    const entries = step.result.entries;
    for (const entry of entries) {
      const item = make("li");
      item.append(make("strong", "", entry.title), make("small", "", step.result.metadata.title));
      list.append(item);
    }
    total += entries.length;
  }
  output.append(list);
  setStatus(`Completed · ${total} feed ${total === 1 ? "entry" : "entries"}`, "success");
}

function selectWorkflow(id, tab = "steps", run = latestRuns.get(id)) {
  selected = id;
  const workflow = workflows[id];
  byId("inspector-title").textContent = workflow.name;
  for (const button of choiceButtons) {
    const active = button.dataset.workflow === id;
    button.classList.toggle("selected", active);
    button.setAttribute("aria-pressed", String(active));
  }
  const steps = workflow.steps.map((step) => {
    const item = make("li");
    const icon = make("span", "step-icon");
    icon.setAttribute("aria-hidden", "true");
    icon.append(make("span", "icon icon-feed"));
    const details = make("div", "step-details");
    details.append(make("strong", "", step.name), make("code", "", step.target));
    item.append(icon, details, make("span", "workflow-tag", "RSS · Read"));
    return item;
  });
  byId("step-list").replaceChildren(...steps);
  byId("yaml-code").textContent = workflowYaml(workflow);
  showRun(run);
  showTab(tab);
}

function renderHistory() {
  byId("history-empty").hidden = runs.length > 0;
  const items = runs.map((run) => {
    const row = make("button", "history-row");
    row.type = "button";
    const stamp = make("time", "", run.date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    stamp.dateTime = run.date.toISOString();
    const badge = run.result.success ? make("span", "badge run-completed", "Completed") : make("span", "badge run-failed", "Failed");
    row.append(make("strong", "", workflows[run.workflow].name), badge, stamp);
    row.addEventListener("click", () => {
      if (running) return;
      selectWorkflow(run.workflow, "output", run);
      byId("output-tab").focus({ preventScroll: true });
      byId("workflows").scrollIntoView({ behavior: scrollBehavior });
    });
    const item = make("li");
    item.append(row);
    return item;
  });
  byId("history-list").replaceChildren(...items);
}

async function runWorkflow(id) {
  if (running) return;
  selectWorkflow(id, "output");
  running = true;
  for (const button of [...choiceButtons, ...runButtons]) button.disabled = true;
  setStatus("Running workflow…");
  let result;
  try {
    const response = await fetch(`/api/demo/${id}`);
    if (!response.ok) throw new Error("The local workflow engine did not respond.");
    result = await response.json();
  } catch (error) {
    result = { success: false, error: error.message };
  } finally {
    running = false;
    for (const button of [...choiceButtons, ...runButtons]) button.disabled = false;
  }
  const run = { workflow: id, date: new Date(), result };
  runs.unshift(run);
  latestRuns.set(id, run);
  showRun(run);
  showTab("output");
  renderHistory();
}

async function copy(text, button) {
  const label = button.textContent;
  try {
    await navigator.clipboard.writeText(text);
    button.textContent = "Copied";
  } catch {
    button.textContent = "Copy unavailable";
  }
  setTimeout(() => { button.textContent = label; }, 1600);
}

for (const button of choiceButtons) button.addEventListener("click", () => selectWorkflow(button.dataset.workflow));
for (const tab of tabs) {
  tab.addEventListener("click", () => showTab(tab.id.replace("-tab", "")));
  tab.addEventListener("keydown", (event) => {
    const index = tabs.indexOf(tab);
    const targets = { ArrowLeft: (index + tabs.length - 1) % tabs.length, ArrowRight: (index + 1) % tabs.length, Home: 0, End: tabs.length - 1 };
    if (!(event.key in targets)) return;
    event.preventDefault();
    showTab(tabs[targets[event.key]].id.replace("-tab", ""), true);
  });
}

for (const button of document.querySelectorAll("[data-open]")) {
  button.addEventListener("click", () => byId(button.dataset.open).showModal());
}

function markLocation() {
  const hash = location.hash || "#overview";
  const links = Array.from(document.querySelectorAll(".rail-nav .nav-link"));
  const current = links.find((link) => link.getAttribute("href") === hash) || links[0];
  for (const link of links) {
    link.classList.toggle("active", link === current);
    if (link === current) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  }
  byId("location-label").textContent = current.textContent.trim();
}

window.addEventListener("hashchange", markLocation);
byId("hero-run").addEventListener("click", async () => {
  byId("workflows").scrollIntoView({ behavior: scrollBehavior });
  await runWorkflow("briefing");
  byId("output-tab").focus({ preventScroll: true });
});
byId("inspector-run").addEventListener("click", (event) => {
  const button = event.currentTarget;
  runWorkflow(selected).then(() => button.focus({ preventScroll: true }));
});
byId("copy-yaml").addEventListener("click", (event) => copy(byId("yaml-code").textContent, event.currentTarget));
byId("copy-output").addEventListener("click", (event) => copy(JSON.stringify(shownRun.result, null, 2), event.currentTarget));
selectWorkflow(selected);
markLocation();

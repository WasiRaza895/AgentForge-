# AgentForge Quickstart Guide

Get up and running with AgentForge in under 5 minutes.

---

## Step 1: Install & Diagnostics
Install the tool, download default CLI dependencies, and run health check:
```bash
pip install -e .
agentforge install
agentforge doctor
```

---

## Step 2: Read URL or Search the Web
Retrieve text from any website or query DuckDuckGo:
```bash
# Web search
agentforge search "SpaceX launch schedule"

# Read page details
agentforge web https://news.ycombinator.com
```

---

## Step 3: Configure Slack Alerts
Let's route research directly to Slack. Create an Incoming Webhook in Slack first, then configure it:
```bash
# Setup Slack notification channel
agentforge notify setup slack-channel --type slack --url "https://hooks.slack.com/services/..."

# Test alert delivery
agentforge notify send slack-channel "Hello Slack from AgentForge!"
```

---

## Step 4: Write Custom YAML Pipeline
Pipelines allow automated sequential tasks. Create a file named `hackernews.yaml`:

```yaml
name: "HN Search & Notify Pipeline"
steps:
  - name: "Web Search"
    platform: search
    action: search
    params:
      query: "LLM agents release"
      limit: 3
    output_var: search_results
    
  - name: "Post to Slack"
    platform: slack
    action: send
    params:
      message: "Here are the latest LLM agent search results:\n\n{search_results}"
```

Run the pipeline:
```bash
agentforge pipeline run hackernews.yaml
```

---

## Step 5: Start Background Watch Jobs
Let's watch for a keyword on Reddit and notify Slack when new matching items appear:
```bash
agentforge watch --platform reddit --query "Python" --interval 15m --notify slack-channel
```
*(Press Ctrl+C to terminate the scheduler)*
